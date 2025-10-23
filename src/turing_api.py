"""
API REST para Validação e Correção de Máquinas de Turing

Instalação:
    pip install flask flask-cors

Uso:
    python src/turing_api.py
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from turing_validator import (
    simulate_turing,
    validate_machine,
    analyze_machine,
    generate_test_cases_with_ai,
    auto_fix_machine_with_ai
)

app = Flask(__name__)
CORS(app)  # Permitir CORS para acesso do frontend


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'service': 'Turing Validator API'})


@app.route('/api/turing/test', methods=['POST'])
def test_turing():
    """
    Testa uma entrada em uma Máquina de Turing
    
    Body:
    {
        "jff_content": "<structure>...</structure>",
        "input": "abccd",
        "max_steps": 10000
    }
    """
    data = request.get_json()
    
    if not data or 'jff_content' not in data or 'input' not in data:
        return jsonify({'error': 'Campos obrigatórios: jff_content, input'}), 400
    
    jff_content = data['jff_content']
    input_str = data['input']
    max_steps = data.get('max_steps', 10000)
    
    result = simulate_turing(jff_content, input_str, max_steps)
    
    return jsonify(result)


@app.route('/api/turing/validate', methods=['POST'])
def validate():
    """
    Valida uma Máquina de Turing contra casos de teste
    
    Body:
    {
        "jff_content": "<structure>...</structure>",
        "test_cases": [
            {"input": "abccd", "expected": true},
            {"input": "abccdd", "expected": false}
        ]
    }
    """
    data = request.get_json()
    
    if not data or 'jff_content' not in data or 'test_cases' not in data:
        return jsonify({'error': 'Campos obrigatórios: jff_content, test_cases'}), 400
    
    jff_content = data['jff_content']
    test_cases = data['test_cases']
    
    results = validate_machine(jff_content, test_cases)
    
    return jsonify(results)


@app.route('/api/turing/analyze', methods=['POST'])
def analyze():
    """
    Analisa uma Máquina de Turing e identifica problemas
    
    Body:
    {
        "jff_content": "<structure>...</structure>",
        "language_description": "{ a^n b^m c^(2n) d^m | n > 0 e m > 0 }"
    }
    """
    data = request.get_json()
    
    if not data or 'jff_content' not in data:
        return jsonify({'error': 'Campo obrigatório: jff_content'}), 400
    
    jff_content = data['jff_content']
    language_desc = data.get('language_description', '')
    
    analysis = analyze_machine(jff_content, language_desc)
    
    return jsonify(analysis)


@app.route('/api/turing/generate-tests', methods=['POST'])
def generate_tests():
    """
    Gera casos de teste baseado na descrição da linguagem usando IA
    
    Body:
    {
        "language_description": "{ a^n b^m c^(2n) d^m | n > 0 e m > 0 }",
        "num_positive": 5,
        "num_negative": 5
    }
    """
    data = request.get_json()
    
    if not data or 'language_description' not in data:
        return jsonify({'error': 'Campo obrigatório: language_description'}), 400
    
    language_desc = data['language_description']
    num_positive = data.get('num_positive', 5)
    num_negative = data.get('num_negative', 5)
    
    test_cases = generate_test_cases_with_ai(language_desc, num_positive, num_negative)
    
    return jsonify({'test_cases': test_cases})


@app.route('/api/turing/auto-fix', methods=['POST'])
def auto_fix():
    """
    Corrige automaticamente problemas identificados usando IA
    
    Body:
    {
        "jff_content": "<structure>...</structure>",
        "language_description": "{ a^n b^m c^(2n) d^m | n > 0 e m > 0 }",
        "test_cases": [
            {"input": "abccd", "expected": true},
            {"input": "abbccdd", "expected": true}
        ]
    }
    """
    data = request.get_json()
    
    if not data or 'jff_content' not in data or 'test_cases' not in data:
        return jsonify({'error': 'Campos obrigatórios: jff_content, test_cases'}), 400
    
    jff_content = data['jff_content']
    language_desc = data.get('language_description', '')
    test_cases = data['test_cases']
    
    # 1. Validar máquina atual
    validation = validate_machine(jff_content, test_cases)
    
    if validation['is_valid']:
        return jsonify({
            'fixed': False,
            'message': 'Máquina já está válida',
            'validation': validation
        })
    
    # 2. Obter testes que falharam
    failed_tests = [r for r in validation['results'] if r['status'] == 'FAIL']
    
    # 3. Tentar correção com IA
    corrections = auto_fix_machine_with_ai(jff_content, language_desc, failed_tests)
    
    if corrections is None:
        return jsonify({
            'fixed': False,
            'error': 'Não foi possível gerar correções automaticamente',
            'validation': validation
        }), 500
    
    return jsonify({
        'fixed': True,
        'corrections': corrections,
        'original_validation': validation,
        'message': 'Correções sugeridas pela IA. Aplique manualmente ou use o endpoint /apply-corrections'
    })


@app.route('/api/turing/batch-test', methods=['POST'])
def batch_test():
    """
    Testa múltiplos arquivos JFF
    
    Body:
    {
        "files": [
            {"name": "Q1a.jff", "content": "<structure>...</structure>"},
            {"name": "Q1b.jff", "content": "<structure>...</structure>"}
        ],
        "test_cases": [
            {"input": "abccd", "expected": true}
        ]
    }
    """
    data = request.get_json()
    
    if not data or 'files' not in data or 'test_cases' not in data:
        return jsonify({'error': 'Campos obrigatórios: files, test_cases'}), 400
    
    files = data['files']
    test_cases = data['test_cases']
    
    results = []
    
    for file_data in files:
        file_name = file_data.get('name', 'unknown')
        jff_content = file_data.get('content', '')
        
        validation = validate_machine(jff_content, test_cases)
        
        results.append({
            'file': file_name,
            'validation': validation
        })
    
    total_valid = sum(1 for r in results if r['validation']['is_valid'])
    
    return jsonify({
        'total_files': len(files),
        'valid': total_valid,
        'invalid': len(files) - total_valid,
        'results': results
    })


if __name__ == '__main__':
    print("="*70)
    print("API de Validação de Máquinas de Turing")
    print("="*70)
    print("Endpoints disponíveis:")
    print("  GET  /api/health              - Health check")
    print("  POST /api/turing/test         - Testar entrada")
    print("  POST /api/turing/validate     - Validar com casos de teste")
    print("  POST /api/turing/analyze      - Analisar máquina")
    print("  POST /api/turing/generate-tests - Gerar casos de teste (IA)")
    print("  POST /api/turing/auto-fix     - Corrigir automaticamente (IA)")
    print("  POST /api/turing/batch-test   - Testar múltiplos arquivos")
    print("="*70)
    print("Servidor rodando em: http://localhost:5000")
    print("="*70)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

