"""
Script CLI para validar e corrigir Máquinas de Turing

Uso:
    python validate_turing.py test <arquivo.jff> <entrada>
    python validate_turing.py validate <arquivo.jff> --tests testes.json
    python validate_turing.py auto-fix <arquivo.jff> --language "{ a^n b^m c^(2n) d^m }"
    python validate_turing.py batch <pasta> --tests testes.json
"""
import argparse
import json
import sys
import os
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from turing_validator import (
    simulate_turing,
    validate_machine,
    analyze_machine,
    generate_test_cases_with_ai,
    auto_fix_machine_with_ai,
    format_test_results
)


def cmd_test(args):
    """Testar uma única entrada"""
    jff_file = Path(args.jff_file)
    
    if not jff_file.exists():
        print(f"Erro: Arquivo não encontrado: {jff_file}")
        sys.exit(1)
    
    jff_content = jff_file.read_text(encoding='utf-8')
    
    print("="*70)
    print(f"TESTANDO: {jff_file.name}")
    print(f"ENTRADA: {args.input}")
    print("="*70)
    
    result = simulate_turing(jff_content, args.input, args.max_steps)
    
    if result.get('error'):
        print(f"\n[!] ERRO: {result['error']}")
    
    print(f"\nRESULTADO: {'ACEITO' if result.get('accepted') else 'REJEITADO'}")
    print(f"PASSOS: {result['steps']}")
    
    if result.get('final_state'):
        print(f"ESTADO FINAL: {result['final_state']}")
    
    if args.verbose and result.get('execution_log'):
        print("\n--- LOG DE EXECUÇÃO ---")
        for log in result['execution_log'][:50]:  # Mostrar primeiros 50 passos
            print(f"Passo {log['step']}: {log['from_state']} -> {log['to_state']} | "
                  f"Leu: '{log['read']}' -> Escreveu: '{log['write']}' | Move: {log['move']}")
    
    sys.exit(0 if result.get('accepted') else 1)


def cmd_validate(args):
    """Validar com casos de teste"""
    jff_file = Path(args.jff_file)
    
    if not jff_file.exists():
        print(f"Erro: Arquivo não encontrado: {jff_file}")
        sys.exit(1)
    
    jff_content = jff_file.read_text(encoding='utf-8')
    
    # Carregar casos de teste
    if args.tests:
        tests_file = Path(args.tests)
        if not tests_file.exists():
            print(f"Erro: Arquivo de testes não encontrado: {tests_file}")
            sys.exit(1)
        
        with open(tests_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            test_cases = data.get('test_cases', [])
    elif args.language:
        # Gerar casos de teste com IA
        print(f"Gerando casos de teste para: {args.language}")
        test_cases = generate_test_cases_with_ai(args.language, 5, 5)
        
        if not test_cases:
            print("Erro: Não foi possível gerar casos de teste")
            sys.exit(1)
        
        print(f"Gerados {len(test_cases)} casos de teste")
    else:
        print("Erro: Especifique --tests ou --language")
        sys.exit(1)
    
    print("="*70)
    print(f"VALIDANDO: {jff_file.name}")
    print(f"CASOS DE TESTE: {len(test_cases)}")
    print("="*70)
    
    results = validate_machine(jff_content, test_cases)
    
    print(format_test_results(results))
    
    # Salvar relatório se solicitado
    if args.output:
        output_file = Path(args.output)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nRelatório salvo em: {output_file}")
    
    sys.exit(0 if results['is_valid'] else 1)


def cmd_analyze(args):
    """Analisar máquina"""
    jff_file = Path(args.jff_file)
    
    if not jff_file.exists():
        print(f"Erro: Arquivo não encontrado: {jff_file}")
        sys.exit(1)
    
    jff_content = jff_file.read_text(encoding='utf-8')
    
    print("="*70)
    print(f"ANALISANDO: {jff_file.name}")
    print("="*70)
    
    analysis = analyze_machine(jff_content, args.language or '')
    
    if 'error' in analysis:
        print(f"\nErro: {analysis['error']}")
        sys.exit(1)
    
    structure = analysis.get('machine_structure', {})
    print(f"\nESTRUTURA:")
    print(f"  Estados: {structure.get('num_states', 0)}")
    print(f"  Transições: {structure.get('num_transitions', 0)}")
    print(f"  Estado inicial: {structure.get('initial_state', 'N/A')}")
    print(f"  Estados finais: {', '.join(structure.get('final_states', []))}")
    
    issues = analysis.get('issues', [])
    
    if issues:
        print(f"\n PROBLEMAS ENCONTRADOS: {len(issues)}")
        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. [{issue['severity']}] {issue['type']}")
            print(f"   Estado: {issue.get('state', 'N/A')}")
            print(f"   Mensagem: {issue['message']}")
            print(f"   Sugestão: {issue['suggestion']}")
    else:
        print("\n Nenhum problema detectado!")
    
    sys.exit(0 if not issues else 1)


def cmd_auto_fix(args):
    """Corrigir automaticamente"""
    jff_file = Path(args.jff_file)
    
    if not jff_file.exists():
        print(f"Erro: Arquivo não encontrado: {jff_file}")
        sys.exit(1)
    
    if not args.language:
        print("Erro: Especifique --language para correção automática")
        sys.exit(1)
    
    jff_content = jff_file.read_text(encoding='utf-8')
    
    print("="*70)
    print(f"CORRIGINDO: {jff_file.name}")
    print(f"LINGUAGEM: {args.language}")
    print("="*70)
    
    # Gerar ou carregar casos de teste
    if args.tests:
        tests_file = Path(args.tests)
        with open(tests_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            test_cases = data.get('test_cases', [])
    else:
        print("\nGerando casos de teste...")
        test_cases = generate_test_cases_with_ai(args.language, 5, 5)
    
    # Validar máquina atual
    print("\nValidando máquina atual...")
    validation = validate_machine(jff_content, test_cases)
    
    if validation['is_valid']:
        print("\n Máquina já está válida!")
        sys.exit(0)
    
    print(f"\n Falhou {validation['failed']} de {validation['total_tests']} testes")
    
    # Obter testes que falharam
    failed_tests = [r for r in validation['results'] if r['status'] == 'FAIL']
    
    # Tentar correção com IA
    print("\nSolicitando correções à IA...")
    corrections = auto_fix_machine_with_ai(jff_content, args.language, failed_tests)
    
    if corrections:
        print("\n CORREÇÕES SUGERIDAS:")
        print(json.dumps(corrections, ensure_ascii=False, indent=2))
        
        if args.output:
            output_file = Path(args.output)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(corrections, f, ensure_ascii=False, indent=2)
            print(f"\nCorreções salvas em: {output_file}")
    else:
        print("\n Não foi possível gerar correções automaticamente")
        sys.exit(1)


def cmd_batch(args):
    """Testar múltiplos arquivos"""
    folder = Path(args.folder)
    
    if not folder.exists():
        print(f"Erro: Pasta não encontrada: {folder}")
        sys.exit(1)
    
    # Buscar arquivos .jff
    jff_files = list(folder.glob('*.jff'))
    
    if not jff_files:
        print(f"Erro: Nenhum arquivo .jff encontrado em: {folder}")
        sys.exit(1)
    
    # Carregar casos de teste
    if args.tests:
        tests_file = Path(args.tests)
        with open(tests_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            test_cases = data.get('test_cases', [])
    else:
        print("Erro: Especifique --tests para teste em lote")
        sys.exit(1)
    
    print("="*70)
    print(f"TESTE EM LOTE: {folder}")
    print(f"ARQUIVOS: {len(jff_files)}")
    print(f"CASOS DE TESTE: {len(test_cases)}")
    print("="*70)
    
    results = []
    valid_count = 0
    
    for jff_file in jff_files:
        print(f"\nTestando: {jff_file.name}...", end=' ')
        
        jff_content = jff_file.read_text(encoding='utf-8')
        validation = validate_machine(jff_content, test_cases)
        
        is_valid = validation['is_valid']
        
        if is_valid:
            print("✓ VÁLIDA")
            valid_count += 1
        else:
            print(f"✗ INVÁLIDA ({validation['failed']} falhas)")
        
        results.append({
            'file': jff_file.name,
            'validation': validation
        })
    
    print("\n" + "="*70)
    print(f"RESUMO: {valid_count}/{len(jff_files)} válidas")
    print("="*70)
    
    # Salvar relatório
    if args.output:
        output_file = Path(args.output)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_files': len(jff_files),
                'valid': valid_count,
                'invalid': len(jff_files) - valid_count,
                'results': results
            }, f, ensure_ascii=False, indent=2)
        print(f"\nRelatório salvo em: {output_file}")
    
    sys.exit(0 if valid_count == len(jff_files) else 1)


def main():
    parser = argparse.ArgumentParser(
        description='Validador e Corretor de Máquinas de Turing',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comando a executar')
    
    # Comando: test
    test_parser = subparsers.add_parser('test', help='Testar uma entrada')
    test_parser.add_argument('jff_file', help='Arquivo JFF')
    test_parser.add_argument('input', help='Entrada para testar')
    test_parser.add_argument('--max-steps', type=int, default=10000, help='Máximo de passos')
    test_parser.add_argument('-v', '--verbose', action='store_true', help='Mostrar log de execução')
    
    # Comando: validate
    validate_parser = subparsers.add_parser('validate', help='Validar com casos de teste')
    validate_parser.add_argument('jff_file', help='Arquivo JFF')
    validate_parser.add_argument('--tests', help='Arquivo JSON com casos de teste')
    validate_parser.add_argument('--language', help='Descrição da linguagem (gera testes com IA)')
    validate_parser.add_argument('-o', '--output', help='Arquivo de saída para relatório')
    
    # Comando: analyze
    analyze_parser = subparsers.add_parser('analyze', help='Analisar máquina')
    analyze_parser.add_argument('jff_file', help='Arquivo JFF')
    analyze_parser.add_argument('--language', help='Descrição da linguagem')
    
    # Comando: auto-fix
    fix_parser = subparsers.add_parser('auto-fix', help='Corrigir automaticamente')
    fix_parser.add_argument('jff_file', help='Arquivo JFF')
    fix_parser.add_argument('--language', required=True, help='Descrição da linguagem')
    fix_parser.add_argument('--tests', help='Arquivo JSON com casos de teste')
    fix_parser.add_argument('-o', '--output', help='Arquivo de saída para correções')
    
    # Comando: batch
    batch_parser = subparsers.add_parser('batch', help='Testar múltiplos arquivos')
    batch_parser.add_argument('folder', help='Pasta com arquivos JFF')
    batch_parser.add_argument('--tests', required=True, help='Arquivo JSON com casos de teste')
    batch_parser.add_argument('-o', '--output', help='Arquivo de saída para relatório')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Executar comando
    if args.command == 'test':
        cmd_test(args)
    elif args.command == 'validate':
        cmd_validate(args)
    elif args.command == 'analyze':
        cmd_analyze(args)
    elif args.command == 'auto-fix':
        cmd_auto_fix(args)
    elif args.command == 'batch':
        cmd_batch(args)


if __name__ == '__main__':
    main()

