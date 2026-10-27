"""Etapa 3: para cada caso da amostra gera relato sintético e roda duas versões da solução.

  Versão A (baseline): LLM sozinho, sem recuperação.
  Versão B (RAG):      normas recuperadas por embeddings + estatística real do órgão/assunto.

Uso: python 03_pipeline.py [--n 10]   (retoma de onde parou; grava saida/resultados.jsonl)
"""
import argparse
import json

import numpy as np
import pandas as pd

from common import SAIDA, chat, chat_json, embed

TOP_K = 4

SISTEMA_RELATO = (
    "Você simula cidadãos brasileiros que registram manifestações na plataforma Fala.BR. "
    "Escreva em português, em primeira pessoa, 2 a 4 frases, tom natural e coloquial. "
    "Não inclua nome, CPF, telefone, e-mail nem endereço. Não mencione leis. Responda só com o relato.")

SISTEMA_RESPOSTA = (
    "Você é um assistente de ouvidoria pública brasileira que apoia o servidor. "
    "Analise a manifestação e responda SOMENTE em JSON com as chaves: "
    '"prioridade" ("alta", "média" ou "baixa"), '
    '"justificativa" (1 frase) e '
    '"minuta" (resposta cordial e objetiva dirigida diretamente ao cidadão, em segunda pessoa, '
    "80 a 150 palavras, sem inventar prazos ou números de protocolo). Critério de prioridade: alta = risco à vida, saúde, subsistência, "
    "denúncia de irregularidade grave ou direito violado; média = reclamação ou solicitação "
    "comum; baixa = elogio, sugestão ou pedido sem urgência.")


def carregar():
    am = pd.read_csv(SAIDA / "amostra.csv")
    chunks = json.loads((SAIDA / "normas_chunks.json").read_text())
    emb = np.load(SAIDA / "normas_emb.npy")
    agg = pd.read_csv(SAIDA / "agregado.csv")
    return am, chunks, emb, agg


def estatistica(agg: pd.DataFrame, orgao: str, assunto: str) -> str:
    sub = agg[(agg["nome_orgao"] == orgao) & (agg["assunto"] == assunto)]
    if sub["n"].sum() < 30:
        sub = agg[agg["nome_orgao"] == orgao]
        escopo = f"{orgao} (todos os assuntos)"
    else:
        escopo = f"{orgao}, assunto '{assunto}'"
    n, nd = sub["n"].sum(), sub["n_dias"].sum()
    if nd == 0:
        return ""
    return (f"Histórico real do Fala.BR para {escopo}: {int(n)} manifestações, "
            f"tempo médio de resolução {sub['soma_dias'].sum() / nd:.1f} dias, "
            f"{sub['n_atrasadas'].sum() / n * 100:.1f}% respondidas com atraso.")


def recuperar(consulta: str, chunks, emb):
    q = np.array(embed([consulta])[0], dtype="float32")
    q /= np.linalg.norm(q)
    idx = np.argsort(-(emb @ q))[:TOP_K]
    return [chunks[i] | {"score": float(emb[i] @ q)} for i in idx]


def formatar_caso(c) -> str:
    return (f"Tipo: {c['tipo_manifestacao']}\nÓrgão: {c['nome_orgao']} ({c['esfera']})\n"
            f"Assunto: {c['assunto']}\n")


def versao_a(c, relato):
    usuario = (formatar_caso(c) + f"\nRelato do cidadão:\n{relato}\n\n"
               "Se citar legislação, indique a lei e o artigo.")
    return chat_json(SISTEMA_RESPOSTA, usuario, max_tokens=700)


def versao_b(c, relato, chunks, emb, agg):
    trechos = recuperar(f"{c['tipo_manifestacao']}. {c['assunto']}. {relato}", chunks, emb)
    contexto = "\n\n".join(f"[{t['norma']}, art. {t['artigo']}]\n{t['texto']}" for t in trechos)
    usuario = (formatar_caso(c) + f"\nRelato do cidadão:\n{relato}\n\n"
               f"CONTEXTO NORMATIVO (única fonte permitida para citações):\n{contexto}\n\n"
               f"{estatistica(agg, c['nome_orgao'], c['assunto'])}\n\n"
               "Cite apenas artigos presentes no CONTEXTO NORMATIVO, no formato (Lei X, art. N). "
               "Se nenhum trecho for pertinente, não cite lei alguma.")
    return chat_json(SISTEMA_RESPOSTA, usuario, max_tokens=700), trechos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=None)
    args = ap.parse_args()

    am, chunks, emb, agg = carregar()
    saida = SAIDA / "resultados.jsonl"
    feitos = {json.loads(l)["id"] for l in saida.open()} if saida.exists() else set()
    casos = am if args.n is None else am.head(args.n)

    with saida.open("a") as f:
        for _, c in casos.iterrows():
            if int(c["id"]) in feitos:
                continue
            relato = chat(SISTEMA_RELATO,
                          f"Tipo: {c['tipo_manifestacao']}\nÓrgão: {c['nome_orgao']}\n"
                          f"Assunto: {c['assunto']}\nFaixa etária: {c['faixa_etaria']}",
                          temperatura=0.8, max_tokens=200)
            a = versao_a(c, relato)
            b, trechos = versao_b(c, relato, chunks, emb, agg)
            reg = {"id": int(c["id"]), "tipo": c["tipo_manifestacao"], "orgao": c["nome_orgao"],
                   "assunto": c["assunto"], "prioridade_ref": c["prioridade_ref"],
                   "relato": relato, "A": a, "B": b,
                   "trechos": [{"norma": t["norma"], "artigo": t["artigo"], "score": t["score"]}
                               for t in trechos]}
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
            f.flush()
            print(f"#{reg['id']} ref={reg['prioridade_ref']} A={a.get('prioridade')} "
                  f"B={b.get('prioridade')}", flush=True)


if __name__ == "__main__":
    main()
