"""
Gerador de casos de teste para a linguagem { a^i b^(2i) a^i | i > 0 }
"""
import json

def gerar_entrada_valida(i):
    """Gera uma entrada válida para a linguagem"""
    return 'a' * i + 'b' * (2 * i) + 'a' * i

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
        return False, "Sem b's"
    
    # Encontrar segunda sequência de a's
    pos_a2_start = pos_b_end
    
    # Contar
    i = pos_a1_end
    num_b = pos_b_end - pos_b_start
    a2 = len(entrada) - pos_a2_start
    
    # Verificar se só tem a's depois dos b's
    for k in range(pos_a2_start, len(entrada)):
        if entrada[k] != 'a':
            return False, f"Caractere inválido na posição {k}: '{entrada[k]}'"
    
    # Verificar condições
    if num_b != 2 * i:
        return False, f"b's ({num_b}) != 2×i ({2*i})"
    
    if a2 != i:
        return False, f"a's finais ({a2}) != i ({i})"
    
    return True, f"i={i}"

# Gerar casos de teste
test_cases = []

# CASOS VÁLIDOS
casos_validos = [
    (1, "caso mínimo válido"),
    (2, "i=2"),
    (3, "i=3"),
    (4, "i=4"),
    (5, "i=5"),
]

print("="*70)
print("CASOS VÁLIDOS")
print("="*70)

for i, descricao in casos_validos:
    entrada = gerar_entrada_valida(i)
    valido, motivo = validar_entrada(entrada)
    
    print(f"\n{descricao}: {entrada}")
    print(f"  i={i}, b's={2*i}")
    print(f"  a's iniciais={i}, b's={2*i}, a's finais={i}")
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
    ("aba", "i=1 mas só tem 1 'b' (deveria ter 2)"),
    ("aabbaa", "i=2 mas só tem 2 b's (deveria ter 4)"),
    ("aabbbba", "i=2 mas só tem 4 b's e 1 'a' final"),
    ("aabbbbaa", "i=2, tem 4 b's correto mas tem 2 a's finais (correto!) - VÁLIDO"),
    ("aabbbbaaa", "i=2, tem 4 b's mas tem 3 a's finais (deveria ter 2)"),
    ("aaabbbbbbaa", "i=3 mas só tem 6 b's, precisa de 2 a's finais"),
    ("ba", "Sem a's iniciais"),
    ("ab", "Sem a's finais e b insuficiente"),
    ("aa", "Sem b's"),
    ("abbba", "i=1 mas tem 3 b's (deveria ter 2)"),
    ("", "String vazia"),
    ("aabcbbaa", "Caractere inválido: 'c'"),
]

# Validar casos inválidos
casos_invalidos_validados = []
for entrada, motivo in casos_invalidos:
    if entrada == "aabbbbaa":  # Este é válido
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
        b_count = 0
        while i_count + b_count < len(entrada) and entrada[i_count + b_count] == 'b':
            b_count += 1
        a2_count = len(entrada) - i_count - b_count
        print(f"  a's iniciais={i_count}, b's={b_count}, a's finais={a2_count}")
    print(f"  Análise: {analise}")
    
    test_cases.append({
        "input": entrada,
        "expected": False,
        "reason": motivo
    })

# Adicionar o caso válido que foi filtrado
test_cases.insert(5, {
    "input": "aabbbbaa",
    "expected": True,
    "reason": "i=2 - a's iniciais=2, b's=4, a's finais=2"
})

# Salvar em JSON
output = {
    "language": "{ a^i b^(2i) a^i | i > 0 }",
    "test_cases": test_cases
}

with open('test_cases_C_correto.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\n" + "="*70)
print(f"✅ Gerados {len(test_cases)} casos de teste")
print(f"   Válidos: {sum(1 for t in test_cases if t['expected'])}")
print(f"   Inválidos: {sum(1 for t in test_cases if not t['expected'])}")
print("="*70)
print("📁 Arquivo salvo: test_cases_C_correto.json")

