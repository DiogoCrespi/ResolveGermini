#!/usr/bin/env python3
"""
Teste da máquina de Turing corrigida
"""

import json
from analisar_turing_H import analisar_maquina_turing, simular_turing

def testar_maquina_corrigida():
    """Testa a máquina de Turing corrigida"""
    
    # Carregar casos de teste
    with open('test_cases_H_correto.json', 'r', encoding='utf-8') as f:
        casos_teste = json.load(f)
    
    # Carregar máquina de Turing corrigida
    jff_file = "H_linguagem_funcionando.jff"
    estados, estado_inicial, estados_finais, transicoes = analisar_maquina_turing(jff_file)
    
    print("=== TESTE DA MÁQUINA DE TURING CORRIGIDA ===")
    print(f"Arquivo: {jff_file}")
    print(f"Linguagem: {casos_teste['language']}")
    print()
    
    # Testar casos específicos primeiro
    casos_especificos = [
        ("", "String vazia - deve aceitar"),
        ("aab", "2 a's, 1 b - deve aceitar"),
        ("aba", "2 a's, 1 b - deve aceitar"),
        ("baa", "2 a's, 1 b - deve aceitar"),
        ("aabb", "2 a's, 2 b's - deve rejeitar"),
        ("aaaabb", "4 a's, 2 b's - deve aceitar"),
        ("aabbaa", "4 a's, 2 b's - deve aceitar"),
        ("ab", "1 a, 1 b - deve rejeitar"),
        ("aa", "2 a's, 0 b's - deve rejeitar"),
        ("bb", "0 a's, 2 b's - deve rejeitar"),
    ]
    
    print("=== TESTES ESPECÍFICOS ===")
    corretos = 0
    incorretos = 0
    
    for entrada, descricao in casos_especificos:
        # Determinar resultado esperado
        if entrada == "":
            esperado = True  # String vazia aceita
        elif entrada in ["aab", "aba", "baa", "aaaabb", "aabbaa"]:
            esperado = True  # Casos válidos
        else:
            esperado = False  # Casos inválidos
        
        # Simular máquina
        resultado, historico, motivo = simular_turing(entrada, estados, estado_inicial, estados_finais, transicoes)
        
        # Verificar se resultado está correto
        correto = (resultado == esperado)
        if correto:
            corretos += 1
        else:
            incorretos += 1
        
        # Mostrar resultado
        status = "✅" if correto else "❌"
        entrada_str = f"'{entrada}'" if entrada else "(vazio)"
        esperado_str = "ACEITA" if esperado else "REJEITA"
        obtido_str = "ACEITA" if resultado else "REJEITA"
        
        print(f"{status} {entrada_str:10} | Esperado: {esperado_str:7} | Obtido: {obtido_str:7} | Passos: {len(historico):3} | {descricao}")
        
        # Mostrar detalhes dos casos incorretos
        if not correto:
            print(f"    Motivo: {motivo}")
            if len(historico) <= 15:
                print("    Execução:")
                for h in historico:
                    fita_vis = h['fita'][:h['cursor_pos']] + '|' + h['fita'][h['cursor_pos']:]
                    print(f"      {h['passo']}: {h['nome_estado']} - {fita_vis}")
            else:
                print("    Últimos passos:")
                for h in historico[-5:]:
                    fita_vis = h['fita'][:h['cursor_pos']] + '|' + h['fita'][h['cursor_pos']:]
                    print(f"      {h['passo']}: {h['nome_estado']} - {fita_vis}")
            print()
    
    print(f"\nResultados dos testes específicos:")
    print(f"Corretos: {corretos}")
    print(f"Incorretos: {incorretos}")
    print(f"Taxa de acerto: {corretos/(corretos+incorretos)*100:.1f}%")
    
    return corretos, incorretos

def testar_todos_casos():
    """Testa todos os casos de teste"""
    
    # Carregar casos de teste
    with open('test_cases_H_correto.json', 'r', encoding='utf-8') as f:
        casos_teste = json.load(f)
    
    # Carregar máquina de Turing corrigida
    jff_file = "H_linguagem_funcionando.jff"
    estados, estado_inicial, estados_finais, transicoes = analisar_maquina_turing(jff_file)
    
    print("\n=== TESTE COMPLETO ===")
    
    corretos = 0
    incorretos = 0
    
    for caso in casos_teste['test_cases']:
        entrada = caso['input']
        esperado = caso['expected']
        
        # Simular máquina
        resultado, historico, motivo = simular_turing(entrada, estados, estado_inicial, estados_finais, transicoes)
        
        # Verificar se resultado está correto
        correto = (resultado == esperado)
        if correto:
            corretos += 1
        else:
            incorretos += 1
    
    print(f"Total de casos: {len(casos_teste['test_cases'])}")
    print(f"Corretos: {corretos}")
    print(f"Incorretos: {incorretos}")
    print(f"Taxa de acerto: {corretos/len(casos_teste['test_cases'])*100:.1f}%")
    
    return corretos, incorretos

if __name__ == "__main__":
    testar_maquina_corrigida()
    testar_todos_casos()
