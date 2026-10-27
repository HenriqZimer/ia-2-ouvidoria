"""Interface de demonstração: pipeline de ouvidoria com RAG (versões A e B lado a lado).

Uso: streamlit run app.py
"""
import importlib.util
import json
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

from common import MODELO_EMB, MODELO_LLM, OLLAMA, RAIZ, SAIDA, chat


def _modulo(nome: str, arquivo: str):
    spec = importlib.util.spec_from_file_location(nome, RAIZ / arquivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pipe = _modulo("pipeline", "03_pipeline.py")
aval = _modulo("avaliar", "04_avaliar.py")

TIPOS = ["Reclamação", "Solicitação", "Denúncia", "Comunicação", "Elogio", "Sugestão"]
COR = {"alta": "#C0392B", "média": "#E08E0B", "baixa": "#2E8B57"}

st.set_page_config(page_title="Ouvidoria com IA Generativa", page_icon="📨", layout="wide")


@st.cache_resource(show_spinner="Carregando base e índice de normas...")
def dados():
    am, chunks, emb, agg = pipe.carregar()
    corpus = {(aval.chave_norma(c["norma"]), c["artigo"]) for c in chunks}
    nomes_lei = {aval.chave_norma(c["norma"]): c["norma"].split(" (")[0] for c in chunks}
    pre = {}
    arq = SAIDA / "resultados.jsonl"
    if arq.exists():
        pre = {r["id"]: r for r in map(json.loads, arq.open())}
    orgaos = agg.groupby("nome_orgao")["n"].sum().sort_values(ascending=False).head(300).index.tolist()
    return am, chunks, emb, agg, corpus, nomes_lei, pre, orgaos


am, chunks, emb, agg, corpus, nomes_lei, pre, orgaos = dados()


def status_ollama():
    try:
        r = requests.get(f"{OLLAMA}/api/tags", timeout=4)
        nomes = {m["name"] for m in r.json()["models"]}
        return MODELO_LLM in nomes and any(n.startswith(MODELO_EMB) for n in nomes), sorted(nomes)
    except requests.RequestException:
        return False, []


def selo(prioridade) -> str:
    p = str(prioridade).lower()
    cor = COR.get(p, "#6B7C8F")
    return (f"<span style='background:{cor};color:#fff;padding:4px 14px;border-radius:14px;"
            f"font-weight:700;font-size:1.05rem'>{p.upper()}</span>")


def mostrar_versao(titulo: str, res: dict, trechos: list | None):
    st.subheader(titulo)
    if "erro" in res:
        st.error("O modelo devolveu um JSON inválido.")
        st.code(res.get("bruto", ""))
        return
    st.markdown(f"Prioridade sugerida: {selo(res.get('prioridade'))}", unsafe_allow_html=True)
    st.caption(res.get("justificativa", ""))
    minuta = str(res.get("minuta", ""))
    st.markdown(f"> {minuta}")

    recuperados = {(aval.chave_norma(t["norma"]), t["artigo"]) for t in (trechos or [])}
    cits = sorted(aval.citacoes(minuta))
    st.markdown("**Citações legais na minuta**")
    if not cits:
        st.write("Nenhuma citação.")
    for lei, art in cits:
        nome = nomes_lei.get(lei, f"norma {lei}")
        if (lei, art) in recuperados:
            st.success(f"{nome}, art. {art}: está no contexto recuperado")
        elif (lei, art) in corpus:
            st.warning(f"{nome}, art. {art}: existe no corpus, mas não foi recuperado")
        else:
            st.error(f"{nome if lei in nomes_lei else 'Lei ' + lei}, art. {art}: fora do corpus, sem fundamento verificável")


def bloco_validacao(caso: dict, relato: str, a: dict, b: dict):
    st.divider()
    st.subheader("Validação humana")
    st.caption("O servidor decide: a IA só sugere.")
    c1, c2 = st.columns([1, 3])
    with c1:
        base = st.radio("Partir da minuta", ["B (com RAG)", "A (sem RAG)"], key="base_val")
        origem = b if base.startswith("B") else a
        opcoes = ["alta", "média", "baixa"]
        padrao = str(origem.get("prioridade", "média")).lower()
        prioridade = st.selectbox("Prioridade final", opcoes, index=opcoes.index(padrao) if padrao in opcoes else 1,
                                  key=f"prio_{base}")
    with c2:
        minuta_final = st.text_area("Minuta final (editável)", value=str(origem.get("minuta", "")),
                                    height=170, key=f"min_{base}")
    decisao = st.radio("Decisão", ["Aprovar", "Aprovar com edição", "Devolver para revisão"], horizontal=True)
    if st.button("Registrar decisão", type="primary"):
        reg = {"quando": datetime.now().isoformat(timespec="seconds"), "caso": caso["id_caso"], "decisao": decisao,
               "partiu_de": base[0], "prioridade_final": prioridade,
               "editada": minuta_final.strip() != str(origem.get("minuta", "")).strip(), "minuta_final": minuta_final}
        with (SAIDA / "validacoes.jsonl").open("a") as f:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
        st.success(f"Decisão registrada: {decisao}.")


# barra lateral
with st.sidebar:
    st.title("📨 Ouvidoria + IA")
    ok, modelos = status_ollama()
    if ok:
        st.success(f"Ollama online\n\nLLM: {MODELO_LLM}\n\nEmbeddings: {MODELO_EMB}")
    else:
        st.error("Ollama indisponível ou modelos ausentes. Use o modo pré-computado.")
    st.caption(f"Endpoint: {OLLAMA}")
    st.caption("Base: Fala.BR/CGU, 8,75 mi de manifestações. Relatos sintéticos.")

aba_demo, aba_res, aba_base = st.tabs(["Demo ao vivo", "Resultados do experimento", "Base de dados"])

with aba_demo:
    st.header("Do registro à minuta, com validação humana")
    modo = st.radio("Caso", ["Da amostra (90 casos)", "Novo caso"], horizontal=True)

    if modo.startswith("Da amostra"):
        rotulos = {int(r["id"]): f"#{int(r['id'])}  {r['tipo_manifestacao']}  ·  {r['assunto']}  ·  {r['nome_orgao'][:50]}"
                   for _, r in am.iterrows()}
        cid = st.selectbox("Escolha o caso", list(rotulos), format_func=rotulos.get)
        linha = am[am["id"] == cid].iloc[0]
        caso = {"id_caso": int(cid), "tipo_manifestacao": linha["tipo_manifestacao"], "nome_orgao": linha["nome_orgao"],
                "esfera": linha["esfera"], "assunto": linha["assunto"]}
        ref = linha["prioridade_ref"]
        relato = pre.get(int(cid), {}).get("relato", "")
        relato = st.text_area("Relato (sintético)", value=relato, height=110, key=f"relato_{cid}")
        modos = ["Resultado pré-computado (instantâneo)", "Rodar ao vivo no Ollama"] if int(cid) in pre else ["Rodar ao vivo no Ollama"]
        execucao = st.radio("Execução", modos, horizontal=True)
        st.caption(f"Prioridade de referência (regra por tipo e assunto): **{ref}**")
    else:
        c1, c2, c3 = st.columns(3)
        tipo = c1.selectbox("Tipo", TIPOS)
        orgao = c2.selectbox("Órgão", orgaos)
        assuntos = (agg[agg["nome_orgao"] == orgao].groupby("assunto")["n"].sum().sort_values(ascending=False)
                    .head(40).index.tolist())
        assunto = c3.selectbox("Assunto", assuntos)
        esfera = agg[agg["nome_orgao"] == orgao]["esfera"].mode().iloc[0]
        caso = {"id_caso": "novo", "tipo_manifestacao": tipo, "nome_orgao": orgao, "esfera": esfera, "assunto": assunto}
        ref, execucao = None, "Rodar ao vivo no Ollama"
        if st.button("Gerar relato sintético com o LLM"):
            with st.spinner("Gerando relato..."):
                st.session_state["relato_novo"] = chat(
                    pipe.SISTEMA_RELATO, f"Tipo: {tipo}\nÓrgão: {orgao}\nAssunto: {assunto}\nFaixa etária: 40-59 anos",
                    temperatura=0.8, max_tokens=200)
        relato = st.text_area("Relato do cidadão (digite ou gere)", value=st.session_state.get("relato_novo", ""), height=110)

    st.caption(pipe.estatistica(agg, caso["nome_orgao"], caso["assunto"]))

    if st.button("Analisar manifestação", type="primary", disabled=not relato.strip()):
        chave = (caso["id_caso"], relato.strip())
        if execucao.startswith("Resultado") and caso["id_caso"] in pre:
            r = pre[caso["id_caso"]]
            st.session_state["res"] = {"chave": chave, "A": r["A"], "B": r["B"], "trechos": r["trechos"], "seg": None}
        else:
            t0 = datetime.now()
            with st.spinner("Rodando versão A (sem RAG)..."):
                a = pipe.versao_a(caso, relato)
            with st.spinner("Recuperando normas e rodando versão B (RAG)..."):
                b, trechos = pipe.versao_b(caso, relato, chunks, emb, agg)
            seg = (datetime.now() - t0).total_seconds()
            st.session_state["res"] = {"chave": chave, "A": a, "B": b, "seg": seg,
                                       "trechos": [{"norma": t["norma"], "artigo": t["artigo"], "score": t["score"]} for t in trechos]}

    res = st.session_state.get("res")
    if res and res["chave"] == (caso["id_caso"], relato.strip()):
        if res.get("seg"):
            st.caption(f"Tempo ao vivo: {res['seg']:.0f} s para as duas versões.")
        col_a, col_b = st.columns(2)
        with col_a:
            mostrar_versao("A: LLM sozinho (baseline)", res["A"], None)
        with col_b:
            mostrar_versao("B: LLM + RAG", res["B"], res["trechos"])
            st.markdown("**Trechos recuperados**")
            for t in res["trechos"]:
                st.write(f"{t['norma'].split(' (')[0]}, art. {t['artigo']}  ·  similaridade {t['score']:.2f}")
        bloco_validacao(caso, relato, res["A"], res["B"])

    vf = SAIDA / "validacoes.jsonl"
    if vf.exists():
        n = sum(1 for _ in vf.open())
        st.caption(f"{n} decisão(ões) registradas em saida/validacoes.jsonl")

with aba_res:
    met = json.loads((SAIDA / "metricas.json").read_text())
    st.header(f"Avaliação em {met['n_casos']} casos")
    a, b = met["A"], met["B"]
    c = st.columns(4)
    c[0].metric("Concordância da prioridade (A)", f"{a['acuracia_prioridade'] * 100:.1f}%")
    c[1].metric("Concordância da prioridade (B)", f"{b['acuracia_prioridade'] * 100:.1f}%",
                f"{(b['acuracia_prioridade'] - a['acuracia_prioridade']) * 100:.1f} pp")
    c[2].metric("Citações fundamentadas (A)", f"{a['citacoes_fundamentadas_pct']:.1f}%")
    c[3].metric("Citações fundamentadas (B)", f"{b['citacoes_fundamentadas_pct']:.1f}%",
                f"{b['citacoes_fundamentadas_pct'] - a['citacoes_fundamentadas_pct']:.1f} pp")
    st.image(str(SAIDA / "grafico_comparacao.png"), width=720)
    tabela = pd.DataFrame({k: {"A: sem RAG": a[k], "B: com RAG": b[k]} for k in
                           ["acuracia_prioridade", "f1_macro", "minutas_com_citacao_pct", "citacoes_total",
                            "citacoes_fundamentadas_pct", "palavras_medias"]}).T
    st.dataframe(tabela, width="stretch")
    st.subheader("Sumarização agregada (2025)")
    resumo = (SAIDA / "sumario_gestao.md").read_text().split("---")[0]
    st.markdown(resumo)
    st.image(str(SAIDA / "grafico_orgaos.png"), width=720)
    st.warning("O resumo escrito pelo LLM trouxe números errados. Os indicadores do gráfico são calculados em código.")
    with st.expander("Exemplos qualitativos"):
        st.markdown((SAIDA / "exemplos.md").read_text())

with aba_base:
    eda = json.loads((SAIDA / "eda.json").read_text())
    st.header("Base do Fala.BR")
    c = st.columns(4)
    c[0].metric("Registros", f"{eda['total_registros']:,}".replace(",", "."))
    c[1].metric("Órgãos", f"{eda['n_orgaos']:,}".replace(",", "."))
    c[2].metric("Assuntos", eda["n_assuntos"])
    c[3].metric("Resolução média", f"{eda['dias_resolucao_medio']:.0f} dias")
    esq, dir_ = st.columns(2)
    esq.subheader("Manifestações por ano (2026 parcial)")
    esq.bar_chart(pd.Series(eda["por_ano"], name="manifestações"))
    dir_.subheader("Por tipo")
    dir_.bar_chart(pd.Series(eda["por_tipo"], name="manifestações"))
    st.info("Os CSVs não trazem o texto da manifestação, só metadados. Os relatos do experimento são sintéticos.")
    st.subheader("Percentual de valores ausentes (colunas relevantes)")
    aus = pd.Series(eda["ausentes_pct"]).sort_values(ascending=False)
    st.bar_chart(aus[aus > 0])
