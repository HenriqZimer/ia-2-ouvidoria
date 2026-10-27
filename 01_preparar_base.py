"""Etapa 1: lê os CSVs do Fala.BR (2014-2026), limpa, agrega e extrai a amostra de trabalho.

Saídas em saida/:
  agregado.csv     contagens e médias por ano/tipo/esfera/órgão/assunto (base completa)
  amostra.csv      casos estratificados por tipo, com rótulo de prioridade de referência
  eda.json         estatísticas exploratórias da base completa
"""
import json
import re

import pandas as pd

from common import DADOS, SAIDA, SEED, sem_acento

CHUNK = 400_000
ANOS_AMOSTRA = (2025, 2026)
POR_TIPO = {"Reclamação": 30, "Solicitação": 20, "Denúncia": 20, "Comunicação": 10,
            "Elogio": 5, "Sugestão": 5}

AREAS_CRITICAS = re.compile(
    r"sa[uú]de|previd[eê]ncia|assist[eê]ncia social|seguran[cç]a|benef[ií]cio|"
    r"educa[cç][aã]o|trabalho|inss|sus", re.I)


def normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [sem_acento(c).strip().lower().replace(" ", "_").replace("/", "_") for c in df.columns]
    return df


def prioridade_referencia(tipo: str, assunto: str) -> str:
    """Rótulo de referência por regra (tipo + sensibilidade do assunto), usado como gabarito."""
    base = {"Denúncia": 3, "Reclamação": 2, "Solicitação": 2, "Comunicação": 2,
            "Elogio": 1, "Sugestão": 1}.get(tipo, 2)
    if base >= 2 and AREAS_CRITICAS.search(assunto or ""):
        base = min(3, base + 1)
    return {3: "alta", 2: "média", 1: "baixa"}[base]


def ler_ano(caminho):
    for ch in pd.read_csv(caminho, sep=";", encoding="latin-1", dtype=str, chunksize=CHUNK):
        ch = normalizar_colunas(ch)
        ch["data_registro"] = pd.to_datetime(ch["data_registro"], format="%d/%m/%Y", errors="coerce")
        ch["dias_para_resolucao"] = pd.to_numeric(ch["dias_para_resolucao"], errors="coerce")
        ch["dias_de_atraso"] = pd.to_numeric(ch["dias_de_atraso"], errors="coerce")
        ch["satisfacao"] = pd.to_numeric(ch["satisfacao"].str.extract(r"\((\d)\)")[0], errors="coerce")
        ch["ano"] = ch["data_registro"].dt.year
        yield ch


def main():
    SAIDA.mkdir(exist_ok=True)
    parciais, total, ausentes, amostras = [], 0, None, []
    for csv in sorted(DADOS.glob("Manifestacoes_Ouvidoria_*.csv")):
        n_arq = 0
        for ch in ler_ano(csv):
            n_arq += len(ch)
            aus = ch.isna().sum()
            ausentes = aus if ausentes is None else ausentes.add(aus, fill_value=0)
            ch["atrasada"] = (ch["dias_de_atraso"].fillna(0) > 0).astype(int)
            g = ch.groupby(["ano", "tipo_manifestacao", "esfera", "nome_orgao", "assunto"],
                           dropna=False).agg(
                n=("assunto", "size"),
                soma_dias=("dias_para_resolucao", "sum"),
                n_dias=("dias_para_resolucao", "count"),
                n_atrasadas=("atrasada", "sum"),
                soma_sat=("satisfacao", "sum"),
                n_sat=("satisfacao", "count"),
            ).reset_index()
            parciais.append(g)
            if ch["ano"].iloc[0] in ANOS_AMOSTRA:
                amostras.append(ch[ch["situacao"] == "Concluída"].sample(
                    frac=0.01, random_state=SEED))
        total += n_arq
        print(csv.name, n_arq)

    chave = ["ano", "tipo_manifestacao", "esfera", "nome_orgao", "assunto"]
    agg = pd.concat(parciais).groupby(chave, dropna=False).sum().reset_index()
    agg.to_csv(SAIDA / "agregado.csv", index=False)

    eda = {
        "total_registros": int(total),
        "ausentes_pct": (ausentes / total * 100).round(2).to_dict(),
        "por_ano": agg.groupby("ano")["n"].sum().astype(int).to_dict(),
        "por_tipo": agg.groupby("tipo_manifestacao")["n"].sum().astype(int).to_dict(),
        "por_esfera": agg.groupby("esfera")["n"].sum().astype(int).to_dict(),
        "n_orgaos": int(agg["nome_orgao"].nunique()),
        "n_assuntos": int(agg["assunto"].nunique()),
        "taxa_atraso_pct": round(agg["n_atrasadas"].sum() / total * 100, 2),
        "dias_resolucao_medio": round(agg["soma_dias"].sum() / agg["n_dias"].sum(), 2),
    }
    (SAIDA / "eda.json").write_text(json.dumps(eda, ensure_ascii=False, indent=2))

    pool = pd.concat(amostras)
    pool = pool[pool["nome_orgao"].notna() & pool["assunto"].notna()]
    pool = pool[~pool["assunto"].str.contains("Não Informado|Outros", case=False, na=False)]
    partes = [pool[pool["tipo_manifestacao"] == t].sample(
        n=min(n, (pool["tipo_manifestacao"] == t).sum()), random_state=SEED)
        for t, n in POR_TIPO.items()]
    am = pd.concat(partes).sample(frac=1, random_state=SEED).reset_index(drop=True)
    am["id"] = am.index + 1
    am["prioridade_ref"] = [prioridade_referencia(t, a) for t, a in zip(am["tipo_manifestacao"], am["assunto"])]
    cols = ["id", "ano", "tipo_manifestacao", "esfera", "nome_orgao", "uf_do_orgao", "assunto",
            "faixa_etaria", "dias_para_resolucao", "dias_de_atraso", "prioridade_ref"]
    am[cols].to_csv(SAIDA / "amostra.csv", index=False)
    print(f"total={total}  amostra={len(am)}")
    print(am["prioridade_ref"].value_counts().to_string())


if __name__ == "__main__":
    main()
