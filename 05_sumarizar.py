"""Etapa 5: sumarização agregada da base completa (8,75 mi de manifestações) para a gestão.

Calcula os indicadores por código e pede ao LLM apenas a redação do resumo sobre as tabelas
já calculadas, evitando que o modelo invente números.
Saídas em saida/: indicadores_orgaos.csv, grafico_orgaos.png, sumario_gestao.md
"""
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from common import SAIDA, chat  # noqa: E402

ANO = 2025
MIN_MANIF = 5000

SISTEMA = (
    "Você é analista de dados de uma ouvidoria pública. Escreva em português um resumo executivo "
    "para o gestor, com no máximo 220 palavras, em tópicos curtos: panorama, 3 principais gargalos "
    "e 2 recomendações. Use EXCLUSIVAMENTE os números das tabelas fornecidas, sem inventar dados.")


def main():
    ag = pd.read_csv(SAIDA / "agregado.csv")
    ano = ag[ag["ano"] == ANO]

    org = ano.groupby("nome_orgao").agg(
        n=("n", "sum"), soma_dias=("soma_dias", "sum"), n_dias=("n_dias", "sum"),
        atrasadas=("n_atrasadas", "sum"), soma_sat=("soma_sat", "sum"), n_sat=("n_sat", "sum"),
    ).reset_index()
    org["dias_medios"] = (org["soma_dias"] / org["n_dias"]).round(1)
    org["atraso_pct"] = (org["atrasadas"] / org["n"] * 100).round(1)
    org["satisfacao_media"] = (org["soma_sat"] / org["n_sat"]).round(2)
    org = org[org["n"] >= MIN_MANIF].sort_values("atraso_pct", ascending=False)
    org[["nome_orgao", "n", "dias_medios", "atraso_pct", "satisfacao_media"]].to_csv(
        SAIDA / "indicadores_orgaos.csv", index=False)

    tipos = ano.groupby("tipo_manifestacao")["n"].sum().sort_values(ascending=False)
    assuntos = ano.groupby("assunto")["n"].sum().sort_values(ascending=False).head(8)
    esferas = ano.groupby("esfera").agg(n=("n", "sum"), atr=("n_atrasadas", "sum")).assign(
        atraso_pct=lambda d: (d["atr"] / d["n"] * 100).round(1))["atraso_pct"]
    anual = ag.groupby("ano")["n"].sum()

    prompt = (
        f"Ano analisado: {ANO}. Total de manifestações: {int(ano['n'].sum())}.\n\n"
        f"Volume anual 2019-{ANO} (2026 é ano parcial e foi omitido):\n"
        f"{anual.loc[2019:ANO].to_string()}\n\n"
        f"Por tipo:\n{tipos.to_string()}\n\nAssuntos mais frequentes:\n{assuntos.to_string()}\n\n"
        f"Atraso (%) por esfera:\n{esferas.to_string()}\n\n"
        f"Órgãos com maior % de atraso (mín. {MIN_MANIF} manifestações):\n"
        f"{org.head(8)[['nome_orgao', 'n', 'dias_medios', 'atraso_pct']].to_string(index=False)}")
    resumo = chat(SISTEMA, prompt, temperatura=0.2, max_tokens=700)
    (SAIDA / "sumario_gestao.md").write_text(
        f"# Sumarização agregada, {ANO}\n\n{resumo}\n\n---\n## Dados de entrada\n```\n{prompt}\n```\n")

    top = org.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(top["nome_orgao"].str.slice(0, 45), top["atraso_pct"], color="#1f6feb")
    ax.set_xlabel(f"% de manifestações respondidas com atraso ({ANO})")
    fig.tight_layout()
    fig.savefig(SAIDA / "grafico_orgaos.png", dpi=160)
    print(resumo)


if __name__ == "__main__":
    main()
