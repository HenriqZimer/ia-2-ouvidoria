# Ouvidoria com IA Generativa (Fala.BR + Qwen3 local + RAG)

Protótipo que, a partir de metadados reais do Fala.BR, gera uma minuta de resposta e uma
prioridade para a manifestação, fundamentada em normas recuperadas por embeddings, com
validação humana. Compara um baseline (A, LLM sozinho) com a versão com RAG (B).

## Requisitos
- Python 3.10+ e `pip install pandas numpy requests beautifulsoup4 lxml matplotlib`
- Ollama acessível com os modelos `qwen3-vl:8b-instruct` e `bge-m3`
  (`OLLAMA_URL`, `MODELO_LLM`, `MODELO_EMB` configuráveis por variável de ambiente;
  padrão `http://ollama.henriqzimer.com.br`)
- CSVs `Manifestacoes_Ouvidoria_*.csv` (Fala.BR/CGU, dados abertos) em `dados/` (ou em outra pasta via `DADOS_DIR`);
  não versionados por causa do tamanho (2 GB): https://www.gov.br/cgu/pt-br/acesso-a-informacao/dados-abertos/arquivos/ouvidoria
- HTML das normas em `normas/` (Planalto)

## Execução
```
python 01_preparar_base.py     # EDA, agregados e amostra de 90 casos
python 02_indexar_normas.py    # chunking por artigo + embeddings (326 trechos)
python 03_pipeline.py          # relato sintético + versões A e B (~35 min)
python 04_avaliar.py           # métricas, gráficos, exemplos, planilha manual
python 05_sumarizar.py         # sumarização agregada da base completa
node gerar_deck.js             # gera apresentacao.pptx (npm install pptxgenjs jszip)
streamlit run app.py           # interface de demonstração (pip install streamlit)
```
Resultados em `saida/`. O `saida/agregado.csv` (47 MB) não é versionado: rode a etapa 1 para gerá-lo antes da interface.
`saida/diagrama_pipeline.html` é o diagrama interativo do pipeline.

## Limitações conhecidas
- Os CSVs não trazem o texto da manifestação: o relato é sintético, gerado pelo próprio modelo.
- O rótulo de prioridade é uma regra (tipo + sensibilidade do assunto), não verdade humana.
- A sumarização agregada pode conter números imprecisos; os indicadores confiáveis são os calculados em código.
