import pulp as lp
import pandas as pd

# Charger les données depuis Excel
def load_operations_from_excel(file_path):
    df = pd.read_excel(file_path)
    df['Hora inicio '] = pd.to_datetime(df['Hora inicio '])
    df['Hora fin'] = pd.to_datetime(df['Hora fin'])

    operaciones = []
    for index, row in df.iterrows():
        operaciones.append((row["Código operación"], row["Hora inicio "], row["Hora fin"]))
    
    return operaciones

# Générer les incompatibilités entre les opérations
def generate_incompatibilidades(operaciones):
    incompatibilidades = {}
    for i, op1 in enumerate(operaciones):
        for j, op2 in enumerate(operaciones):
            if i < j:
                if not (op1[2] <= op2[1] or op2[2] <= op1[1]):  
                    incompatibilidades[(op1[0], op2[0])] = True
                else:
                    incompatibilidades[(op1[0], op2[0])] = False
    return incompatibilidades

# Programme principal d'affectation des opérations aux blocs
def assign_operations_to_blocks(operaciones, incompatibilidades):
    num_operations = len(operaciones)
    max_blocks = num_operations  
    model = lp.LpProblem("Bloc_Operatoire_Optimise", sense=lp.LpMinimize)

    x = lp.LpVariable.dicts("Assign", (range(num_operations), range(max_blocks)), cat='Binary')

    model += lp.lpSum([x[i][b] for i in range(num_operations) for b in range(max_blocks)])

    for i in range(num_operations):
        model += lp.lpSum([x[i][b] for b in range(max_blocks)]) == 1, f"Operation_Assignment_{i}"

    for b in range(max_blocks):
        for i in range(num_operations):
            for j in range(i + 1, num_operations):
                # Si les opérations i et j se chevauchent
                if not (operaciones[i][2] <= operaciones[j][1] or operaciones[j][2] <= operaciones[i][1]):
                    model += x[i][b] + x[j][b] <= 1, f"Incompat_{i}_{j}_block_{b}"

    model.solve()
    assigned_blocks = {}
    used_blocks = set()  
    for b in range(max_blocks):
        assigned_blocks[b] = []
        for i in range(num_operations):
            if lp.value(x[i][b]) == 1:
                assigned_blocks[b].append(operaciones[i])
                used_blocks.add(b)

    return assigned_blocks, used_blocks

# Exporter les résultats dans un fichier Excel
def export_results(assigned_blocks, used_blocks, output_file):
    # Préparer les données pour l'exportation
    rows = []
    for b in used_blocks:
        for op in assigned_blocks[b]:
            rows.append({
                "Bloc opératoire": b + 1,
                "Opération": op[0],
                "Heure début": op[1].strftime('%H:%M'),
                "Heure fin": op[2].strftime('%H:%M')
            })

    df = pd.DataFrame(rows)
    df.to_excel(output_file, index=False)
    print(f"Planifications optimales exportées dans {output_file}")

# Exemple d'utilisation
if __name__ == "__main__":
    file_path = "241204_datos_operaciones_programadas.xlsx"  
    operaciones = load_operations_from_excel(file_path)

    incompatibilidades = generate_incompatibilidades(operaciones)
    assigned_blocks, used_blocks = assign_operations_to_blocks(operaciones, incompatibilidades)
    export_results(assigned_blocks, used_blocks, "planifications_optimales.xlsx")
    print(f"Numero de quirofanos utilizados : {len(used_blocks)}")
