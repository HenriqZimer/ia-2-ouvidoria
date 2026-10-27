"""Etapa 4: métricas de priorização e de fundamentação normativa (A sem RAG vs B com RAG).

Saídas em saida/: metricas.json, grafico_*.png, exemplos.md, avaliacao_manual.csv
"""
import json
import re
from collections import Counter

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from common import SAIDA, SEED  # noqa: E402

CLASSES = ["baixa", "média", "alta"]
ALIAS = {"lgpd": "13709", "lai": "12527"}
RE_LEI_ART = re.compile(
    r"(?:Lei|Decreto)[^()\d]{0,15}([\d\.]{4,})(?:/\d{4})?[^()]{0,30}?art(?:igo|s)?\.?\s*(\d+)", re.I)
RE_ART_LEI = re.compile(
    r"art(?:igo|s)?\.?\s*(\d+)[^()]{0,40}?(?:Lei|Decreto)[^()\d]{0,15}([\d\.]{4,})", re.I)
RE_ALIAS = re.compile(r"\b(LGPD|LAI)\b[^()]{0,30}?art(?:igo|s)?\.?\s*(\d+)", re.I)


def chave_norma(nome: str) -> str:
    return re.sub(r"\D", "", re.search(r"(?:Lei|Decreto)\s*([\d\.]+)", nome).group(1))


def citacoes(texto: str) -> set[tuple[str, int]]:
    achadas = {(re.sub(r"\D", "", l), int(a)) for l, a in RE_LEI_ART.findall(texto)}
    achadas |= {(re.sub(r"\D", "", l), int(a)) for a, l in RE_ART_LEI.findall(texto)}
    achadas |= {(ALIAS[k.lower()], int(a)) for k, a in RE_ALIAS.findall(texto)}
    return achadas


def f1_macro(ref, pred):
    fs = []
    for c in CLASSES:
        tp = sum(r == c and p == c for r, p in zip(ref, pred))
        fp = sum(r != c and p == c for r, p in zip(ref, pred))
        fn = sum(r == c and p != c for r, p in zip(ref, pred))
        fs.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return sum(fs) / len(fs)


def main():
    regs = [json.loads(l) for l in (SAIDA / "resultados.jsonl").open()]
    chunks = json.loads((SAIDA / "normas_chunks.json").read_text())
    corpus = {(chave_norma(c["norma"]), c["artigo"]) for c in chunks}

    met, tabela = {"n_casos": len(regs)}, []
    for v in ("A", "B"):
        ref = [r["prioridade_ref"] for r in regs]
        pred = [str(r[v].get("prioridade", "")).lower() for r in regs]
        pred = [p if p in CLASSES else "inválido" for p in pred]
        acerto = sum(a == b for a, b in zip(ref, pred)) / len(regs)
        adj = sum(abs(CLASSES.index(a) - CLASSES.index(b)) <= 1
                  for a, b in zip(ref, pred) if b in CLASSES) / len(regs)
        conf = pd.crosstab(pd.Series(ref, name="ref"), pd.Series(pred, name="pred"))

        n_cit = n_validas = n_pertinentes = com_cit = 0
        palavras, terceira = [], 0
        for r in regs:
            texto = str(r[v].get("minuta", ""))
            palavras.append(len(texto.split()))
            terceira += bool(re.search(r"\bo cidad[ãa]o\b|\ba cidad[ãa]\b", texto, re.I))
            cit = citacoes(texto)
            recuperados = {(chave_norma(t["norma"]), t["artigo"]) for t in r["trechos"]}
            com_cit += bool(cit)
            n_cit += len(cit)
            n_validas += sum(c in corpus for c in cit)
            n_pertinentes += sum(c in recuperados for c in cit)

        met[v] = {
            "acuracia_prioridade": round(acerto, 3),
            "acuracia_adjacente": round(adj, 3),
            "f1_macro": round(f1_macro(ref, pred), 3),
            "json_invalido": sum(p == "inválido" for p in pred),
            "minutas_com_citacao_pct": round(com_cit / len(regs) * 100, 1),
            "citacoes_total": n_cit,
            "citacoes_existentes_no_corpus_pct": round(n_validas / n_cit * 100, 1) if n_cit else None,
            "citacoes_fundamentadas_pct": round(n_pertinentes / n_cit * 100, 1) if n_cit else None,
            "palavras_medias": round(sum(palavras) / len(palavras), 1),
            "minutas_em_terceira_pessoa_pct": round(terceira / len(regs) * 100, 1),
            "matriz_confusao": conf.to_dict(),
        }
        tabela.append((v, acerto, 0 if not n_cit else n_pertinentes / n_cit))
    met["dist_ref"] = dict(Counter(r["prioridade_ref"] for r in regs))
    met["dist_pred_A"] = dict(Counter(str(r["A"].get("prioridade")) for r in regs))
    met["dist_pred_B"] = dict(Counter(str(r["B"].get("prioridade")) for r in regs))
    (SAIDA / "metricas.json").write_text(json.dumps(met, ensure_ascii=False, indent=2))

    fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
    nomes = ["A: sem RAG", "B: com RAG"]
    ax[0].bar(nomes, [t[1] * 100 for t in tabela], color=["#8c8c8c", "#1f6feb"])
    ax[0].set_title("Concordância da prioridade\ncom a regra de referência (%)")
    ax[1].bar(nomes, [t[2] * 100 for t in tabela], color=["#8c8c8c", "#1f6feb"])
    ax[1].set_title("Citações legais fundamentadas\nno contexto recuperado (%)")
    for a in ax:
        a.set_ylim(0, 100)
        for p in a.patches:
            a.annotate(f"{p.get_height():.0f}", (p.get_x() + p.get_width() / 2, p.get_height()),
                       ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(SAIDA / "grafico_comparacao.png", dpi=160)

    # exemplos qualitativos: um acerto, um erro de prioridade e uma alucinação do baseline
    def tem_alucinacao_a(r):
        rec = {(chave_norma(t["norma"]), t["artigo"]) for t in r["trechos"]}
        return any(c not in corpus for c in citacoes(str(r["A"].get("minuta", ""))))

    escolhas = []
    for rotulo, filtro in [
        ("Acerto de prioridade", lambda r: r["A"].get("prioridade") == r["B"].get("prioridade") == r["prioridade_ref"]),
        ("Divergência de prioridade", lambda r: r["B"].get("prioridade") != r["prioridade_ref"]),
        ("Baseline cita norma inexistente no corpus", tem_alucinacao_a),
    ]:
        for r in regs:
            if filtro(r) and r["id"] not in [e[1]["id"] for e in escolhas]:
                escolhas.append((rotulo, r))
                break
    md = ["# Exemplos qualitativos\n"]
    for rotulo, r in escolhas:
        md += [f"## {rotulo} (caso {r['id']})", f"- **Tipo/Assunto:** {r['tipo']} / {r['assunto']}",
               f"- **Órgão:** {r['orgao']}", f"- **Prioridade de referência:** {r['prioridade_ref']}",
               f"\n**Relato (sintético):** {r['relato']}\n",
               f"**A (sem RAG)** prioridade={r['A'].get('prioridade')}\n> {r['A'].get('minuta')}\n",
               f"**B (com RAG)** prioridade={r['B'].get('prioridade')}\n> {r['B'].get('minuta')}\n",
               "**Trechos recuperados:** " + "; ".join(f"{t['norma'].split(' (')[0]} art. {t['artigo']}"
                                                       for t in r["trechos"]) + "\n"]
    (SAIDA / "exemplos.md").write_text("\n".join(md))

    # planilha para avaliação manual (nota 1-5) feita pelo grupo
    manual = pd.DataFrame([{
        "id": r["id"], "relato": r["relato"], "minuta_A": r["A"].get("minuta"),
        "minuta_B": r["B"].get("minuta"), "nota_A_adequacao": "", "nota_B_adequacao": "",
        "nota_A_tom": "", "nota_B_tom": "", "observacao": ""}
        for r in pd.Series(regs).sample(n=min(20, len(regs)), random_state=SEED)])
    manual.to_csv(SAIDA / "avaliacao_manual.csv", index=False)
    print(json.dumps({k: met[k] for k in ("A", "B")}, ensure_ascii=False, indent=2,
                     default=str)[:3500])


if __name__ == "__main__":
    main()
