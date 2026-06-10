#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projet d'Aide Multicritère à la Décision (MCDA) - Rock en Seine 2026
Membres du groupe : Jules BOBO, Florent JIN, Victor CAI
Enseignante : Lucie GALAND
Université Paris-Dauphine - PSL

Ce script implémente les modèles mathématiques d'aide à la décision collective
pour le choix des formules de billets au festival Rock en Seine. Il contient :
1. La modélisation des alternatives (les formules de billets) et critères (coût, goûts artistiques, disponibilités).
2. La mise à l'échelle (normalisation) des performances initiales sur une échelle commune de 0 à 10.
3. La résolution par la méthode d'agrégation de la Somme Pondérée (méthode compensatoire).
4. La résolution par la méthode de surclassement ELECTRE I (méthode non-compensatoire avec seuils de veto).
5. La génération automatique des tableaux formatés pour l'intégration directe dans le rapport LaTeX.
"""

# ==============================================================================
# 1. PARAMÈTRES ET DONNÉES INITIALES
# ==============================================================================

# Dénomination des 6 alternatives retenues (actions possibles)
ALTERNATIVES = [
    "a1 (Mercredi)",
    "a2 (Jeudi)",
    "a3 (Vendredi)",
    "a4 (Samedi)",
    "a5 (Dimanche)",
    "a6 (Pass 2 Jours)"
]

# Libellés des 7 critères d'évaluation
CRITERIA = [
    "g1 (Coût)",
    "g2 (Satisf. Jules)",
    "g3 (Satisf. Florent)",
    "g4 (Satisf. Victor)",
    "g5 (Disp. Jules)",
    "g6 (Disp. Florent)",
    "g7 (Disp. Victor)"
]

# Matrice de performance initiale (6 alternatives x 7 critères)
# Échelles d'origine :
# - g1 (Coût) : en euros [89, 149] (à minimiser)
# - g2, g3, g4 (Artistique) : notes sur 10 (à maximiser)
# - g5, g6, g7 (Disponibilité) : notes sur 5 (à maximiser)
PERF_MATRIX = [
    [99.0,  4.0, 9.0, 5.0, 5.0, 5.0, 5.0],  # a1 (Me)
    [89.0,  3.0, 4.0, 9.0, 5.0, 5.0, 5.0],  # a2 (Je)
    [94.0,  8.0, 5.0, 4.0, 5.0, 1.0, 5.0],  # a3 (Ve)
    [94.0,  5.0, 6.0, 6.0, 5.0, 5.0, 5.0],  # a4 (Sa)
    [99.0,  9.0, 3.0, 7.0, 5.0, 5.0, 1.0],  # a5 (Di)
    [149.0, 6.5, 5.5, 5.0, 5.0, 2.0, 5.0]   # a6 (2 Jours)
]

# Vecteur des poids des critères (la somme doit valoir 1.0)
WEIGHTS = [
    0.25,  # w1 (Coût)
    0.15,  # w2 (Artistique Jules)
    0.15,  # w3 (Artistique Florent)
    0.15,  # w4 (Artistique Victor)
    0.10,  # w5 (Dispo Jules)
    0.10,  # w6 (Dispo Florent)
    0.10   # w7 (Dispo Victor)
]

# Seuils de veto pour ELECTRE I définis sur l'échelle d'utilité normalisée [0, 10]
# Si la différence d'utilité u_k(aj) - u_k(ai) > veto_k, alors ai ne peut surclasser aj
VETOES = [
    9.0,  # Coût : un écart trop grand (ex: 89€ vs 149€) bloque la décision
    6.0,  # Goûts : veto si l'un perd plus de 6/10 d'utilité artistique
    6.0,
    6.0,
    5.0,  # Disponibilité : un score normalisé de 2/10 (dispo 1/5) déclenche un veto (10 - 2 = 8 > 5)
    5.0,
    5.0
]


# ==============================================================================
# 2. LOGIQUE DE CALCULS ET ALGORITHMES
# ==============================================================================

def normalize_matrix(matrix):
    """
    Normalise la matrice de performance sur une échelle commune d'utilité [0, 10].
    
    Règles de normalisation :
    - Coût g1 (à minimiser) : u_1(a) = 10 * (149 - g_1(a)) / (149 - 89)
    - Artistique g2, g3, g4 (sur 10) : u_j(a) = g_j(a)
    - Disponibilité g5, g6, g7 (sur 5) : u_j(a) = 2 * g_j(a)
    """
    norm_matrix = []
    min_cost, max_cost = 89.0, 149.0
    
    for row in matrix:
        norm_row = [0.0] * 7
        # Normalisation du coût (interpolation linéaire inverse)
        norm_row[0] = 10.0 * (max_cost - row[0]) / (max_cost - min_cost)
        
        # Les critères artistiques sont déjà sur 10
        norm_row[1] = row[1]
        norm_row[2] = row[2]
        norm_row[3] = row[3]
        
        # Les critères de disponibilité (sur 5) sont multipliés par 2
        norm_row[4] = 2.0 * row[4]
        norm_row[5] = 2.0 * row[5]
        norm_row[6] = 2.0 * row[6]
        
        norm_matrix.append(norm_row)
        
    return norm_matrix


def solve_weighted_sum(norm_matrix, weights):
    """
    Calcule les scores globaux selon la méthode de la Somme Pondérée.
    Renvoie une liste de couples (indice_alternative, score) classée par ordre décroissant.
    """
    scores = []
    for i, row in enumerate(norm_matrix):
        score = sum(val * w for val, w in zip(row, weights))
        scores.append((i, score))
    
    # Tri par score décroissant pour obtenir le classement
    ranking = sorted(scores, key=lambda x: x[1], reverse=True)
    return ranking


def solve_electre_i(norm_matrix, weights, vetoes):
    """
    Implémente la méthode de surclassement ELECTRE I.
    Calcule et renvoie la matrice de concordance et la matrice de discordance (vetos).
    """
    n = len(norm_matrix)
    concordance = [[0.0] * n for _ in range(n)]
    discordance = [[0] * n for _ in range(n)]  # 1 si veto activé, 0 sinon
    
    for i in range(n):
        for j in range(n):
            if i == j:
                concordance[i][j] = 1.0
                discordance[i][j] = 0
                continue
            
            # 1. Calcul de l'indice de concordance C(ai, aj)
            # Somme des poids des critères où ai est au moins aussi bon que aj
            c_score = 0.0
            veto_triggered = 0
            
            for k in range(len(weights)):
                u_ik = norm_matrix[i][k]
                u_jk = norm_matrix[j][k]
                
                if u_ik >= u_jk:
                    c_score += weights[k]
                else:
                    # 2. Vérification des conditions de veto (discordance)
                    # Veto activé si l'écart dépasse le seuil : u_jk - u_ik > veto_k
                    if (u_jk - u_ik) > vetoes[k]:
                        veto_triggered = 1
                        
            concordance[i][j] = c_score
            discordance[i][j] = veto_triggered
            
    return concordance, discordance


# ==============================================================================
# 3. INTERFACES DE SORTIE (CONSOLE ET LATEX)
# ==============================================================================

def display_console_results(norm_matrix, ws_ranking, concordance, discordance):
    """
    Affiche une synthèse complète et lisible des calculs dans la console.
    """
    print("=" * 80)
    print(" RÉSULTATS D'AIDE À LA DÉCISION MULTICRITÈRE - ROCK EN SEINE 2026")
    print("=" * 80)
    
    # 1. Matrice des utilités normalisées
    print("\n1. MATRICE DES UTILITÉS NORMALISÉES (Échelle commune [0, 10]) :")
    print("-" * 80)
    header = f"{'Alternative':<20} | " + " | ".join(f"u{k+1}" for k in range(7))
    print(header)
    print("-" * 80)
    for i, row in enumerate(norm_matrix):
        row_str = " | ".join(f"{val:>4.2f}" for val in row)
        print(f"{ALTERNATIVES[i]:<20} | {row_str}")
    print("-" * 80)
    
    # 2. Résultats de la Somme Pondérée
    print("\n2. RÉSULTATS ET CLASSEMENT (SOMME PONDÉRÉE) :")
    print("-" * 50)
    print(f"{'Rang':<6} | {'Alternative':<20} | {'Score Global':<12}")
    print("-" * 50)
    for rank, (idx, score) in enumerate(ws_ranking):
        print(f"{rank + 1:<6} | {ALTERNATIVES[idx]:<20} | {score:>12.3f}")
    print("-" * 50)
    
    # 3. Matrice de Concordance ELECTRE I
    print("\n3. MATRICE DE CONCORDANCE ELECTRE I C(ai, aj) :")
    print("-" * 60)
    print(" " * 18 + " ".join(f"  a{j+1}  " for j in range(6)))
    print("-" * 60)
    for i, row in enumerate(concordance):
        row_str = " ".join(f"{val:>6.2f}" for val in row)
        print(f"a{i+1} ({ALTERNATIVES[i][:3]}) | {row_str}")
    print("-" * 60)
    
    # 4. Matrice de Discordance ELECTRE I (Vetos)
    print("\n4. MATRICE DE DISCORDANCE ELECTRE I (1 = VETO ACTIVÉ, 0 = PAS DE VETO) :")
    print("-" * 60)
    print(" " * 18 + " ".join(f"  a{j+1}  " for j in range(6)))
    print("-" * 60)
    for i, row in enumerate(discordance):
        row_str = " ".join(f"{val:>6d}" for val in row)
        print(f"a{i+1} ({ALTERNATIVES[i][:3]}) | {row_str}")
    print("-" * 60)
    
    # 5. Synthèse des relations de surclassement
    print("\n5. RELATIONS DE SURCLASSEMENT ELECTRE I (Seuil de concordance gamma = 0.60) :")
    print("-" * 80)
    gamma = 0.60
    has_outranking = False
    for i in range(len(ALTERNATIVES)):
        targets = []
        for j in range(len(ALTERNATIVES)):
            if i != j and concordance[i][j] >= gamma and discordance[i][j] == 0:
                targets.append(f"a{j+1}")
        if targets:
            has_outranking = True
            targets_str = ", ".join(targets)
            print(f"L'alternative a{i+1} ({ALTERNATIVES[i]}) surclasse : {targets_str}")
    if not has_outranking:
        print("Aucune relation de surclassement n'est établie pour ce seuil.")
    print("-" * 80)


def generate_latex_tables(norm_matrix, ws_ranking, concordance, discordance):
    """
    Génère les codes LaTeX prêts pour intégration directe dans le rapport.
    """
    print("\n" + "%" * 50)
    print("% CODE LATEX POUR LES TABLEAUX DU RAPPORT")
    print("%" * 50 + "\n")
    
    # A. Tableau des performances initiales
    print("% --- TABLEAU DES PERFORMANCES INITIALES (ORIGINAL) ---")
    print("\\begin{table}[H]\n  \\centering\n  \\caption{Tableau de nos performances initiales (matrice d'évaluation)}\n  \\label{tab:perf_original}")
    print("  \\begin{tabular}{lccccccc}\n    \\toprule\n    Alternative & $g_1$ (Coût) & $g_2$ (Jules) & $g_3$ (Florent) & $g_4$ (Victor) & $g_5$ (Disp. J) & $g_6$ (Disp. F) & $g_7$ (Disp. V) \\\\")
    print("    \\midrule")
    for i, row in enumerate(PERF_MATRIX):
        print(f"    a{i+1} ({ALTERNATIVES[i].split('(')[1][:-1]}) & {row[0]:.0f}~€ & {row[1]:.1f}/10 & {row[2]:.1f}/10 & {row[3]:.1f}/10 & {row[4]:.1f}/5 & {row[5]:.1f}/5 & {row[6]:.1f}/5 \\\\")
    print("    \\bottomrule\n  \\end{tabular}\n\\end{table}\n")
    
    # B. Tableau des performances normalisées
    print("% --- TABLEAU DES PERFORMANCES NORMALISÉES ---")
    print("\\begin{table}[H]\n  \\centering\n  \\caption{Tableau des utilités normalisées (sur une échelle commune de 0 à 10)}\n  \\label{tab:perf_normalized}")
    print("  \\begin{tabular}{lccccccc}\n    \\toprule\n    Alternative & $u_1$ (Coût) & $u_2$ (Jules) & $u_3$ (Florent) & $u_4$ (Victor) & $u_5$ (Disp. J) & $u_6$ (Disp. F) & $u_7$ (Disp. V) \\\\")
    print("    \\midrule")
    for i, row in enumerate(norm_matrix):
        print(f"    a{i+1} ({ALTERNATIVES[i].split('(')[1][:-1]}) & {row[0]:.2f} & {row[1]:.2f} & {row[2]:.2f} & {row[3]:.2f} & {row[4]:.2f} & {row[5]:.2f} & {row[6]:.2f} \\\\")
    print("    \\bottomrule\n  \\end{tabular}\n\\end{table}\n")
    
    # C. Tableau de classement Somme Pondérée
    print("% --- TABLEAU DE CLASSEMENT DE LA SOMME PONDÉRÉE ---")
    print("\\begin{table}[H]\n  \\centering\n  \\caption{Résultats et classement par la méthode de la Somme Pondérée}\n  \\label{tab:ranking_ws}")
    print("  \\begin{tabular}{ccc}\n    \\toprule\n    Rang & Alternative & Score global \\\\\n    \\midrule")
    for rank, (idx, score) in enumerate(ws_ranking):
        print(f"    {rank + 1} & a{idx+1} ({ALTERNATIVES[idx].split('(')[1][:-1]}) & {score:.3f} \\\\")
    print("    \\bottomrule\n  \\end{tabular}\n\\end{table}\n")
    
    # D. Matrice de concordance
    print("% --- TABLEAU MATRICE DE CONCORDANCE ELECTRE I ---")
    print("\\begin{table}[H]\n  \\centering\n  \\caption{Matrice de concordance $C(a_i, a_j)$}\n  \\label{tab:concordance}")
    print("  \\begin{tabular}{ccccccc}\n    \\toprule\n    & $a_1$ & $a_2$ & $a_3$ & $a_4$ & $a_5$ & $a_6$ \\\\\n    \\midrule")
    for i, row in enumerate(concordance):
        row_str = " & ".join(f"{val:.2f}" for val in row)
        print(f"    $a_{i+1}$ & {row_str} \\\\")
    print("    \\bottomrule\n  \\end{tabular}\n\\end{table}\n")
    
    # E. Matrice de discordance (vetos)
    print("% --- TABLEAU MATRICE DE DISCORDANCE ELECTRE I (VETOS) ---")
    print("\\begin{table}[H]\n  \\centering\n  \\caption{Matrice de discordance (1 = Veto activé, 0 = Pas de veto)}\n  \\label{tab:discordance}")
    print("  \\begin{tabular}{ccccccc}\n    \\toprule\n    & $a_1$ & $a_2$ & $a_3$ & $a_4$ & $a_5$ & $a_6$ \\\\\n    \\midrule")
    for i, row in enumerate(discordance):
        row_str = " & ".join(f"{val}" for val in row)
        print(f"    $a_{i+1}$ & {row_str} \\\\")
    print("    \\bottomrule\n  \\end{tabular}\n\\end{table}\n")


# ==============================================================================
# 4. POINT D'ENTRÉE PRINCIPAL
# ==============================================================================

if __name__ == "__main__":
    # Étape 1 : Normalisation
    normalized = normalize_matrix(PERF_MATRIX)
    
    # Étape 2 : Résolution de la Somme Pondérée
    ws_results = solve_weighted_sum(normalized, WEIGHTS)
    
    # Étape 3 : Résolution d'ELECTRE I
    concordance_mat, discordance_mat = solve_electre_i(normalized, WEIGHTS, VETOES)
    
    # Étape 4 : Affichage textuel dans la console
    display_console_results(normalized, ws_results, concordance_mat, discordance_mat)
    
    # Étape 5 : Option pour imprimer le code LaTeX
    print("\n[INFO] Pour afficher le code LaTeX généré, décommentez la fonction generate_latex_tables() dans le code.")
    # generate_latex_tables(normalized, ws_results, concordance_mat, discordance_mat)
