# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 17:55:09 2024

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

numero_eq = 175  #numero equipos medicales
I = [] #code medicos, equipos de medicos, heure début, heure fin
II = []  #solo codigo medicos
for i in range(numero_eq):
    I.append([datos.iloc[i,0],datos.iloc[i,1],datos.iloc[i,2],datos.iloc[i,3],datos.iloc[i,4]])
    II.append(datos.iloc[i,0])
    
numero_quir = 99 #numero quirofanos
J = []  #conjunto quirofanos
for i in range(numero_quir):
    J.append(costes.iloc[i,0])

# PASO 4: DECLARAR PARAMETROS
Cij = {}  #dictionnaire costes
for i in I:
    for j in J:
        indice_ligne = costes[costes.iloc[:, 0] == j].index[0]
        indice_colonne = costes.columns.get_loc(i[0])
        Cij[(i[0], j)] = costes.iloc[indice_ligne,indice_colonne]
        
Li = {}  # dictionnaire des opérations incompatibles avec l'opération i
hora_inicio = []
hora_fin = []
for i in range(numero_eq):
    hora_inicio.append(pd.to_datetime(I[i][3]))  # Heures de début
    hora_fin.append(pd.to_datetime(I[i][4]))  # Heures de fin

# Parcourir chaque opération
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
    upBound=None,
    cat=lp.LpBinary
    )

# PASO 5: DECLARAR RESTRICCIONES

for i in II:
    problema += lp.lpSum(x[(i,j)] for j in J) >= 1
    
for i in tqdm(II):
    for m in J:
        problema += lp.lpSum(x[(i, m)] + x[(h, m)] for h in Li[i]) <= 1

# PASO 6: DECLARAR FUNCIÓN OBJETIVO
problema += lp.lpSum(Cij[(i, j)] * x[(i, j)] for i in II for j in J)

# PASO 7: RESOLVEMOS PROBLEMA
print('En cours de résolution...')
problema.solve()


print("\nValor de las variables: ")
for v in problema.variables():
    print(v.name," = ", v.value())
print("\nEstado del problema: ", lp.LpStatus[problema.status])
print("\nValor de la función objetivo: ", lp.value(problema.objective))
