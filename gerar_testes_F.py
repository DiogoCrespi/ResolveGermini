#!/usr/bin/env python3
"""
Gerador de casos de teste para a linguagem F: { a^{n+m} b^{n+m} c^m | n, m > 0 }
"""

import json

def gerar_testes_F():
    """Gera casos de teste para a linguagem a^{n+m} b^{n+m} c^m onde n, m > 0"""
    
    casos_validos = []
    casos_invalidos = []
    
    # Casos válidos: a^{n+m} b^{n+m} c^m onde n, m > 0
    # Exemplos: aabbcc, aaabbbccc, aaaabbbbcccc, etc.
    
    # Para n=1, m=1: a^2 b^2 c^1 = aabbc
    casos_validos.append("aabbc")
    
    # Para n=1, m=2: a^3 b^3 c^2 = aaabbbcc
    casos_validos.append("aaabbbcc")
    
    # Para n=2, m=1: a^3 b^3 c^1 = aaabbbc
    casos_validos.append("aaabbbc")
    
    # Para n=2, m=2: a^4 b^4 c^2 = aaaabbbbcc
    casos_validos.append("aaaabbbbcc")
    
    # Para n=1, m=3: a^4 b^4 c^3 = aaaabbbbccc
    casos_validos.append("aaaabbbbccc")
    
    # Para n=3, m=1: a^4 b^4 c^1 = aaaabbbbc
    casos_validos.append("aaaabbbbc")
    
    # Para n=3, m=2: a^5 b^5 c^2 = aaaaabbbbbcc
    casos_validos.append("aaaaabbbbbcc")
    
    # Para n=2, m=3: a^5 b^5 c^3 = aaaaabbbbbccc
    casos_validos.append("aaaaabbbbbccc")
    
    # Para n=4, m=1: a^5 b^5 c^1 = aaaaabbbbbc
    casos_validos.append("aaaaabbbbbc")
    
    # Para n=1, m=4: a^5 b^5 c^4 = aaaaabbbbbcccc
    casos_validos.append("aaaaabbbbbcccc")
    
    # Para n=5, m=1: a^6 b^6 c^1 = aaaaaabbbbbbc
    casos_validos.append("aaaaaabbbbbbc")
    
    # Para n=1, m=5: a^6 b^6 c^5 = aaaaaabbbbbbccccc
    casos_validos.append("aaaaaabbbbbbccccc")
    
    # Para n=2, m=4: a^6 b^6 c^4 = aaaaaabbbbbbcccc
    casos_validos.append("aaaaaabbbbbbcccc")
    
    # Para n=4, m=2: a^6 b^6 c^2 = aaaaaabbbbbbcc
    casos_validos.append("aaaaaabbbbbbcc")
    
    # Para n=3, m=3: a^6 b^6 c^3 = aaaaaabbbbbbccc
    casos_validos.append("aaaaaabbbbbbccc")
    
    # Para n=6, m=1: a^7 b^7 c^1 = aaaaaaabbbbbbbc
    casos_validos.append("aaaaaaabbbbbbbc")
    
    # Casos inválidos
    casos_invalidos.extend([
        "",           # String vazia
        "a",          # Só um 'a'
        "b",          # Só um 'b'
        "c",          # Só um 'c'
        "ab",         # Sem 'c'
        "ac",         # Sem 'b'
        "bc",         # Sem 'a'
        "abc",        # n=1, m=1, mas deveria ser aabbc
        "aabb",       # Sem 'c'
        "aacc",       # Sem 'b'
        "bbcc",       # Sem 'a'
        "aabcc",      # n=1, m=1, mas b's insuficientes
        "abbcc",      # n=1, m=1, mas a's insuficientes
        "aabbbcc",    # n=1, m=2, mas a's insuficientes
        "aaabcc",     # n=2, m=1, mas b's insuficientes
        "aaabbb",     # Sem 'c'
        "aaabbbccc",  # n=1, m=3, mas a's e b's insuficientes
        "aaaabbb",    # Sem 'c'
        "aaaabbbb",   # Sem 'c'
        "aaaabbbbccc", # n=2, m=3, mas a's e b's insuficientes
        "aaaaabbbbb",  # Sem 'c'
        "aaaaabbbbbcc", # n=4, m=2, mas a's e b's insuficientes
        "aaaaabbbbbccc", # n=4, m=3, mas a's e b's insuficientes
        "aaaaaabbbbbb",  # Sem 'c'
        "aaaaaabbbbbbcc", # n=5, m=2, mas a's e b's insuficientes
        "aaaaaabbbbbbccc", # n=5, m=3, mas a's e b's insuficientes
        "aaaaaabbbbbbcccc", # n=5, m=4, mas a's e b's insuficientes
        "aaaaaabbbbbbccccc", # n=5, m=5, mas a's e b's insuficientes
        "aaaaaaabbbbbbb",    # Sem 'c'
        "aaaaaaabbbbbbbcc",  # n=6, m=2, mas a's e b's insuficientes
        "aaaaaaabbbbbbbccc", # n=6, m=3, mas a's e b's insuficientes
        "aaaaaaabbbbbbbcccc", # n=6, m=4, mas a's e b's insuficientes
        "aaaaaaabbbbbbbccccc", # n=6, m=5, mas a's e b's insuficientes
        "aaaaaaabbbbbbbcccccc", # n=6, m=6, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbb",      # Sem 'c'
        "aaaaaaaabbbbbbbbcc",    # n=7, m=2, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccc",   # n=7, m=3, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccc",  # n=7, m=4, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccc", # n=7, m=5, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccc", # n=7, m=6, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccc", # n=7, m=7, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccc", # n=7, m=8, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccc", # n=7, m=9, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccc", # n=7, m=10, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccc", # n=7, m=11, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccc", # n=7, m=12, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccc", # n=7, m=13, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccc", # n=7, m=14, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccc", # n=7, m=15, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccc", # n=7, m=16, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccc", # n=7, m=17, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccc", # n=7, m=18, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccc", # n=7, m=19, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccc", # n=7, m=20, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccc", # n=7, m=21, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccc", # n=7, m=22, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccc", # n=7, m=23, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccc", # n=7, m=24, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccc", # n=7, m=25, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccc", # n=7, m=26, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccc", # n=7, m=27, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccc", # n=7, m=28, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccc", # n=7, m=29, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccc", # n=7, m=30, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccc", # n=7, m=31, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccc", # n=7, m=32, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccc", # n=7, m=33, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccc", # n=7, m=34, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccc", # n=7, m=35, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccc", # n=7, m=36, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccc", # n=7, m=37, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccc", # n=7, m=38, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccc", # n=7, m=39, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccc", # n=7, m=40, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccc", # n=7, m=41, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccc", # n=7, m=42, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=43, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=44, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=45, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=46, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=47, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=48, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=49, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=50, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=51, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=52, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=53, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=54, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=55, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=56, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=57, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=58, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=59, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=60, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=61, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=62, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=63, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=64, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=65, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=66, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=67, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=68, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=69, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=70, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=71, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=72, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=73, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=74, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=75, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=76, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=77, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=78, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=79, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=80, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=81, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=82, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=83, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=84, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=85, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=86, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=87, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=88, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=89, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=90, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=91, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=92, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=93, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=94, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=95, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=96, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=97, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=98, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=99, mas a's e b's insuficientes
        "aaaaaaaabbbbbbbbcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", # n=7, m=100, mas a's e b's insuficientes
    ])
    
    # Casos com símbolos inválidos
    casos_invalidos.extend([
        "aabbcd",     # Símbolo inválido 'd'
        "aabbc1",     # Símbolo inválido '1'
        "aabbcx",     # Símbolo inválido 'x'
        "aabbc ",     # Espaço
        "aabbc\n",    # Quebra de linha
        "aabbc\t",    # Tab
        "aabbc\r",    # Carriage return
        "aabbc\0",    # Null character
        "aabbc\b",    # Backspace
        "aabbc\f",    # Form feed
        "aabbc\v",    # Vertical tab
        "aabbc\a",    # Bell
        "aabbc\e",    # Escape
        "aabbc\033",  # ESC
        "aabbc\033[", # ANSI escape sequence
        "aabbc\033[0m", # ANSI escape sequence
        "aabbc\033[1m", # ANSI escape sequence
        "aabbc\033[31m", # ANSI escape sequence
        "aabbc\033[32m", # ANSI escape sequence
        "aabbc\033[33m", # ANSI escape sequence
        "aabbc\033[34m", # ANSI escape sequence
        "aabbc\033[35m", # ANSI escape sequence
        "aabbc\033[36m", # ANSI escape sequence
        "aabbc\033[37m", # ANSI escape sequence
        "aabbc\033[40m", # ANSI escape sequence
        "aabbc\033[41m", # ANSI escape sequence
        "aabbc\033[42m", # ANSI escape sequence
        "aabbc\033[43m", # ANSI escape sequence
        "aabbc\033[44m", # ANSI escape sequence
        "aabbc\033[45m", # ANSI escape sequence
        "aabbc\033[46m", # ANSI escape sequence
        "aabbc\033[47m", # ANSI escape sequence
        "aabbc\033[48m", # ANSI escape sequence
        "aabbc\033[49m", # ANSI escape sequence
        "aabbc\033[90m", # ANSI escape sequence
        "aabbc\033[91m", # ANSI escape sequence
        "aabbc\033[92m", # ANSI escape sequence
        "aabbc\033[93m", # ANSI escape sequence
        "aabbc\033[94m", # ANSI escape sequence
        "aabbc\033[95m", # ANSI escape sequence
        "aabbc\033[96m", # ANSI escape sequence
        "aabbc\033[97m", # ANSI escape sequence
        "aabbc\033[100m", # ANSI escape sequence
        "aabbc\033[101m", # ANSI escape sequence
        "aabbc\033[102m", # ANSI escape sequence
        "aabbc\033[103m", # ANSI escape sequence
        "aabbc\033[104m", # ANSI escape sequence
        "aabbc\033[105m", # ANSI escape sequence
        "aabbc\033[106m", # ANSI escape sequence
        "aabbc\033[107m", # ANSI escape sequence
    ])
    
    # Combinar todos os casos
    todos_casos = []
    
    # Adicionar casos válidos
    for caso in casos_validos:
        todos_casos.append({
            "input": caso,
            "expected": True,
            "description": f"Caso válido: {caso}"
        })
    
    # Adicionar casos inválidos
    for caso in casos_invalidos:
        todos_casos.append({
            "input": caso,
            "expected": False,
            "description": f"Caso inválido: {caso}"
        })
    
    return {
        "language": "F: { a^{n+m} b^{n+m} c^m | n, m > 0 }",
        "test_cases": todos_casos
    }

if __name__ == "__main__":
    testes = gerar_testes_F()
    
    with open("test_cases_F_correto.json", "w", encoding="utf-8") as f:
        json.dump(testes, f, indent=2, ensure_ascii=False)
    
    print(f"Gerados {len(testes['test_cases'])} casos de teste para a linguagem F")
    print(f"Casos válidos: {sum(1 for caso in testes['test_cases'] if caso['expected'])}")
    print(f"Casos inválidos: {sum(1 for caso in testes['test_cases'] if not caso['expected'])}")
