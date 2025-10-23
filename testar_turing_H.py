#!/usr/bin/env python3
"""
Teste completo da máquina de Turing H com casos de teste gerados
"""

import json
from analisar_turing_H import analisar_maquina_turing, simular_turing

def testar_maquina_completa():
    """Testa a máquina de Turing com todos os casos de teste"""
    
    # Carregar casos de teste
    with open('test_cases_H_correto.json', 'r', encoding='utf-8') as f:
        casos_teste = json.load(f)
    
    # Carregar máquina de Turing
    jff_file = "atividade turing/H linguagem_w_ab_estrela_dobro_a_que_b.jff"
    estados, estado_inicial, estados_finais, transicoes = analisar_maquina_turing(jff_file)
    
    print("=== TESTE COMPLETO DA MÁQUINA DE TURING H ===")
    print(f"Linguagem: {casos_teste['language']}")
    print(f"Total de casos de teste: {len(casos_teste['test_cases'])}")
    print()
    
    resultados = []
    corretos = 0
    incorretos = 0
    
    for i, caso in enumerate(casos_teste['test_cases']):
        entrada = caso['input']
        esperado = caso['expected']
        descricao = caso['description']
        
        # Simular máquina
        resultado, historico, motivo = simular_turing(entrada, estados, estado_inicial, estados_finais, transicoes)
        
        # Verificar se resultado está correto
        correto = (resultado == esperado)
        if correto:
            corretos += 1
        else:
            incorretos += 1
        
        resultados.append({
            'entrada': entrada,
            'esperado': esperado,
            'obtido': resultado,
            'correto': correto,
            'motivo': motivo,
            'passos': len(historico),
            'descricao': descricao
        })
        
        # Mostrar resultado
        status = "✅" if correto else "❌"
        entrada_str = f"'{entrada}'" if entrada else "(vazio)"
        esperado_str = "ACEITA" if esperado else "REJEITA"
        obtido_str = "ACEITA" if resultado else "REJEITA"
        
        print(f"{status} {entrada_str:20} | Esperado: {esperado_str:7} | Obtido: {obtido_str:7} | Passos: {len(historico):3} | {descricao}")
        
        # Mostrar detalhes dos casos incorretos
        if not correto:
            print(f"    Motivo: {motivo}")
            if len(historico) <= 10:
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
    
    print()
    print("=== RESUMO DOS RESULTADOS ===")
    print(f"Total de casos: {len(casos_teste['test_cases'])}")
    print(f"Corretos: {corretos}")
    print(f"Incorretos: {incorretos}")
    print(f"Taxa de acerto: {corretos/len(casos_teste['test_cases'])*100:.1f}%")
    
    # Análise dos casos incorretos
    if incorretos > 0:
        print()
        print("=== ANÁLISE DOS CASOS INCORRETOS ===")
        
        casos_incorretos = [r for r in resultados if not r['correto']]
        
        # Agrupar por tipo de erro
        erros_por_tipo = {}
        for caso in casos_incorretos:
            if caso['esperado'] and not caso['obtido']:
                tipo = "Falso negativo (deveria aceitar mas rejeitou)"
            elif not caso['esperado'] and caso['obtido']:
                tipo = "Falso positivo (deveria rejeitar mas aceitou)"
            else:
                tipo = "Outro erro"
            
            if tipo not in erros_por_tipo:
                erros_por_tipo[tipo] = []
            erros_por_tipo[tipo].append(caso)
        
        for tipo, casos in erros_por_tipo.items():
            print(f"\n{tipo}: {len(casos)} casos")
            for caso in casos[:5]:  # Mostrar apenas os primeiros 5
                entrada_str = f"'{caso['entrada']}'" if caso['entrada'] else "(vazio)"
                print(f"  - {entrada_str}: {caso['descricao']}")
            if len(casos) > 5:
                print(f"  ... e mais {len(casos) - 5} casos")
    
    return resultados

def analisar_problemas_especificos():
    """Analisa problemas específicos da máquina"""
    
    print("\n=== ANÁLISE DE PROBLEMAS ESPECÍFICOS ===")
    
    # Carregar máquina
    jff_file = "atividade turing/H linguagem_w_ab_estrela_dobro_a_que_b.jff"
    estados, estado_inicial, estados_finais, transicoes = analisar_maquina_turing(jff_file)
    
    # Casos problemáticos identificados
    casos_problematicos = [
        ("aba", "2 a's, 1 b - deveria aceitar"),
        ("baa", "2 a's, 1 b - deveria aceitar"),
        ("aabbaa", "4 a's, 2 b's - deveria aceitar"),
        ("aa", "2 a's, 0 b's - deveria rejeitar"),
    ]
    
    for entrada, descricao in casos_problematicos:
        print(f"\nAnalisando: '{entrada}' - {descricao}")
        resultado, historico, motivo = simular_turing(entrada, estados, estado_inicial, estados_finais, transicoes, max_steps=50)
        
        print(f"Resultado: {'ACEITA' if resultado else 'REJEITA'}")
        print(f"Motivo: {motivo}")
        print(f"Passos: {len(historico)}")
        
        # Mostrar execução detalhada
        print("Execução detalhada:")
        for h in historico:
            fita_vis = h['fita'][:h['cursor_pos']] + '|' + h['fita'][h['cursor_pos']:]
            print(f"  {h['passo']}: {h['nome_estado']} - {fita_vis}")

if __name__ == "__main__":
    resultados = testar_maquina_completa()
    analisar_problemas_especificos()
