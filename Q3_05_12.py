
import pulp as lp

def maestro_relajado(K, I):
    model = lp.LpProblem("Maestro Relajado", sense=lp.LpMinimize)
    y = lp.LpVariable.dicts("y", range(len(K)), cat='Binary')

    model += lp.lpSum(y[k] for k in range(len(K))) 

    Bik = {(i, k): 1 if i in [op[0] for op in K[k]] else 0 for k in range(len(K)) for i in I}

    for idx, i in enumerate(I):
        model += lp.lpSum(Bik[(i, k)] * y[k] for k in range(len(K))) >= 1, f"Couv_{idx}"

    model.solve()

    # Vérification de la solution
    if model.status != 1:

        return None, None, None  # Si le modèle n'a pas trouvé de solution valide

    solution = {k: y[k].varValue for k in range(len(K))}
    dual_values = {idx: model.constraints[f"Couv_{idx}"].pi for idx in range(len(I))}

    return solution, lp.value(model.objective), dual_values

def SP(operaciones, incompatibilidades, dualvalues, cost_per_op, current_columns):
    model = lp.LpProblem("SubProblema", sense=lp.LpMaximize)

    # Utiliser seulement les colonnes actuelles
    B = lp.LpVariable.dicts("B", [op[0] for op in operaciones], cat=lp.LpBinary)

    # Fonction objectif : Maximiser les profits réduits (dual values - cost)
    model += lp.lpSum((dualvalues[idx] - cost_per_op.get(op[0], 0)) * B[op[0]] for idx, op in enumerate(operaciones))

    # Contraintes d'incompatibilité
    for (op1, op2), incompatible in incompatibilidades.items():
        if incompatible:
            model += B[op1] + B[op2] <= 1

    # Résolution du modèle
    model.solve()
   
    n_column = [op[0] for op in operaciones if B[op[0]].varValue == 1]
    profit = lp.value(model.objective)

    # Filtrage des colonnes avec un profit trop faible
    threshold = 0.05 * profit  # seuil basé sur le profit généré
    n_column = [col for col in n_column if (dualvalues.get(col, 0) - cost_per_op.get(col, 0)) > threshold]

    # Réduire le nombre de colonnes dans current_columns si trop nombreuses
    if len(current_columns) + len(n_column) > 99:
        n_column = n_column[:99 - len(current_columns)]  # Limiter à 99 colonnes

    return n_column, profit


def main(init, operaciones, incompatibilidades, costs):
    current = init
    i = 1
    while True:
        # Résolution de Maestro Relajado avec les contraintes supplémentaires
        solution, obj, dualvalues = maestro_relajado(current, [op[0] for op in operaciones])

        # Résolution du sous-problème
        n_column, profit = SP(operaciones, incompatibilidades, dualvalues, costs,current)

        # Condition d'arrêt si le profit est faible ou nul
        if profit is None or profit <= 0:
            break

        # Ajouter la nouvelle colonne si elle apporte un profit suffisant
        seuil = 0.05 * obj  # 5% du profit initial comme seuil
        if profit > seuil:
            current.append(n_column)

        # Limiter la taille des colonnes à 99
        if len(current) > 99:
            current = current[:99]

        i += 1

    # Extraire la solution finale
    final = {k: solution[k] for k in range(len(current))}
    return final, obj


#DATOS EXERCICIO

import pandas as pd

costes_df = pd.read_excel("241204_costes.xlsx")  # Remplacez par le chemin du fichier
datos_operaciones_df = pd.read_excel("241204_datos_operaciones_programadas.xlsx")  # Remplacez par le chemin du fichier

#COSTES
medias = costes_df.mean(numeric_only=True)
costes_medios = medias.to_dict()
costes_medios = {str(k): v for k, v in costes_medios.items()}

#OPERACIONES
operaciones = []
for _, row in datos_operaciones_df.iterrows():
    id_operacion = row["Código operación"]
    hora_inicio = pd.to_datetime(row["Hora inicio "])  
    hora_fin = pd.to_datetime(row["Hora fin"])  
    operaciones.append((id_operacion, hora_inicio, hora_fin))

#INCOMPATIBILIDADES
incompatibilidades = {}
for i, (id_op_i, inicio_i, fin_i) in enumerate(operaciones):
    for j, (id_op_j, inicio_j, fin_j) in enumerate(operaciones):
        if i < j:  # Comparer chaque paire
            if not (fin_i <= inicio_j or fin_j <= inicio_i):  # Si elles se chevauchent
                incompatibilidades[(id_op_i, id_op_j)] = True
            else:
                incompatibilidades[(id_op_i, id_op_j)] = False


#COLUMNAS INICIALES
initial_columns = []
used = set()
for op1 in operaciones:
    if op1[0] not in used:
        group = [op1]
        used.add(op1[0])
        for op2 in operaciones:
            if op2[0] not in used and not incompatibilidades.get((op1[0], op2[0]), False):
                group.append(op2)
                used.add(op2[0])
        initial_columns.append([(op[0], op[1], op[2]) for op in group])


# Exécuter l'algorithme avec les données préparées
final_solution, final_objective = main(initial_columns, operaciones, incompatibilidades,costes_medios)

df = pd.DataFrame(list(final_solution.items()), columns=['Planification', 'Choix'])
df['Objectif'] = final_objective


#Pour Excel, tu peux utiliser :
df.to_excel('resultats.xlsx', index=False)

# Affichage des résultats
print("Solution finale :", final_solution)
print("Valeur objective finale :", final_objective)

# Affichage de la planification complète
for k, chosen in final_solution.items():
    if chosen == 1:  # Si la planification est choisie
        print(f"Planification {k}:")
        for op in initial_columns[k]:
            operation_id, start_time, end_time = op
            print(f"  Opération {operation_id}: de {start_time} à {end_time}")

