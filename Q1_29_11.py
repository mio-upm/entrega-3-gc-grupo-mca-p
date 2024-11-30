# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 21:11:48 2024

@author: noele
"""

# PASO 1: IMPORTAR LIBRERÍA
import pulp as lp
import pandas as pd
import numpy as np
from tqdm import tqdm

# PASO 2: CREAR PROBLEMA
problema = lp.LpProblem("Model1", sense = lp.LpMinimize)

# PASO 3: DECLARAR CONJUNTOS
datos = pd.read_excel("241204_datos_operaciones_programadas.xlsx", sheet_name='operaciones')
costes = pd.read_excel("241204_costes.xlsx", sheet_name = 'costes')

# Filtrar solo las operaciones del servicio de Cardiología Pediátrica
datos_cardio = datos[datos['Especialidad quirúrgica'] == 'Cardiología Pediátrica']

numero_eq = len(datos_cardio)  # Número de equipos médicos en Cardiología Pediátrica
I = []  # código médico, equipos médicos, hora inicio, hora fin
II = []  # Solo códigos médicos 
for i in range(numero_eq):
    I.append([datos_cardio.iloc[i,0], datos_cardio.iloc[i,1], datos_cardio.iloc[i,2], datos_cardio.iloc[i,3], datos_cardio.iloc[i,4]])
    II.append(datos_cardio.iloc[i,0])

numero_quir = len(costes)  # Número de quirófanos
J = []
for i in range(numero_quir):
    J.append(costes.iloc[i, 0])

# PASO 4: DECLARAR PARÁMETROS
Cij = {}  # Diccionario de costes
for i in I:
    for j in J:
        indice_ligne = costes[costes.iloc[:, 0] == j].index[0]
        indice_colonne = costes.columns.get_loc(i[0])
        Cij[(i[0], j)] = costes.iloc[indice_ligne, indice_colonne]

Li = {}  # Diccionario de operaciones incompatibles
hora_inicio = []
hora_fin = []
for i in range(numero_eq):
    hora_inicio.append(pd.to_datetime(I[i][3]))  # Hora de inicio
    hora_fin.append(pd.to_datetime(I[i][4]))  # Hora de fin

for i in range(numero_eq):
    incompatibles = []
    for j in range(numero_eq):
        if i != j:
            if not (hora_fin[i] <= hora_inicio[j] or hora_inicio[i] >= hora_fin[j]):
                incompatibles.append(I[j][0])
    Li[II[i]] = incompatibles

# PASO 5: DECLARAR LAS VARIABLES
x = lp.LpVariable.dicts(
    "x",
    [(i,j) for i in II for j in J],
    lowBound=0,
    upBound=None,cat = 'Binary'
)

# PASO 5: DECLARAR RESTRICCIONES
# Asegurarse de que cada operación se asigna a al menos un quirófano
for i in II:
    problema += lp.lpSum(x[(i,j)] for j in J) >= 1

# Asegurar que las operaciones incompatibles no se asignen al mismo quirófano
for i in tqdm(II):
    for m in J:
        problema += lp.lpSum(x[(i, m)]) + lp.lpSum(x[(h, m)] for h in Li[i]) <= 1

# PASO 6: DECLARAR FUNCIÓN OBJETIVO
# Minimizar el coste total de la asignación
problema += lp.lpSum(Cij[(i, j)] * x[(i, j)] for i in II for j in J)

# PASO 7: RESOLVER PROBLEMA
print('En cours de resolución...')
problema.solve()

# Resultados
print("\nValor de las variables: ")
for v in problema.variables():
    print(v.name," = ", v.value())
print("\nEstado del problema: ", lp.LpStatus[problema.status])
print("\nValor de la función objetivo: ", lp.value(problema.objective))
