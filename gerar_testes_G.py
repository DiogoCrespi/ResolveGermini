#!/usr/bin/env python3
"""
Gerador de casos de teste para a linguagem G: {wwR | w ∈ {a, b}*}
onde wR é o inverso de w
"""

import json

def validar_entrada(entrada):
    """Valida se uma entrada pertence à linguagem {wwR | w ∈ {a,b}*}"""
    if not entrada:
        return True, "String vazia (w=ε, wR=ε)"  # εε = ε
    
    # Verificar se só contém a's e b's
    for char in entrada:
        if char not in ['a', 'b']:
            return False, f"Caractere inválido: '{char}'"
    
    # Verificar se tem tamanho par
    if len(entrada) % 2 != 0:
        return False, f"Tamanho ímpar ({len(entrada)}), deve ser par para wwR"
    
    # Dividir ao meio
    meio = len(entrada) // 2
    w = entrada[:meio]
    wR = entrada[meio:]
    
    # Verificar se wR é realmente o inverso de w
    if wR != w[::-1]:
        return False, f"Segunda metade ({wR}) não é inverso da primeira ({w})"
    
    return True, f"w={w}, wR={wR}"

def gerar_testes_G():
    """Gera casos de teste para a linguagem {wwR | w ∈ {a,b}*}"""
    
    casos_validos = []
    casos_invalidos = []
    
    # Casos válidos específicos
    casos_validos.extend([
        "",           # String vazia (εε)
        "aa",         # w=a, wR=a
        "bb",         # w=b, wR=b
        "abba",       # w=ab, wR=ba
        "baab",       # w=ba, wR=ab
        "aaaa",       # w=aa, wR=aa
        "bbbb",       # w=bb, wR=bb
        "aabbaa",     # w=aab, wR=baa
        "aabbbbaa",   # w=aabb, wR=bbaa
        "aabbaabbaa", # w=aabba, wR=abbaa
        "bbabbaabbb", # w=bbabb, wR=bbabb (não é wwR!)
        "abababab",   # w=abab, wR=baba
        "babababa",   # w=baba, wR=abab
        "aaabbbaaa",  # w=aaab, wR=baaa
        "bbbaaabbb",  # w=bbba, wR=abbb
        "ababababab", # w=ababa, wR=babab
        "bababababa", # w=babab, wR=ababa
        "aabbaabbaabbaabb", # w=aabbaabb, wR=bbaaabba
        "bbabbaabbaabbaab", # w=bbabbaab, wR=baabbaab
    ])
    
    # Casos inválidos específicos
    casos_invalidos.extend([
        "a",          # Tamanho ímpar
        "b",          # Tamanho ímpar
        "ab",         # w=a, wR=b (não é inverso)
        "ba",         # w=b, wR=a (não é inverso)
        "abc",        # Caractere inválido 'c'
        "aab",        # Tamanho ímpar
        "abb",        # Tamanho ímpar
        "abab",       # w=ab, wR=ab (não é inverso)
        "aabb",       # w=aa, wR=bb (não é inverso)
        "bbaa",       # w=bb, wR=aa (não é inverso)
        "ababab",     # w=aba, wR=bab (não é inverso)
        "bababa",     # w=bab, wR=aba (não é inverso)
        "bbabab",     # w=bba, wR=bab (não é inverso)
        "ababba",     # w=aba, wR=bba (não é inverso)
        "bbaaabbb",   # w=bbaa, wR=abbb (não é inverso)
        "abababababababab", # Padrão repetitivo que não é wwR
        "babababababababa", # Padrão repetitivo que não é wwR
        "aabbaabbaabbaabb", # Padrão repetitivo que não é wwR
        "bbabbaabbaabbaab", # Padrão repetitivo que não é wwR
        "aabbcc",     # Caracteres inválidos
        "aabb1",      # Caractere inválido '1'
        "aabbx",      # Caractere inválido 'x'
        "aabb ",      # Espaço
        "aabb\n",     # Quebra de linha
        "aabb\t",     # Tab
        "aabb\r",     # Carriage return
        "aabb\0",     # Null character
        "aabb\b",     # Backspace
        "aabb\f",     # Form feed
        "aabb\v",     # Vertical tab
        "aabb\a",     # Bell
    ])
    
    # Validar e filtrar casos
    casos_validos_filtrados = []
    casos_invalidos_filtrados = []
    
    print("="*70)
    print("VALIDANDO CASOS VÁLIDOS")
    print("="*70)
    
    for caso in casos_validos:
        valido, motivo = validar_entrada(caso)
        if valido:
            casos_validos_filtrados.append(caso)
            print(f"✅ {caso or '(vazio)'}: {motivo}")
        else:
            print(f"❌ {caso or '(vazio)'}: {motivo}")
    
    print("\n" + "="*70)
    print("VALIDANDO CASOS INVÁLIDOS")
    print("="*70)
    
    for caso in casos_invalidos:
        valido, motivo = validar_entrada(caso)
        if not valido:
            casos_invalidos_filtrados.append(caso)
            print(f"✅ {caso or '(vazio)'}: {motivo}")
        else:
            print(f"❌ {caso or '(vazio)'}: {motivo}")
    
    # Combinar todos os casos
    todos_casos = []
    
    # Adicionar casos válidos
    for caso in casos_validos_filtrados:
        todos_casos.append({
            "input": caso,
            "expected": True,
            "description": f"Caso válido: {caso or '(string vazia)'}"
        })
    
    # Adicionar casos inválidos
    for caso in casos_invalidos_filtrados:
        todos_casos.append({
            "input": caso,
            "expected": False,
            "description": f"Caso inválido: {caso or '(string vazia)'}"
        })
    
    return {
        "language": "G: {wwR | w ∈ {a, b}*}",
        "test_cases": todos_casos
    }

if __name__ == "__main__":
    testes = gerar_testes_G()
    
    with open("test_cases_G_correto.json", "w", encoding="utf-8") as f:
        json.dump(testes, f, indent=2, ensure_ascii=False)
    
    print(f"\nGerados {len(testes['test_cases'])} casos de teste para a linguagem G")
    print(f"Casos válidos: {sum(1 for caso in testes['test_cases'] if caso['expected'])}")
    print(f"Casos inválidos: {sum(1 for caso in testes['test_cases'] if not caso['expected'])}")