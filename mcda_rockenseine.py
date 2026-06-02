# Alternatives:
# a1 : Mercredi (Me) - 75€
# a2 : Jeudi (Je) - 75€
# a3 : Vendredi (Ve) - 75€
# a4 : Samedi (Sa) - 75€
# a5 : Dimanche (Di) - 75€
# a6 : Pass 3 Jours (Ve+Sa+Di) - 185€
alternatives = [
    "a1 (Me)", "a2 (Je)", "a3 (Ve)", "a4 (Sa)", "a5 (Di)", "a6 (3 Jours)"
]

criteria_names = [
    "g1 (Coût)", 
    "g2 (Prog Jules)", 
    "g3 (Prog Florent)", 
    "g4 (Prog Victor)", 
    "g5 (Disp Jules)", 
    "g6 (Disp Florent)", 
    "g7 (Disp Victor)"
]

# Original evaluation matrix (6 alternatives, 7 criteria)
perf_matrix = [
    [75.0,  4.0, 9.0, 5.0, 5.0, 5.0, 5.0],  # a1 (Me)
    [75.0,  3.0, 4.0, 9.0, 5.0, 5.0, 5.0],  # a2 (Je)
    [75.0,  8.0, 5.0, 4.0, 5.0, 1.0, 5.0],  # a3 (Ve)
    [75.0,  5.0, 6.0, 6.0, 5.0, 5.0, 5.0],  # a4 (Sa)
    [75.0,  9.0, 3.0, 7.0, 5.0, 5.0, 1.0],  # a5 (Di)
    [185.0, 7.3, 4.7, 5.7, 5.0, 2.0, 2.0]   # a6 (3 Jours)
]

# Criteria weights
weights = [0.25, 0.15, 0.15, 0.15, 0.10, 0.10, 0.10]
assert abs(sum(weights) - 1.0) < 1e-9

# Normalize criteria to 0-10 scale
# For cost: min cost = 75 (utility = 10), max cost = 185 (utility = 0)
# Formula: u_1(a) = 10 * (185 - cost) / (185 - 75)
# For artistic (already 0-10): u_j(a) = g_j(a)
# For availability (0-5): u_j(a) = 2 * g_j(a)

normalized_matrix = []
for row in perf_matrix:
    norm_row = [0.0] * 7
    # Cost
    norm_row[0] = 10.0 * (185.0 - row[0]) / (185.0 - 75.0)
    # Artistic
    norm_row[1] = row[1]
    norm_row[2] = row[2]
    norm_row[3] = row[3]
    # Availabilities
    norm_row[4] = 2.0 * row[4]
    norm_row[5] = 2.0 * row[5]
    norm_row[6] = 2.0 * row[6]
    normalized_matrix.append(norm_row)

# --------------------------------------------------------------------------------
# METHOD 1: WEIGHTED SUM (Somme Pondérée)
# --------------------------------------------------------------------------------
weighted_sum_scores = []
for row in normalized_matrix:
    score = sum(val * w for val, w in zip(row, weights))
    weighted_sum_scores.append(score)

ranking_ws = sorted(range(len(weighted_sum_scores)), key=lambda k: weighted_sum_scores[k], reverse=True)

# --------------------------------------------------------------------------------
# METHOD 2: ELECTRE I
# --------------------------------------------------------------------------------
# Veto thresholds on normalized 0-10 scale:
vetoes = [9.0, 6.0, 6.0, 6.0, 5.0, 5.0, 5.0]

num_alts = len(alternatives)
concordance_matrix = [[0.0] * num_alts for _ in range(num_alts)]
discordance_matrix = [[0] * num_alts for _ in range(num_alts)] # 1 if veto exists, 0 otherwise

for i in range(num_alts):
    for j in range(num_alts):
        if i == j:
            concordance_matrix[i][j] = 1.0
            discordance_matrix[i][j] = 0
            continue
            
        # Concordance: sum of weights where u_k(ai) >= u_k(aj)
        conc_weight = 0.0
        veto_triggered = 0
        for k in range(len(weights)):
            if normalized_matrix[i][k] >= normalized_matrix[j][k]:
                conc_weight += weights[k]
            else:
                # Check veto: if u_k(aj) - u_k(ai) > vetoes[k]
                diff = normalized_matrix[j][k] - normalized_matrix[i][k]
                if diff > vetoes[k]:
                    veto_triggered = 1
        
        concordance_matrix[i][j] = conc_weight
        discordance_matrix[i][j] = veto_triggered

# Outranking for a given gamma
def get_outranking_matrix(gamma):
    outranking = [[0] * num_alts for _ in range(num_alts)]
    for i in range(num_alts):
        for j in range(num_alts):
            if i == j:
                continue
            if concordance_matrix[i][j] >= gamma and discordance_matrix[i][j] == 0:
                outranking[i][j] = 1
    return outranking

# Kernel calculation
def find_kernel(outranking_mat):
    from itertools import combinations
    kernels = []
    all_indices = set(range(num_alts))
    for r in range(1, num_alts + 1):
        for comb in combinations(range(num_alts), r):
            K = set(comb)
            # Check internal stability
            int_stable = True
            for u in K:
                for v in K:
                    if u != v and outranking_mat[u][v] == 1:
                        int_stable = False
                        break
                if not int_stable:
                    break
            
            if not int_stable:
                continue
                
            # Check external stability
            ext_stable = True
            for x in all_indices - K:
                outranked = False
                for y in K:
                    if outranking_mat[y][x] == 1:
                        outranked = True
                        break
                if not outranked:
                    ext_stable = False
                    break
            
            if ext_stable:
                kernels.append(list(K))
    return kernels

# --------------------------------------------------------------------------------
# GENERATE LATEX CODE SNIPPETS
# --------------------------------------------------------------------------------
def print_latex_tables():
    print("% ========================================== %")
    print("% TABLEAU DES PERFORMANCES (ORIGINAL)       %")
    print("% ========================================== %")
    print("\\begin{table}[htbp]")
    print("  \\centering")
    print("  \\caption{Tableau des performances initiales (matrice d'évaluation)}")
    print("  \\label{tab:perf_original}")
    print("  \\begin{tabular}{lccccccc}")
    print("    \\toprule")
    print("    Alternative & $g_1$ (Coût) & $g_2$ (Jules) & $g_3$ (Florent) & $g_4$ (Victor) & $g_5$ (Disp. J) & $g_6$ (Disp. F) & $g_7$ (Disp. V) \\\\")
    print("    \\midrule")
    for i in range(num_alts):
        row = perf_matrix[i]
        print(f"    {alternatives[i]} & {row[0]:.0f}~€ & {row[1]:.1f}/10 & {row[2]:.1f}/10 & {row[3]:.1f}/10 & {row[4]:.1f}/5 & {row[5]:.1f}/5 & {row[6]:.1f}/5 \\\\")
    print("    \\bottomrule")
    print("  \\end{tabular}")
    print("\\end{table}")
    print()

    print("% ========================================== %")
    print("% TABLEAU DES PERFORMANCES NORMALISÉES     %")
    print("% ========================================== %")
    print("\\begin{table}[htbp]")
    print("  \\centering")
    print("  \\caption{Tableau des utilités normalisées (sur une échelle commune de 0 à 10)}")
    print("  \\label{tab:perf_normalized}")
    print("  \\begin{tabular}{lccccccc}")
    print("    \\toprule")
    print("    Alternative & $u_1$ (Coût) & $u_2$ (Jules) & $u_3$ (Florent) & $u_4$ (Victor) & $u_5$ (Disp. J) & $u_6$ (Disp. F) & $u_7$ (Disp. V) \\\\")
    print("    \\midrule")
    for i in range(num_alts):
        row = normalized_matrix[i]
        print(f"    {alternatives[i]} & {row[0]:.2f} & {row[1]:.2f} & {row[2]:.2f} & {row[3]:.2f} & {row[4]:.2f} & {row[5]:.2f} & {row[6]:.2f} \\\\")
    print("    \\bottomrule")
    print("  \\end{tabular}")
    print("\\end{table}")
    print()

    print("% ========================================== %")
    print("% SCORE ET CLASSEMENT DE LA SOMME PONDÉRÉE  %")
    print("% ========================================== %")
    print("\\begin{table}[htbp]")
    print("  \\centering")
    print("  \\caption{Résultats et classement par la méthode de la Somme Pondérée}")
    print("  \\label{tab:ranking_ws}")
    print("  \\begin{tabular}{ccc}")
    print("    \\toprule")
    print("    Rang & Alternative & Score global \\\\")
    print("    \\midrule")
    for idx, r in enumerate(ranking_ws):
        print(f"    {idx+1} & {alternatives[r]} & {weighted_sum_scores[r]:.3f} \\\\")
    print("    \\bottomrule")
    print("  \\end{tabular}")
    print("\\end{table}")
    print()

    print("% ========================================== %")
    print("% MATRICE DE CONCORDANCE ELECTRE I          %")
    print("% ========================================== %")
    print("\\begin{table}[htbp]")
    print("  \\centering")
    print("  \\caption{Matrice de concordance $C(a_i, a_j)$}")
    print("  \\label{tab:concordance}")
    print("  \\begin{tabular}{ccccccc}")
    print("    \\toprule")
    print("    & $a_1$ & $a_2$ & $a_3$ & $a_4$ & $a_5$ & $a_6$ \\\\")
    print("    \\midrule")
    for i in range(num_alts):
        row_str = f"    $a_{i+1}$"
        for j in range(num_alts):
            row_str += f" & {concordance_matrix[i][j]:.2f}"
        row_str += " \\\\"
        print(row_str)
    print("    \\bottomrule")
    print("  \\end{tabular}")
    print("\\end{table}")
    print()

    print("% ========================================== %")
    print("% MATRICE DE DISCORDANCE / VETO ELECTRE I    %")
    print("% ========================================== %")
    print("\\begin{table}[htbp]")
    print("  \\centering")
    print("  \\caption{Matrice de discordance (1 = Veto activé, 0 = Pas de veto)}")
    print("  \\label{tab:discordance}")
    print("  \\begin{tabular}{ccccccc}")
    print("    \\toprule")
    print("    & $a_1$ & $a_2$ & $a_3$ & $a_4$ & $a_5$ & $a_6$ \\\\")
    print("    \\midrule")
    for i in range(num_alts):
        row_str = f"    $a_{i+1}$"
        for j in range(num_alts):
            row_str += f" & {discordance_matrix[i][j]}"
        row_str += " \\\\"
        print(row_str)
    print("    \\bottomrule")
    print("  \\end{tabular}")
    print("\\end{table}")
    print()

if __name__ == "__main__":
    print_latex_tables()
