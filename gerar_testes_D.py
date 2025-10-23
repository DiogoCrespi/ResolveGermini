"""
Gerador de casos de teste para a linguagem { a^n b^k c^m | n, k > m }
"""
import json

def gerar_entrada_valida(n, k, m):
    """Gera uma entrada válida para a linguagem"""
    return 'a' * n + 'b' * k + 'c' * m

def validar_entrada(entrada):
    """Valida se uma entrada pertence à linguagem"""
    if not entrada:
        return False, "String vazia"
    
    # Contar ocorrências
    pos_a_end = 0
    while pos_a_end < len(entrada) and entrada[pos_a_end] == 'a':
        pos_a_end += 1
    
    pos_b_start = pos_a_end
    pos_b_end = pos_b_start
    while pos_b_end < len(entrada) and entrada[pos_b_end] == 'b':
        pos_b_end += 1
    
    pos_c_start = pos_b_end
    
    # Contar
    n = pos_a_end
    k = pos_b_end - pos_b_start
    m = len(entrada) - pos_c_start
    
    # Verificar se só tem c's depois dos b's
    for i in range(pos_c_start, len(entrada)):
        if entrada[i] != 'c':
            return False, f"Caractere inválido na posição {i}: '{entrada[i]}'"
    
    # Verificar condições: n > m e k > m
    if n <= m:
        return False, f"n ({n}) deve ser > m ({m})"
    if k <= m:
        return False, f"k ({k}) deve ser > m ({m})"
    
    return True, f"n={n}, k={k}, m={m}"

# Gerar casos de teste
test_cases = []

# CASOS VÁLIDOS
casos_validos = [
    (2, 2, 1, "caso mínimo válido"),
    (3, 2, 1, "n=3, k=2, m=1"),
    (2, 3, 1, "n=2, k=3, m=1"),
    (3, 3, 1, "n=3, k=3, m=1"),
    (3, 3, 2, "n=3, k=3, m=2"),
    (4, 3, 2, "n=4, k=3, m=2"),
    (3, 4, 2, "n=3, k=4, m=2"),
    (5, 5, 3, "caso maior"),
    (2, 2, 0, "m=0 permitido (n,k > 0)"),
]

print("="*70)
print("CASOS VÁLIDOS")
print("="*70)

for n, k, m, descricao in casos_validos:
    entrada = gerar_entrada_valida(n, k, m)
    valido, motivo = validar_entrada(entrada)
    
    print(f"\n{descricao}: {entrada}")
    print(f"  n={n}, k={k}, m={m}")
    print(f"  Condições: n>{m} ({n}>{m}), k>{m} ({k}>{m})")
    print(f"  Validação: {motivo}")
    
    test_cases.append({
        "input": entrada,
        "expected": True,
        "reason": f"{descricao} - {motivo}"
    })

# CASOS INVÁLIDOS
print("\n" + "="*70)
print("CASOS INVÁLIDOS")
print("="*70)

casos_invalidos = [
    ("abc", "n=1, k=1, m=1 (n e k não são > m)"),
    ("aabbc", "n=2, k=2, m=1 mas tem c extra - VÁLIDO!"),
    ("aabc", "n=2, k=1, m=1 (k não é > m)"),
    ("abbc", "n=1, k=2, m=1 (n não é > m)"),
    ("aabbcc", "n=2, k=2, m=2 (n e k não são > m)"),
    ("aaabbbccc", "n=3, k=3, m=3 (n e k não são > m)"),
    ("ac", "k=0 (sem b's)"),
    ("bc", "n=0 (sem a's)"),
    ("ab", "m=0 - VÁLIDO se n,k > 0!"),
    ("", "String vazia"),
    ("aaabbcc", "n=3, k=2, m=2 (k não é > m)"),
    ("aabbbcc", "n=2, k=3, m=2 (n não é > m)"),
    ("aabcbcc", "Ordem incorreta (b no meio dos c's)"),
    ("abxc", "Caractere inválido: 'x'"),
]

# Filtrar casos que são válidos
casos_invalidos_filtrados = []
for entrada, motivo in casos_invalidos:
    if entrada in ["aabbc", "ab"]:  # Estes são válidos
        continue
    casos_invalidos_filtrados.append((entrada, motivo))

for entrada, motivo in casos_invalidos_filtrados:
    valido, analise = validar_entrada(entrada) if entrada else (False, "String vazia")
    
    print(f"\n{entrada or '(vazio)'}: {motivo}")
    if entrada:
        # Analisar estrutura
        n_count = 0
        while n_count < len(entrada) and entrada[n_count] == 'a':
            n_count += 1
        k_count = 0
        while n_count + k_count < len(entrada) and entrada[n_count + k_count] == 'b':
            k_count += 1
        m_count = len(entrada) - n_count - k_count
        print(f"  n={n_count}, k={k_count}, m={m_count}")
    print(f"  Análise: {analise}")
    
    test_cases.append({
        "input": entrada,
        "expected": False,
        "reason": motivo
    })

# Adicionar casos válidos que foram filtrados
test_cases.extend([
    {
        "input": "aabbc",
        "expected": True,
        "reason": "n=2, k=2, m=1 - válido (n>m, k>m)"
    },
    {
        "input": "ab",
        "expected": True,
        "reason": "n=1, k=1, m=0 - válido (n>m, k>m)"
    }
])

# Salvar em JSON
output = {
    "language": "{ a^n b^k c^m | n, k > m }",
    "test_cases": test_cases
}

with open('test_cases_D_correto.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\n" + "="*70)
print(f"✅ Gerados {len(test_cases)} casos de teste")
print(f"   Válidos: {sum(1 for t in test_cases if t['expected'])}")
print(f"   Inválidos: {sum(1 for t in test_cases if not t['expected'])}")
print("="*70)
print("📁 Arquivo salvo: test_cases_D_correto.json")

