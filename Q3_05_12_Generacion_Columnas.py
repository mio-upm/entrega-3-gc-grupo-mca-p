import pulp as lp
import pandas as pd
from datetime import datetime

# Charger les opérations depuis un fichier Excel
def load_operations_from_excel(file_path):
    df = pd.read_excel(file_path)
    df['Hora inicio '] = pd.to_datetime(df['Hora inicio '])
    df['Hora fin'] = pd.to_datetime(df['Hora fin'])
    operaciones = [(row["Código operación"], row["Hora inicio "], row["Hora fin"]) for _, row in df.iterrows()]
    return operaciones

# Fonction pour générer les incompatibilités
def generate_incompatibilidades(operaciones):
    incompatibilidades = {}
    for i, op1 in enumerate(operaciones):
        for j, op2 in enumerate(operaciones):
            if i < j:
                # Si les deux opérations se chevauchent, elles sont incompatibles
                if not (op1[2] <= op2[1] or op2[2] <= op1[1]):  # Si chevauchement
                    incompatibilidades[(op1[0], op2[0])] = True
                else:
                    incompatibilidades[(op1[0], op2[0])] = False
    return incompatibilidades

def subproblem(operations, incompatibilities, duals):
    model = lp.LpProblem("Subproblem", sense=lp.LpMaximize)

    # Variables binaires : inclure une opération dans une nouvelle colonne
    x = lp.LpVariable.dicts("x", [op[0] for op in operations], cat="Binary")

    # Objectif : Maximiser la somme des duales et la durée totale
    model += lp.lpSum(duals.get(f"Coverage_{idx}", 0) * x[op[0]] for idx, op in enumerate(operations)) + \
             lp.lpSum((op[2] - op[1]).total_seconds() / 3600 * x[op[0]] for op in operations)

    # Contraintes : éviter les chevauchements dans la colonne
    for i, op1 in enumerate(operations):
        for j, op2 in enumerate(operations):
            if i < j and incompatibilities.get((op1[0], op2[0]), False):
                model += x[op1[0]] + x[op2[0]] <= 1, f"Incompat_{op1[0]}_{op2[0]}"

    model.solve()

    # Vérifier si une solution optimale a été trouvée
    if model.status != 1:
        print("Aucune solution optimale trouvée pour le sous-problème.")
        return None, None

    # Générer une nouvelle colonne avec les opérations sélectionnées
    new_column = [op for op in operations if x[op[0]].varValue == 1]
    profit = lp.value(model.objective)
    return new_column, profit


def column_generation(operations, incompatibilities):
    # Initialiser les colonnes
    columns = [[op] for op in operations]

    while True:
        # Résoudre le problème maître détendu
        solution, objective, duals = maestro_relajado(columns, operations)

        if solution is None:
            print("Aucune solution trouvée dans le problème maître.")
            break

        # Résoudre le sous-problème pour générer une nouvelle colonne
        new_column, profit = subproblem(operations, incompatibilities, duals)

        # Vérification si le sous-problème retourne une colonne valide
        if new_column is None or profit is None or profit <= 0:
            print("Aucune nouvelle colonne valide à ajouter. Arrêt.")
            break

        # Ajouter la nouvelle colonne
        columns.append(new_column)

    return columns, objective


# Mise à jour du problème maître
def maestro_relajado(columns, operations):
    model = lp.LpProblem("Master", sense=lp.LpMinimize)

    # Variables binaires : chaque colonne est-elle utilisée ?
    y = lp.LpVariable.dicts("y", range(len(columns)), cat="Binary")

    # Objectif : Minimiser le nombre de colonnes utilisées
    model += lp.lpSum(y[k] for k in range(len(columns)))

    # Contraintes : chaque opération doit être couverte au moins une fois
    for idx, op in enumerate(operations):
        model += lp.lpSum(y[k] for k, col in enumerate(columns) if op in col) >= 1, f"Coverage_{idx}"

    model.solve()

    # Vérification si une solution optimale a été trouvée
    if model.status != 1:
        print("Aucune solution optimale trouvée pour le problème maître.")
        return None, None, None

    # Extraire les duales et les colonnes utilisées
    duals = {name: model.constraints[name].pi for name in model.constraints}
    solution = {k: y[k].varValue for k in range(len(columns))}
    objective = lp.value(model.objective)
    return solution, objective, duals


# Exporter les résultats
def export_results(columns, output_file):
    rows = []
    for block_id, column in enumerate(columns):
        for op in column:
            rows.append({
                "Bloc opératoire": block_id + 1,
                "Opération": op[0],
                "Heure début": op[1].strftime("%H:%M"),
                "Heure fin": op[2].strftime("%H:%M")
            })

    df = pd.DataFrame(rows)
    df.to_excel(output_file, index=False)
    print(f"Planifications exportées dans {output_file}")

# Exemple d'utilisation
if __name__ == "__main__":
    # Charger les données
    file_path = "241204_datos_operaciones_programadas.xlsx"
    operations = load_operations_from_excel(file_path)
    incompatibilities = generate_incompatibilidades(operations)

    # Lancer la génération de colonnes
    columns, objective = column_generation(operations, incompatibilities)

    # Exporter les résultats
    export_results(columns, "planifications_colgen.xlsx")
