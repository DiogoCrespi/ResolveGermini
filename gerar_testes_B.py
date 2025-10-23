"""
Gerador de casos de teste para a linguagem { a^i b^j a^(i+j) | i, j > 0 }
"""
import json

def gerar_entrada_valida(i, j):
    """Gera uma entrada válida para a linguagem"""
    return 'a' * i + 'b' * j + 'a' * (i + j)

def validar_entrada(entrada):
    """Valida se uma entrada pertence à linguagem"""
    if not entrada:
        return False, "String vazia"
    
    # Contar posições
    pos_a1_end = 0
    pos_b_start = -1
    pos_b_end = -1
    pos_a2_start = -1
    
    # Encontrar primeira sequência de a's
    while pos_a1_end < len(entrada) and entrada[pos_a1_end] == 'a':
        pos_a1_end += 1
    
    if pos_a1_end == 0:
        return False, "Sem a's iniciais (i deve ser > 0)"
    
    # Encontrar sequência de b's
    pos_b_start = pos_a1_end
    pos_b_end = pos_b_start
    while pos_b_end < len(entrada) and entrada[pos_b_end] == 'b':
        pos_b_end += 1
    
    if pos_b_end == pos_b_start:
        return False, "Sem b's (j deve ser > 0)"
    
    # Encontrar segunda sequência de a's
    pos_a2_start = pos_b_end
    
    # Contar
    i = pos_a1_end
    j = pos_b_end - pos_b_start
    a2 = len(entrada) - pos_a2_start
    
    # Verificar se só tem a's depois dos b's
    for k in range(pos_a2_start, len(entrada)):
        if entrada[k] != 'a':
            return False, f"Caractere inválido na posição {k}: '{entrada[k]}'"
    
    # Verificar condição i+j
    if a2 != i + j:
        return False, f"a's finais ({a2}) != i+j ({i}+{j}={i+j})"
    
    return True, f"i={i}, j={j}, i+j={i+j}"

# Gerar casos de teste
test_cases = []

# CASOS VÁLIDOS
casos_validos = [
    (1, 1, "caso mínimo válido"),
    (1, 2, "i=1, j=2"),
    (2, 1, "i=2, j=1"),
    (2, 2, "i=2, j=2"),
    (3, 1, "i=3, j=1"),
    (3, 2, "i=3, j=2"),
    (2, 3, "i=2, j=3"),
    (4, 4, "caso maior")
]

print("="*70)
print("CASOS VÁLIDOS")
print("="*70)

for i, j, descricao in casos_validos:
    entrada = gerar_entrada_valida(i, j)
    valido, motivo = validar_entrada(entrada)
    
    print(f"\n{descricao}: {entrada}")
    print(f"  i={i}, j={j}, i+j={i+j}")
    print(f"  a's iniciais={i}, b's={j}, a's finais={i+j}")
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
    ("aba", "i=1, j=1 mas só tem 1 'a' final (deveria ter 2)"),
    ("abaa", "i=1, j=1, tem 2 a's finais correto - AGUARDE, ISSO É VÁLIDO!"),
    ("aabaa", "i=2, j=1 mas só tem 2 a's finais (deveria ter 3)"),
    ("aabaaa", "i=2, j=1, tem 3 a's finais - VÁLIDO! Remover"),
    ("aabbaa", "i=2, j=2 mas só tem 2 a's finais (deveria ter 4)"),
    ("aabbaaa", "i=2, j=2 mas só tem 3 a's finais (deveria ter 4)"),
    ("aabbaaaaa", "i=2, j=2, tem 5 a's finais (deveria ter 4)"),
    ("ba", "Sem a's iniciais (i deve ser > 0)"),
    ("aa", "Sem b's (j deve ser > 0)"),
    ("aabba", "i=2, j=2 mas só tem 1 'a' final (deveria ter 4)"),
    ("baa", "Sem a's iniciais"),
    ("abb", "Sem a's finais"),
    ("aabcaa", "Caractere inválido: 'c'"),
    ("", "String vazia"),
    ("aabbbaaa", "i=2, j=3 mas só tem 3 a's finais (deveria ter 5)"),
]

# Revalidar casos inválidos
casos_invalidos_validados = []
for entrada, motivo in casos_invalidos:
    if entrada in ["abaa", "aabaaa"]:  # Pular válidos
        continue
    casos_invalidos_validados.append((entrada, motivo))

for entrada, motivo in casos_invalidos_validados:
    valido, analise = validar_entrada(entrada) if entrada else (False, "String vazia")
    
    print(f"\n{entrada or '(vazio)'}: {motivo}")
    if entrada:
        # Analisar estrutura
        i_count = 0
        while i_count < len(entrada) and entrada[i_count] == 'a':
            i_count += 1
        j_count = 0
        while i_count + j_count < len(entrada) and entrada[i_count + j_count] == 'b':
            j_count += 1
        a2_count = len(entrada) - i_count - j_count
        print(f"  a's iniciais={i_count}, b's={j_count}, a's finais={a2_count}")
    print(f"  Análise: {analise}")
    
    test_cases.append({
        "input": entrada,
        "expected": False,
        "reason": motivo
    })

# Salvar em JSON
output = {
    "language": "{ a^i b^j a^(i+j) | i, j > 0 }",
    "test_cases": test_cases
}

with open('test_cases_B_correto.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\n" + "="*70)
print(f"✅ Gerados {len(test_cases)} casos de teste")
print(f"   Válidos: {sum(1 for t in test_cases if t['expected'])}")
print(f"   Inválidos: {sum(1 for t in test_cases if not t['expected'])}")
print("="*70)
print("📁 Arquivo salvo: test_cases_B_correto.json")

