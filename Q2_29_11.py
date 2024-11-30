# -*- coding: utf-8 -*-
"""
Created on Sat Nov 30 02:41:47 2024

@author: noele
"""

import pulp as lp
import pandas as pd
import numpy as np
from tqdm import tqdm

# PASO 2: CREAR PROBLEMA
problema = lp.LpProblem("Model1", sense = lp.LpMinimize)

# PASO 3: DECLARAR CONJUNTOS
datos = pd.read_excel("241204_datos_operaciones_programadas.xlsx", sheet_name='operaciones')
costes = pd.read_excel("241204_costes.xlsx", sheet_name = 'costes')

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
    

K = []
n = len(II)

def est_compatible(op1, op2):
    # Vérifie si deux opérations ne se chevauchent pas
    return op1[4] <= op2[3] or op1[3] >= op2[4]

# Générer toutes les combinaisons faisables de tailles différentes
for taille in tqdm(range(1, n + 1)):  # Taille des planifications (1, 2, ..., n)
    planifications = []
    indices = list(range(taille))  # Indices pour la première combinaison
    while True:
        # Construire la planification actuelle à partir des indices
        planification = [I[i] for i in indices]
        # Vérifier si toutes les opérations sont compatibles
        if all(est_compatible(op1, op2) for op1 in planification for op2 in planification if op1 != op2):
            K.append(planification)

        # Générer la prochaine combinaison
        for i in reversed(range(taille)):
            if indices[i] < n - (taille - i):
                indices[i] += 1
                for j in range(i + 1, taille):
                    indices[j] = indices[j - 1] + 1
                break
        else:  # Fin des combinaisons pour cette taille
            break


# PASO 4: DECLARAR PARÁMETROS
Cij = {}  # Diccionario de costes
for i in I:
    for j in J:
        indice_ligne = costes[costes.iloc[:, 0] == j].index[0]
        indice_colonne = costes.columns.get_loc(i[0])
        Cij[(i[0], j)] = costes.iloc[indice_ligne, indice_colonne]
        
Ci = {} #valeur moyenne opération i
for i in II :
    a = 0
    for j in J:
            a += Cij[(i,j)]
    Ci[i] = a/len(J)
    
Bik ={} #binaire si opération i dans la planification k
for k in range(len(K)):
    for j in II :
        for m in range(len(K[k])):
            if j == K[k][m][0]:
                Bik[(j,k)] = 1 #si opération i est dans planification k
            else :
              Bik[(j,k)] = 0 #sinon


Ck = {} #cout de la planification k
for i in range(len(K)):
    a = 0
    for j in range(len(K[i])):
            a += Ci[K[i][j][0]]
    Ck[i] = a

# PASO 5: DECLARAR LAS VARIABLES
y = lp.LpVariable.dicts(
    "y",
    range(len(K)),
    lowBound=0,
    upBound=None,cat = 'Binary'
)

# PASO 5: DECLARAR RESTRICCIONES
for i in II:
    problema += lp.lpSum(Bik[(i,k)]*y[k] for k in range(len(K))) >= 1

# PASO 6: DECLARAR FUNCIÓN OBJETIVO
problema += lp.lpSum(Ck[k] * y[k] for k in range(len(K)))

# PASO 7: RESOLVER PROBLEMA
problema.solve()

# Resultados
print("\nValor de las variables: ")
for v in problema.variables():
    print(v.name," = ", v.value())
print("\nEstado del problema: ", lp.LpStatus[problema.status])
print("\nValor de la función objetivo: ", lp.value(problema.objective))



