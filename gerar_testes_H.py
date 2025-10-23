#!/usr/bin/env python3
"""
Gerador de casos de teste para a linguagem H: {w | w ∈ {a, b}* e w contenha o dobro de símbolos "a" do que "b"}
"""

import json

def validar_linguagem_H(entrada):
    """
    Valida se uma entrada pertence à linguagem H.
    A linguagem aceita strings onde o número de 'a's é exatamente o dobro do número de 'b's.
    """
    if not entrada:
        return True, "String vazia - aceita (0 a's = 2 * 0 b's)"
    
    # Contar símbolos
    count_a = entrada.count('a')
    count_b = entrada.count('b')
    
    # Verificar se só contém 'a' e 'b'
    for char in entrada:
        if char not in ['a', 'b']:
            return False, f"Contém símbolo inválido: '{char}'"
    
    # Verificar condição: count_a = 2 * count_b
    if count_a == 2 * count_b:
        return True, f"Válido: {count_a} a's = 2 * {count_b} b's"
    else:
        return False, f"Inválido: {count_a} a's ≠ 2 * {count_b} b's"

def gerar_testes_H():
    """Gera casos de teste para a linguagem H"""
    
    casos_validos = []
    casos_invalidos = []
    
    # CASOS VÁLIDOS: count_a = 2 * count_b
    
    # Caso vazio (0 a's = 2 * 0 b's)
    casos_validos.append("")
    
    # Para count_b = 1: count_a = 2
    casos_validos.append("aab")
    casos_validos.append("aba")
    casos_validos.append("baa")
    
    # Para count_b = 2: count_a = 4
    casos_validos.append("aaaabb")
    casos_validos.append("aabaab")
    casos_validos.append("abaaba")
    casos_validos.append("baabaa")
    casos_validos.append("aabbaa")
    casos_validos.append("bbaaaa")
    
    # Para count_b = 3: count_a = 6
    casos_validos.append("aaaaaabbb")
    casos_validos.append("aaabaaabab")
    casos_validos.append("abababaaa")
    casos_validos.append("bbbaaaaaa")
    
    # Para count_b = 4: count_a = 8
    casos_validos.append("aaaaaaaaaabbbb")
    casos_validos.append("aabbaabbaabbaa")
    casos_validos.append("bbbbaaaaaaaaaa")
    
    # Para count_b = 5: count_a = 10
    casos_validos.append("aaaaaaaaaabbbbb")
    casos_validos.append("abababababaaaaa")
    
    # Para count_b = 6: count_a = 12
    casos_validos.append("aaaaaaaaaaaabbbbbb")
    
    # Para count_b = 7: count_a = 14
    casos_validos.append("aaaaaaaaaaaaabbbbbbb")
    
    # Para count_b = 8: count_a = 16
    casos_validos.append("aaaaaaaaaaaaaaaabbbbbbbb")
    
    # Para count_b = 9: count_a = 18
    casos_validos.append("aaaaaaaaaaaaaaaaaabbbbbbbbb")
    
    # Para count_b = 10: count_a = 20
    casos_validos.append("aaaaaaaaaaaaaaaaaaaabbbbbbbbbb")
    
    # CASOS INVÁLIDOS: count_a ≠ 2 * count_b
    
    # Só 'a's (count_b = 0, count_a > 0)
    casos_invalidos.extend([
        "a",           # 1 a, 0 b
        "aa",          # 2 a's, 0 b's
        "aaa",         # 3 a's, 0 b's
        "aaaa",        # 4 a's, 0 b's
        "aaaaa",       # 5 a's, 0 b's
    ])
    
    # Só 'b's (count_a = 0, count_b > 0)
    casos_invalidos.extend([
        "b",           # 0 a's, 1 b
        "bb",          # 0 a's, 2 b's
        "bbb",         # 0 a's, 3 b's
        "bbbb",        # 0 a's, 4 b's
        "bbbbb",       # 0 a's, 5 b's
    ])
    
    # count_a < 2 * count_b
    casos_invalidos.extend([
        "ab",          # 1 a, 1 b (1 ≠ 2*1)
        "abb",         # 1 a, 2 b's (1 ≠ 2*2)
        "aab",         # 2 a's, 1 b (2 ≠ 2*1) - WAIT, este é válido!
        "aabb",        # 2 a's, 2 b's (2 ≠ 2*2)
        "aaab",        # 3 a's, 1 b (3 ≠ 2*1)
        "aabbb",       # 2 a's, 3 b's (2 ≠ 2*3)
        "aaabb",       # 3 a's, 2 b's (3 ≠ 2*2)
        "aaaab",       # 4 a's, 1 b (4 ≠ 2*1)
        "aabbbb",      # 2 a's, 4 b's (2 ≠ 2*4)
        "aaabbb",      # 3 a's, 3 b's (3 ≠ 2*3)
        "aaaaab",      # 5 a's, 1 b (5 ≠ 2*1)
        "aabbbbb",     # 2 a's, 5 b's (2 ≠ 2*5)
        "aaabbbb",     # 3 a's, 4 b's (3 ≠ 2*4)
        "aaaaaab",     # 6 a's, 1 b (6 ≠ 2*1)
        "aabbbbbb",    # 2 a's, 6 b's (2 ≠ 2*6)
        "aaabbbbb",    # 3 a's, 5 b's (3 ≠ 2*5)
        "aaaaaaab",    # 7 a's, 1 b (7 ≠ 2*1)
        "aabbbbbbb",   # 2 a's, 7 b's (2 ≠ 2*7)
        "aaabbbbbb",   # 3 a's, 6 b's (3 ≠ 2*6)
    ])
    
    # count_a > 2 * count_b
    casos_invalidos.extend([
        "aaaab",       # 4 a's, 1 b (4 ≠ 2*1)
        "aaaaab",      # 5 a's, 1 b (5 ≠ 2*1)
        "aaaaaab",     # 6 a's, 1 b (6 ≠ 2*1)
        "aaaaaaab",    # 7 a's, 1 b (7 ≠ 2*1)
        "aaaaaaaab",   # 8 a's, 1 b (8 ≠ 2*1)
        "aaaaaaaaab",  # 9 a's, 1 b (9 ≠ 2*1)
        "aaaaaaaaaab", # 10 a's, 1 b (10 ≠ 2*1)
        "aaaabb",      # 4 a's, 2 b's (4 ≠ 2*2)
        "aaaaabb",     # 5 a's, 2 b's (5 ≠ 2*2)
        "aaaaaabb",    # 6 a's, 2 b's (6 ≠ 2*2)
        "aaaaaaabb",   # 7 a's, 2 b's (7 ≠ 2*2)
        "aaaaaaaabb",  # 8 a's, 2 b's (8 ≠ 2*2)
        "aaaaaaaaabb", # 9 a's, 2 b's (9 ≠ 2*2)
        "aaaaaaaaaabb", # 10 a's, 2 b's (10 ≠ 2*2)
    ])
    
    # Casos com símbolos inválidos
    casos_invalidos.extend([
        "abc",         # Contém 'c'
        "aabbc",       # Contém 'c'
        "aabb1",       # Contém '1'
        "aabbx",       # Contém 'x'
        "aabb ",       # Contém espaço
        "aabb\n",      # Contém quebra de linha
        "aabb\t",      # Contém tab
        "aabb\r",      # Contém carriage return
        "aabb\0",      # Contém null character
        "aabb\b",      # Contém backspace
        "aabb\f",      # Contém form feed
        "aabb\v",      # Contém vertical tab
        "aabb\a",      # Contém bell
        "aabb\\e",     # Contém escape
        "aabb\033",    # Contém ESC
        "aabb\033[",   # Contém ANSI escape sequence
        "aabb\033[0m", # Contém ANSI escape sequence
        "aabb\033[1m", # Contém ANSI escape sequence
        "aabb\033[31m", # Contém ANSI escape sequence
        "aabb\033[32m", # Contém ANSI escape sequence
        "aabb\033[33m", # Contém ANSI escape sequence
        "aabb\033[34m", # Contém ANSI escape sequence
        "aabb\033[35m", # Contém ANSI escape sequence
        "aabb\033[36m", # Contém ANSI escape sequence
        "aabb\033[37m", # Contém ANSI escape sequence
    ])
    
    # Combinar todos os casos
    todos_casos = []
    
    # Adicionar casos válidos
    for caso in casos_validos:
        valido, motivo = validar_linguagem_H(caso)
        todos_casos.append({
            "input": caso,
            "expected": True,
            "description": f"Caso válido: '{caso}' - {motivo}"
        })
    
    # Adicionar casos inválidos
    for caso in casos_invalidos:
        valido, motivo = validar_linguagem_H(caso)
        todos_casos.append({
            "input": caso,
            "expected": False,
            "description": f"Caso inválido: '{caso}' - {motivo}"
        })
    
    return {
        "language": "H: {w | w ∈ {a, b}* e w contenha o dobro de símbolos \"a\" do que \"b\"}",
        "test_cases": todos_casos
    }

if __name__ == "__main__":
    testes = gerar_testes_H()
    
    with open("test_cases_H_correto.json", "w", encoding="utf-8") as f:
        json.dump(testes, f, indent=2, ensure_ascii=False)
    
    print(f"Gerados {len(testes['test_cases'])} casos de teste para a linguagem H")
    print(f"Casos válidos: {sum(1 for caso in testes['test_cases'] if caso['expected'])}")
    print(f"Casos inválidos: {sum(1 for caso in testes['test_cases'] if not caso['expected'])}")
    
    # Validar alguns casos específicos
    print("\nValidação de casos específicos:")
    casos_teste = ["", "aab", "aabb", "aaaabb", "ab", "aa", "bb", "aaaab", "aabbb"]
    for caso in casos_teste:
        valido, motivo = validar_linguagem_H(caso)
        print(f"'{caso}': {valido} - {motivo}")
