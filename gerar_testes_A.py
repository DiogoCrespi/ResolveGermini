"""
Gerador de casos de teste para a linguagem { a^n b^m c^(2n) d^m | n > 0 e m > 0 }
"""
import json

def gerar_entrada_valida(n, m):
    """Gera uma entrada válida para a linguagem"""
    return 'a' * n + 'b' * m + 'c' * (2 * n) + 'd' * m

def validar_entrada(entrada):
    """Valida se uma entrada pertence à linguagem"""
    # Contar ocorrências
    count_a = entrada.count('a')
    count_b = entrada.count('b')
    count_c = entrada.count('c')
    count_d = entrada.count('d')
    
    # Verificar ordem
    last_a = entrada.rfind('a')
    first_b = entrada.find('b')
    last_b = entrada.rfind('b')
    first_c = entrada.find('c')
    last_c = entrada.rfind('c')
    first_d = entrada.find('d')
    
    # Verificar se a ordem é a^n b^m c^(2n) d^m
    if last_a >= first_b if first_b != -1 else False:
        return False, "a's devem vir antes de b's"
    if last_b >= first_c if first_c != -1 else False:
        return False, "b's devem vir antes de c's"
    if last_c >= first_d if first_d != -1 else False:
        return False, "c's devem vir antes de d's"
    
    # Verificar condições da linguagem
    if count_a == 0:
        return False, "n deve ser > 0 (sem a's)"
    if count_b == 0:
        return False, "m deve ser > 0 (sem b's)"
    if count_c != 2 * count_a:
        return False, f"c's ({count_c}) != 2 × a's ({count_a})"
    if count_d != count_b:
        return False, f"d's ({count_d}) != b's ({count_b})"
    
    # Verificar se contém apenas a, b, c, d
    for char in entrada:
        if char not in 'abcd':
            return False, f"Caractere inválido: '{char}'"
    
    return True, f"n={count_a}, m={count_b}"

# Gerar casos de teste
test_cases = []

# CASOS VÁLIDOS
casos_validos = [
    (1, 1, "caso mínimo válido"),
    (1, 2, "n=1, m=2"),
    (2, 1, "n=2, m=1"),
    (2, 2, "n=2, m=2"),
    (3, 1, "n=3, m=1"),
    (3, 2, "n=3, m=2"),
    (4, 3, "n=4, m=3"),
    (5, 5, "caso maior")
]

print("="*70)
print("CASOS VÁLIDOS")
print("="*70)

for n, m, descricao in casos_validos:
    entrada = gerar_entrada_valida(n, m)
    valido, motivo = validar_entrada(entrada)
    
    # Contar caracteres para verificação
    print(f"\n{descricao}: {entrada}")
    print(f"  a's={entrada.count('a')}, b's={entrada.count('b')}, "
          f"c's={entrada.count('c')}, d's={entrada.count('d')}")
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
    ("abcd", "Falta um c (precisa de 2 c's para n=1)"),
    ("aabbccdd", "n=2 mas só tem 2 c's (deveria ter 4)"),
    ("abccdd", "m=2 (2 d's) mas só tem 1 b"),
    ("abbbccd", "m=3 (3 b's) mas só tem 1 d"),
    ("aabcccccd", "n=2 mas tem c a mais (5 c's, deveria ter 4)"),
    ("bccd", "Falta a (n deve ser > 0)"),
    ("accd", "Falta b (m deve ser > 0)"),
    ("abcc", "Falta d (m deve ser > 0)"),
    ("abbdccdd", "Ordem incorreta (d antes de c)"),
    ("aabbccccbdd", "Ordem incorreta (b no meio dos c's)"),
    ("", "String vazia"),
    ("aaabcccccc", "m=0 (sem b's)")
]

for entrada, motivo in casos_invalidos:
    valido, analise = validar_entrada(entrada) if entrada else (False, "String vazia")
    
    print(f"\n{entrada or '(vazio)'}: {motivo}")
    if entrada:
        print(f"  a's={entrada.count('a')}, b's={entrada.count('b')}, "
              f"c's={entrada.count('c')}, d's={entrada.count('d')}")
    print(f"  Análise: {analise}")
    
    test_cases.append({
        "input": entrada,
        "expected": False,
        "reason": motivo
    })

# Salvar em JSON
output = {
    "language": "{ a^n b^m c^(2n) d^m | n > 0 e m > 0 }",
    "test_cases": test_cases
}

with open('test_cases_A_correto.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\n" + "="*70)
print(f"✅ Gerados {len(test_cases)} casos de teste")
print(f"   Válidos: {sum(1 for t in test_cases if t['expected'])}")
print(f"   Inválidos: {sum(1 for t in test_cases if not t['expected'])}")
print("="*70)
print("📁 Arquivo salvo: test_cases_A_correto.json")

