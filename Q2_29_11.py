# -*- coding: utf-8 -*-
"""
Created on Sat Nov 30 02:41:47 2024

@author: noele
"""

import pulp as lp
import pandas as pd
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt


especialidades = ['Cardiología Pediátrica','Cirugía Cardíaca Pediátrica','Cirugía Cardiovascular','Cirugía General y del Aparato Digestivo']
resultados =[]

def est_compatible(op1, op2):
    # Verifica si dos operaciones no se solapan
    return op1[4] <= op2[3] or op1[3] >= op2[4]

for x in especialidades:
    # PASO 2: CREAR PROBLEMA
    problema = lp.LpProblem("Model1", sense = lp.LpMinimize)

    # PASO 3: DECLARAR CONJUNTOS
    datos = pd.read_excel("241204_datos_operaciones_programadas.xlsx", sheet_name='operaciones')
    costes = pd.read_excel("241204_costes.xlsx", sheet_name = 'costes')

    datos_cardio = datos[datos['Especialidad quirúrgica'] == x]

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


    # generar todas las combinaciones
    for taille in range(1, n + 1):  # tamano de las planificaciones
        planifications = []
        indices = list(range(taille))  # Indices 
        while True:
            # Construir la planificación actual con los índices
            planification = [I[i] for i in indices]
            # Verificar si todas las operaciones son compatibles
            if all(est_compatible(op1, op2) for op1 in planification for op2 in planification if op1 != op2):
                K.append(planification)

            # Generar la proxima combinación
            for i in reversed(range(taille)):
                if indices[i] < n - (taille - i):
                    indices[i] += 1
                    for j in range(i + 1, taille):
                        indices[j] = indices[j - 1] + 1
                    break
            else:
                break


# PASO 4: DECLARAR PARÁMETROS
    Cij = {}  # Diccionario de costes
    for i in I:
        for j in J:
            indice_ligne = costes[costes.iloc[:, 0] == j].index[0]
            indice_colonne = costes.columns.get_loc(i[0])
            Cij[(i[0], j)] = costes.iloc[indice_ligne, indice_colonne]
        
    Ci = {} #valor media operación i
    for i in II :
        a = 0
        for j in J:
                a += Cij[(i,j)]
        Ci[i] = a/len(J)
    
    Bik ={} #binaria si operación i en planificación k
    for k in range(len(K)):
        for j in II :
            for m in range(len(K[k])):
                if j == K[k][m][0]:
                    Bik[(j,k)] = 1 #si operación i en planificación k
                else :
                  Bik[(j,k)] = 0 #sino


    Ck = {} #coste de la planificacóin k
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
    #print("\nValor de las variables: ")
    #for v in problema.variables():
    #   print(v.name," = ", v.value())
    print("\nEstado del problema para  ",x," : ", lp.LpStatus[problema.status])
    print("\nValor de la función objetivo para ",x," = ", lp.value(problema.objective))
    
    # Créer un DataFrame pour stocker les résultats
    result_data = []
    for k in range(len(K)):
        if y[k].value() == 1:  # Si la planification k est sélectionnée
            for op in K[k]:  # Pour chaque opération dans la planification k
                result_data.append({
                    'Operación': op[0],
                    'Inicio': op[3],
                    'Fin': op[4],
                    'Coste': Ck[k]
                })
    
    result_df = pd.DataFrame(result_data)
    
    print(result_df)


    
