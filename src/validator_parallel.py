"""
Verificador paralelo que usa chave de backup para validar questões resolvidas.
Executa em background sem afetar o programa principal.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import requests
from dotenv import load_dotenv

load_dotenv()

from .config import GEMINI_API_KEY_BACKUP, GEMINI_MODEL, OUTPUT_DIR_DEFAULT
from .gemini_client import _make_api_call, _extract_json_from_text

# Usa chave de backup para não afetar o programa principal
VALIDATOR_API_KEY = GEMINI_API_KEY_BACKUP or os.getenv("GEMINI_API_KEY", "")

if not VALIDATOR_API_KEY:
    print("⚠️  Chave de backup não configurada. Validador desabilitado.")
    VALIDATOR_ENABLED = False
else:
    VALIDATOR_ENABLED = True

VALIDATOR_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

VALIDATOR_STATUS_FILE = "validator_status.json"
VALIDATOR_OUTPUT_SUBDIR = "validadas"

# Lock para operações de I/O thread-safe
io_lock = threading.Lock()

SYSTEM_PROMPT_VALIDATOR = (
    "[PERSONA E OBJETIVO]\n"
    "Você é um especialista em Linguagens Formais e Teoria da Computação focado em validação rigorosa de respostas."
    "Seu objetivo é validar se as respostas fornecidas estão CORRETAS ou ERRADAS.\n\n"
    
    "[FORMATO DE RESPOSTA]\n"
    "Retorne EM JSON VÁLIDO: {\n"
    '  "questoes": [\n'
    '    {\n'
    '      "id": "Q1",\n'
    '      "correto": true,  // true se CORRETO, false se ERRADO\n'
    '      "observacao": "Breve observação se houver",\n'
    '      "resposta_correta": "Solução correta completa se correto=false"\n'
    '    }\n'
    '  ]\n'
    "}\n\n"
    
    "REGRAS:\n"
    "- SEM TEXTO fora do JSON\n"
    "- Se correto=true: não precisa de observacao nem resposta_correta\n"
    "- Se correto=false: OBRIGATÓRIO fornecer resposta_correta completa com a solução correta\n"
    "- Para gramáticas: valide se gera exatamente a linguagem pedida\n"
    "- Para autômatos: valide se reconhece exatamente a linguagem pedida\n"
    "- Para conversões: valide se o procedimento está correto\n"
    "- Para derivaciones/CYK: valide se está correta\n"
    "- Para bombeamento: valide se a prova está correta\n\n"
    
    "SEJA RIGOROSO: Apenas marque como correto=true se estiver 100% correto."
)


def _validator_make_api_call(payload: Dict[str, Any], timeout: int = 300) -> Dict[str, Any]:
    """Faz chamada à API usando chave de backup"""
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": VALIDATOR_API_KEY,
    }
    
    resp = requests.post(VALIDATOR_API_URL, headers=headers, data=json.dumps(payload), timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _validate_single_question(q: Dict[str, Any], stem: str, out_dir: Path, validated_dir: Path) -> Dict[str, Any]:
    """Valida uma única questão em background"""
    qid = q.get("id") or ""
    
    try:
        # Montar prompt com enunciado e resposta
        enunciado = q.get("enunciado", "") or ""
        explicacao = q.get("explicacao", "") or ""
        
        if not explicacao or not explicacao.strip():
            return {"id": qid, "correto": None, "observacao": "Sem resposta para validar"}
        
        prompt = f"{SYSTEM_PROMPT_VALIDATOR}\n\nQUESTÃO PARA VALIDAÇÃO:\n\nID: {qid}\n\nENUNCIADO:\n{enunciado}\n\nRESPOSTA FORNECIDA:\n{explicacao}\n\nValide se esta resposta está CORRETA ou ERRADA."
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        
        # Chamar API com chave de backup
        data = _validator_make_api_call(payload, timeout=300)
        candidates = data.get("candidates", [])
        if not candidates:
            return {"id": qid, "correto": None, "observacao": "Sem resposta da API"}
        
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts or "text" not in parts[0]:
            return {"id": qid, "correto": None, "observacao": "Resposta inválida da API"}
        
        text = parts[0]["text"]
        result = _extract_json_from_text(text)
        
        if result.get("questoes"):
            validation = result["questoes"][0]
        else:
            # Tentar extrair manualmente
            validation = {"id": qid, "correto": None, "observacao": "Não conseguiu extrair validação"}
        
        # Salvar resultado imediatamente
        _save_validation_result(q, validation, stem, out_dir, validated_dir)
        
        return validation
        
    except Exception as e:
        print(f"⚠️  Erro ao validar {qid}: {e}")
        validation = {"id": qid, "correto": None, "observacao": f"Erro: {e}"}
        _save_validation_result(q, validation, stem, out_dir, validated_dir)
        return validation


def _save_validation_result(q: Dict[str, Any], validation: Dict[str, Any], stem: str, out_dir: Path, validated_dir: Path) -> None:
    """Salva resultado de validação em arquivo, thread-safe"""
    qid = q.get("id") or "Q"
    is_correct = validation.get("correto")
    
    # Não salvar se None (sem resposta para validar)
    if is_correct is None:
        return
    
    with io_lock:
        validated_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar arquivo por questão
        base = f"{stem}_{qid}"
        result_path = validated_dir / f"{base}_validado.txt"
        
        # Se estiver incorreto, criar arquivo indicando erro mas sem conteúdo
        # Se estiver correto, copiar o conteúdo original
        if is_correct:
            # Copiar conteúdo da questão original
            original_txt = out_dir / f"{base}.txt"
            if original_txt.exists():
                content = original_txt.read_text(encoding="utf-8")
                lines = content.split("\n")
                # Adicionar "CORRETO" na primeira linha
                content_lines = [f"CORRETO"] + lines
                result_path.write_text("\n".join(content_lines), encoding="utf-8")
                print(f"✅ {qid}: CORRETO - salvo em {result_path.name}")
            else:
                print(f"⚠️  Arquivo original não encontrado para {qid}")
        else:
            # Marcar como ERRADO e escrever solução correta
            resposta_correta = validation.get("resposta_correta", "")
            if resposta_correta:
                content = f"ERRADO\n\n{resposta_correta}"
                result_path.write_text(content, encoding="utf-8")
                print(f"❌ {qid}: ERRADO - solução correta salvada em {result_path.name}")
            else:
                # Se não tem solução, apenas marcar como ERRADO
                result_path.write_text("ERRADO\n\nSem solução correta fornecida", encoding="utf-8")
                print(f"❌ {qid}: ERRADO - sem solução fornecida em {result_path.name}")
        
        # Copiar imediatamente para Desktop/resolvidas
        try:
            desktop_resolvidas = Path.home() / "Desktop" / "resolvidas"
            desktop_resolvidas.mkdir(parents=True, exist_ok=True)
            desktop_file = desktop_resolvidas / result_path.name
            desktop_file.write_text(result_path.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"📋 {qid}: Copiado para Desktop/resolvidas")
        except Exception as e:
            print(f"⚠️  Erro ao copiar {qid} para Desktop: {e}")


def run_validator_background(file_path: Path, out_dir: Path) -> None:
    """Monitora Desktop/resolvidas e valida questões encontradas"""
    if not VALIDATOR_ENABLED:
        return
    
    # Pasta do Desktop/resolvidas
    desktop_resolvidas = Path.home() / "Desktop" / "resolvidas"
    if not desktop_resolvidas.exists():
        print(f"⚠️  Pasta Desktop/resolvidas não encontrada")
        return
    
    # Pasta de destino para validados
    validated_dir = desktop_resolvidas / "validadas"
    validated_dir.mkdir(parents=True, exist_ok=True)
    
    # Procurar arquivos TXT em Desktop/resolvidas
    txt_files = list(desktop_resolvidas.glob("*.txt"))
    
    # Filtrar apenas arquivos de questões (Q1, Q1a, Q2b, etc)
    question_files = [f for f in txt_files if "_Q" in f.name and "_validado.txt" not in f.name]
    
    if not question_files:
        print("ℹ️  Nenhum arquivo de questão encontrado em Desktop/resolvidas")
        return
    
    print(f"\nValidador: encontrados {len(question_files)} arquivos para validar...")
    
    # Processar cada arquivo
    questions_to_validate = []
    for txt_file in question_files:
        try:
            # Extrair nome do arquivo e ID da questão
            content = txt_file.read_text(encoding="utf-8")
            lines = content.split("\n")
            if not lines:
                continue
            
            # Primeira linha geralmente é o enunciado
            enunciado = lines[0]
            
            # Tentar extrair ID do nome do arquivo
            # Formato: Prova_2_Linguagens_Livres_Contexto_Q1.txt
            stem_id = txt_file.stem
            qid = ""
            if "_Q" in stem_id:
                parts = stem_id.split("_Q")
                if len(parts) > 1:
                    qid = "Q" + parts[1]
            
            # Procurar por "Explicacao:" no conteúdo
            explicacao = ""
            for i, line in enumerate(lines):
                if "Explicacao:" in line:
                    explicacao = "\n".join(lines[i+1:]).strip()
                    break
            
            # Extrair apenas o conteúdo depois de "Explicacao:"
            if not explicacao and len(lines) > 1:
                # Se não encontrou "Explicacao:", tentar pegar da linha 2 em diante
                explicacao = "\n".join(lines[1:]).strip()
            
            if not explicacao:
                print(f"⚠️  Arquivo {txt_file.name} não tem conteúdo, pulando...")
                continue
            
            q = {
                "id": qid,
                "enunciado": enunciado,
                "explicacao": explicacao
            }
            questions_to_validate.append((q, txt_file.stem))
            
        except Exception as e:
            print(f"⚠️  Erro ao processar {txt_file.name}: {e}")
            continue
    
    if not questions_to_validate:
        print("ℹ️  Nenhuma questão válida encontrada")
        return
    
    print(f"Validando {len(questions_to_validate)} questoes em paralelo...")
    
    # Processar em paralelo
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_validate_single_question_desktop, q, stem, validated_dir): (q, stem)
            for q, stem in questions_to_validate
        }
        
        # Aguardar resultados
        for future in as_completed(futures):
            (q, stem) = futures[future]
            try:
                validation = future.result()
                # Resultado já foi salvo pela função
            except Exception as e:
                print(f"❌ Erro ao validar {q.get('id')}: {e}")
    
    print(f"✅ Validador concluído! Resultados em: {validated_dir}")


def _validate_single_question_desktop(q: Dict[str, Any], stem: str, validated_dir: Path) -> Dict[str, Any]:
    """Valida uma única questão lida do Desktop"""
    qid = q.get("id") or ""
    
    try:
        # Montar prompt com enunciado e resposta
        enunciado = q.get("enunciado", "") or ""
        explicacao = q.get("explicacao", "") or ""
        
        if not explicacao or not explicacao.strip():
            return {"id": qid, "correto": None, "observacao": "Sem resposta para validar"}
        
        prompt = f"{SYSTEM_PROMPT_VALIDATOR}\n\nQUESTÃO PARA VALIDAÇÃO:\n\nID: {qid}\n\nENUNCIADO:\n{enunciado}\n\nRESPOSTA FORNECIDA:\n{explicacao}\n\nValide se esta resposta está CORRETA ou ERRADA."
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        
        # Chamar API com chave de backup
        data = _validator_make_api_call(payload, timeout=300)
        candidates = data.get("candidates", [])
        if not candidates:
            return {"id": qid, "correto": None, "observacao": "Sem resposta da API"}
        
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts or "text" not in parts[0]:
            return {"id": qid, "correto": None, "observacao": "Resposta inválida da API"}
        
        text = parts[0]["text"]
        result = _extract_json_from_text(text)
        
        validation = (result.get("questoes") or [None])[0] or {}
        validation["id"] = qid  # Garantir que o ID está correto
        
        _save_validation_result_desktop(q, validation, stem, validated_dir)
        return validation
        
    except Exception as e:
        validation = {"id": qid, "correto": None, "observacao": f"Erro: {e}"}
        _save_validation_result_desktop(q, validation, stem, validated_dir)
        return validation


def _save_validation_result_desktop(q: Dict[str, Any], validation: Dict[str, Any], stem: str, validated_dir: Path) -> None:
    """Salva resultado de validação em arquivo no Desktop, thread-safe"""
    qid = q.get("id") or "Q"
    is_correct = validation.get("correto")
    
    # Não salvar se None (sem resposta para validar)
    if is_correct is None:
        return
    
    with io_lock:
        validated_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar arquivo por questão
        result_path = validated_dir / f"{stem}_validado.txt"
        
        # Se estiver incorreto, criar arquivo indicando erro mas sem conteúdo
        # Se estiver correto, copiar o conteúdo original
        if is_correct:
            # Copiar conteúdo da questão original do enunciado + explicação
            explicacao = q.get("explicacao", "")
            enunciado = q.get("enunciado", "")
            content_lines = [f"CORRETO", enunciado, f"Explicacao: {explicacao}"]
            result_path.write_text("\n".join(content_lines), encoding="utf-8")
            print(f"✅ {qid}: CORRETO - salvo em {result_path.name}")
        else:
            # Marcar como ERRADO e escrever solução correta
            resposta_correta = validation.get("resposta_correta", "")
            if resposta_correta:
                content = f"ERRADO\n\n{resposta_correta}"
                result_path.write_text(content, encoding="utf-8")
                print(f"❌ {qid}: ERRADO - solução correta salvada em {result_path.name}")
            else:
                # Se não tem solução, apenas marcar como ERRADO
                result_path.write_text("ERRADO\n\nSem solução correta fornecida", encoding="utf-8")
                print(f"❌ {qid}: ERRADO - sem solução fornecida em {result_path.name}")

