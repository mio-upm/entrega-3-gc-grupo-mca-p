import pulp as lp

# Données simplifiées pour tester
operations = [
    ('20241204 OP-1', '08:00', '09:00'),
    ('20241204 OP-2', '09:00', '10:00'),
    ('20241204 OP-3', '10:00', '11:00')
]

# Colonnes initiales (planifications de blocs opératoires)
initial_columns = [
    [('20241204 OP-1', '08:00', '09:00')],
    [('20241204 OP-2', '09:00', '10:00')],
    [('20241204 OP-3', '10:00', '11:00')]
]

# Incompatibilités (opérations qui se chevauchent)
incompatibilities = {
    ('20241204 OP-1', '20241204 OP-2'): True,
    ('20241204 OP-2', '20241204 OP-3'): False,
    ('20241204 OP-1', '20241204 OP-3'): False
}

# Modèle principal (Maestro Relajado)
def maestro_relajado(K, I):
    model = lp.LpProblem("Maestro Relajado", sense=lp.LpMinimize)
    
    # Variables binaires : y[k] indique si la planification k est utilisée
    y = lp.LpVariable.dicts("y", range(len(K)), cat='Binary')
    
    # Fonction objectif : Minimiser le nombre de planifications utilisées
    model += lp.lpSum(y[k] for k in range(len(K)))
    
    # Calcul de Bik : indique si l'opération i est dans la planification k
    Bik = {(i, k): 1 if i in [op[0] for op in K[k]] else 0 for k in range(len(K)) for i in I}
    
    # Contraintes : chaque opération doit être couverte par au moins une planification
    for idx, i in enumerate(I):  
        model += lp.lpSum(Bik[(i, k)] * y[k] for k in range(len(K))) >= 1, f"Couv_{idx}"
    
    # Résolution du modèle
    model.solve()
    solution = {k: y[k].varValue for k in range(len(K))}
    
    # Extraction des valeurs duales
    dual_values = {idx: model.constraints[f"Couv_{idx}"].pi for idx in range(len(I))}
    
    return solution, lp.value(model.objective), dual_values

# Problème de sous-optimisation (SP)
def SP(operaciones, incompatibilidades, dualvalues):
    model = lp.LpProblem("SubProblema", sense=lp.LpMaximize)
    
    B = lp.LpVariable.dicts("B", [op[0] for op in operaciones], cat=lp.LpBinary)
    
    model += lp.lpSum(dualvalues[idx] * B[op[0]] for idx, op in enumerate(operaciones))
    
    for (op1, op2), incompatible in incompatibilidades.items():
        if incompatible:
            model += B[op1] + B[op2] <= 1
    
    model.solve()
    n_column = [op[0] for op in operaciones if B[op[0]].varValue == 1]
    profit = lp.value(model.objective)
    
    return n_column, profit

# Exécution de l'algorithme principal
def main(init, operaciones, incompatibilidades):
    current = init
    while True:
        # Résolution MR
        solution, obj, dualvalues = maestro_relajado(current, [op[0] for op in operaciones])
        
        # Résolution SP
        n_column, profit = SP(operaciones, incompatibilidades, dualvalues)
        
        if profit is None or profit<= 0:
            break
        current.append(n_column)
    
    final = {k: solution[k] for k in range(len(current))}
    return final, obj

# Exécuter avec les données simplifiées
final_solution, final_objective = main(initial_columns, operations, incompatibilities)

# Afficher les résultats
print("Solution finale :", final_solution)
print("Valeur objective finale :", final_objective)
