"""Etapa 2: chunking normativo (por artigo) das leis baixadas do Planalto e indexação com embeddings."""
import json
import re

import numpy as np
from bs4 import BeautifulSoup

from common import NORMAS, SAIDA, embed

LEIS = {
    "lei_13460_2017": "Lei 13.460/2017 (Direitos do usuário de serviços públicos)",
    "lei_12527_2011_lai": "Lei 12.527/2011 (Lei de Acesso à Informação)",
    "lgpd_13709_2018": "Lei 13.709/2018 (LGPD)",
    "decreto_9492_2018": "Decreto 9.492/2018 (Sistema de Ouvidoria do Poder Executivo Federal)",
    "lei_14129_2021": "Lei 14.129/2021 (Governo Digital)",
}
MAX_CHARS = 1400
RE_ARTIGO = re.compile(r"(?=^Art\.\s*\d+[ºo°]?[-A-Z]*\.?\s)", re.M)
RE_NUM = re.compile(r"^Art\.\s*(\d+)")


def texto_limpo(caminho) -> str:
    soup = BeautifulSoup(caminho.read_bytes(), "lxml", from_encoding="windows-1252")
    for t in soup(["strike", "s", "script", "style"]):  # dispositivos revogados
        t.decompose()
    linhas = [re.sub(r"\s+", " ", p.get_text(" ")).strip() for p in soup.find_all("p")]
    return "\n".join(l for l in linhas if l)


def dividir(artigo: str) -> list[str]:
    if len(artigo) <= MAX_CHARS:
        return [artigo]
    cabeca = artigo.split(" ", 2)[:2]
    cabeca = " ".join(cabeca)
    partes, atual = [], ""
    for linha in artigo.split("\n"):
        if len(atual) + len(linha) > MAX_CHARS and atual:
            partes.append(atual)
            atual = f"{cabeca} (cont.) "
        atual += linha + "\n"
    partes.append(atual)
    return [p.strip() for p in partes]


def main():
    chunks = []
    for chave, nome in LEIS.items():
        texto = texto_limpo(NORMAS / f"{chave}.html")
        inicio = RE_ARTIGO.search(texto)
        artigos = RE_ARTIGO.split(texto[inicio.start():]) if inicio else []
        for art in artigos:
            m = RE_NUM.match(art)
            if not m:
                continue
            for parte in dividir(art.strip()):
                chunks.append({"norma": nome, "artigo": int(m.group(1)), "texto": parte})
        print(nome, sum(1 for c in chunks if c["norma"] == nome), "chunks")

    vetores = []
    for i in range(0, len(chunks), 16):
        lote = [f'{c["norma"]}. {c["texto"]}' for c in chunks[i:i + 16]]
        vetores += embed(lote)
        print(f"embeddings {min(i + 16, len(chunks))}/{len(chunks)}", end="\r")
    m = np.array(vetores, dtype="float32")
    m /= np.linalg.norm(m, axis=1, keepdims=True)
    np.save(SAIDA / "normas_emb.npy", m)
    (SAIDA / "normas_chunks.json").write_text(json.dumps(chunks, ensure_ascii=False))
    print("\nindexado:", m.shape)


if __name__ == "__main__":
    main()
