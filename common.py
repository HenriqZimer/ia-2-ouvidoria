"""Configuração e cliente Ollama compartilhados pelas etapas do pipeline."""
import json
import os
import time
import unicodedata
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent
# CSVs do Fala.BR: DADOS_DIR, ou ./dados, ou ../dados (layout local de desenvolvimento)
DADOS = Path(os.environ.get("DADOS_DIR") or (RAIZ / "dados" if (RAIZ / "dados").exists() else RAIZ.parent / "dados"))
NORMAS = RAIZ / "normas"
SAIDA = RAIZ / "saida"

OLLAMA = os.environ.get("OLLAMA_URL", "http://ollama.henriqzimer.com.br")
MODELO_LLM = os.environ.get("MODELO_LLM", "qwen3-vl:8b-instruct")
MODELO_EMB = os.environ.get("MODELO_EMB", "bge-m3")

SEED = 42


def sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _post(rota: str, payload: dict, tentativas: int = 8, timeout: int = 600) -> dict:
    for i in range(tentativas):
        try:
            r = requests.post(f"{OLLAMA}{rota}", json=payload, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            if i == tentativas - 1:
                raise
            time.sleep(15 * (i + 1))  # cobre o restart do pod do Ollama


def embed(textos: list[str]) -> list[list[float]]:
    return _post("/api/embed", {"model": MODELO_EMB, "input": textos})["embeddings"]


def chat(sistema: str, usuario: str, temperatura: float = 0.2, json_saida: bool = False,
         max_tokens: int = 600) -> str:
    payload = {
        "model": MODELO_LLM,
        "stream": False,
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": usuario},
        ],
        "options": {"temperature": temperatura, "num_predict": max_tokens, "seed": SEED},
    }
    if json_saida:
        payload["format"] = "json"
    return _post("/api/chat", payload)["message"]["content"].strip()


def chat_json(sistema: str, usuario: str, **kw) -> dict:
    bruto = chat(sistema, usuario, json_saida=True, **kw)
    try:
        return json.loads(bruto)
    except json.JSONDecodeError:
        return {"erro": "json_invalido", "bruto": bruto}
