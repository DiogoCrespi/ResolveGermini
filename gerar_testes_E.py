#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

def gerar_testes_linguagem_E():
    """
    Gera casos de teste para a linguagem E: { a^i b^j a^i b^j | i, j > 0 }
    
    A linguagem aceita strings da forma:
    - Bloco 1: a^i (i > 0)
    - Bloco 2: b^j (j > 0) 
    - Bloco 3: a^i (mesmo número de a's do bloco 1)
    - Bloco 4: b^j (mesmo número de b's do bloco 2)
    """
    
    test_cases = []
    
    # Casos válidos - devem ser ACEITOS
    casos_validos = [
        # Casos básicos
        ("abab", "Caso básico: i=1, j=1"),
        ("aabb", "Caso básico: i=2, j=1"),
        ("abba", "Caso básico: i=1, j=2"),
        ("aabbaa", "Caso básico: i=2, j=2"),
        
        # Casos com mais a's
        ("aaabaa", "i=3, j=1"),
        ("aaaabaaa", "i=4, j=1"),
        ("aaabbaaa", "i=3, j=2"),
        ("aaaabbaaaa", "i=4, j=2"),
        
        # Casos com mais b's
        ("abbbabbb", "i=1, j=3"),
        ("abbbbabb", "i=1, j=4"),
        ("aabbbaa", "i=2, j=3"),
        ("aabbbbaa", "i=2, j=4"),
        
        # Casos com a's e b's maiores
        ("aaabbbaaabbb", "i=3, j=3"),
        ("aaaabbbbaaaabbbb", "i=4, j=4"),
        ("aaaaabbbbbaaaaabbbbb", "i=5, j=5"),
    ]
    
    # Casos inválidos - devem ser REJEITADOS
    casos_invalidos = [
        # Strings vazias ou muito curtas
        ("", "String vazia"),
        ("a", "Apenas um 'a'"),
        ("b", "Apenas um 'b'"),
        ("ab", "Apenas 'ab'"),
        
        # Números incorretos de a's
        ("abaa", "i=1, j=1, mas 2o bloco tem 2 a's"),
        ("aabaa", "i=2, j=1, mas 2o bloco tem 2 a's"),
        ("aaabaa", "i=3, j=1, mas 2o bloco tem 2 a's"),
        ("aabbaa", "i=2, j=2, mas 2o bloco tem 2 a's"),
        ("aaaabbaa", "i=4, j=2, mas 2o bloco tem 2 a's"),
        
        # Números incorretos de b's
        ("abbb", "i=1, j=1, mas 2o bloco tem 3 b's"),
        ("aabbb", "i=2, j=1, mas 2o bloco tem 3 b's"),
        ("abba", "i=1, j=2, mas 2o bloco tem 1 b"),
        ("aabbba", "i=2, j=3, mas 2o bloco tem 1 b"),
        
        # Ordem incorreta
        ("baab", "Começa com 'b'"),
        ("ababab", "i=1, j=1, mas tem 3 blocos de 'ab'"),
        ("aabab", "i=2, j=1, mas estrutura incorreta"),
        ("ababb", "i=1, j=2, mas estrutura incorreta"),
        
        # Caracteres inválidos
        ("acac", "Contém 'c'"),
        ("ababx", "Contém 'x'"),
        ("a1b1", "Contém números"),
        
        # Casos especiais
        ("aaaa", "Apenas a's"),
        ("bbbb", "Apenas b's"),
        ("abababab", "Múltiplos blocos 'ab'"),
        ("aabbaabb", "Dois blocos completos"),
    ]
    
    # Adicionar casos válidos
    for string, descricao in casos_validos:
        test_cases.append({
            "input": string,
            "expected": True,
            "reason": descricao
        })
    
    # Adicionar casos inválidos
    for string, descricao in casos_invalidos:
        test_cases.append({
            "input": string,
            "expected": False,
            "reason": descricao
        })
    
    return test_cases

def main():
    print("Gerando casos de teste para linguagem E: { a^i b^j a^i b^j | i, j > 0 }")
    
    test_cases = gerar_testes_linguagem_E()
    
    # Salvar em arquivo JSON
    output_data = {
        "language": "{ a^i b^j a^i b^j | i, j > 0 }",
        "test_cases": test_cases
    }
    
    with open("test_cases_E_correto.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Gerados {len(test_cases)} casos de teste")
    print(f"Casos salvos em: test_cases_E_correto.json")
    
    # Mostrar alguns exemplos
    print("\nExemplos de casos gerados:")
    for i, case in enumerate(test_cases[:10]):
        status = "ACCEPT" if case['expected'] else "REJECT"
        print(f"{i+1:2d}. '{case['input']}' -> {status:7s} ({case['reason']})")

if __name__ == "__main__":
    main()
