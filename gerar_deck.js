// Gera apresentacao.pptx. Requer: npm install pptxgenjs jszip
// Uso: node gerar_deck.js   (os números dos slides vêm de saida/metricas.json e saida/indicadores_orgaos.csv)
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");
const path = require("path");
const OUT = path.join(__dirname, "apresentacao.pptx");

const THEME = {
  name: "Ouvidoria IA",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1F2933", lt1: "FFFFFF", dk2: "12304A", lt2: "EEF3F6",
    accent1: "1B7F8C", accent2: "F2A900", accent3: "C0392B",
    accent4: "2E8B57", accent5: "6B7C8F", accent6: "5B8DB8",
    hlink: "1B7F8C", folHlink: "6B7C8F",
  },
};
const HEX = { teal: "1B7F8C", gray: "8A99A8", red: "C0392B", navy: "12304A", amber: "F2A900", ink: "1F2933" };


async function applyTheme(file, theme) {
  const zip = await JSZip.loadAsync(require("fs").readFileSync(file));
  const nome = Object.keys(zip.files).find((n) => /^ppt\/theme\/theme\d+\.xml$/.test(n));
  let xml = await zip.file(nome).async("string");
  for (const [k, v] of Object.entries(theme.colors)) {
    xml = xml.replace(new RegExp(`(<a:${k}>)[\\s\\S]*?(</a:${k}>)`), `$1<a:srgbClr val="${v}"/>$2`);
  }
  zip.file(nome, xml);
  require("fs").writeFileSync(file, await zip.generateAsync({ type: "nodebuffer" }));
}

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Ouvidoria com IA Generativa";
const C = pres.SchemeColor;
["Abertura","Retomada","Base e preparação","Solução implementada","Técnicas utilizadas","Demonstração","Resultados","Limitações","Conclusões"].forEach((title) => pres.addSection({ title }));

pres.defineSlideMaster({
  title: "CAPA",
  background: { color: HEX.navy },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.3, w: 5.6, h: 1.6,
      fontSize: 40, bold: true, color: C.background1, align: "left", valign: "top", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.05, w: 5.6, h: 1.1,
      fontSize: 18, color: C.background2, align: "left", valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTEUDO",
  background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.8,
      fontSize: 28, bold: true, color: C.text2, align: "left", valign: "middle", margin: 0 }, text: "" } },
    { text: { text: "Ouvidoria com IA Generativa  ·  Aplicação IA_Gen", options: {
      x: 0.5, y: 5.2, w: 6, h: 0.25, fontSize: 10, color: C.accent5, margin: 0, isTextBox: true } } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.25, fontSize: 10, color: C.accent5, align: "right" },
});

const T = (slide, text, o) => slide.addText(text, { isTextBox: true, margin: 0, color: C.text1, ...o });
const card = (slide, x, y, w, h, name) =>
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: C.background2 },
    line: { color: C.background2, width: 0 }, objectName: name });
const bubble = (slide, x, y, d, label, color, name) =>
  slide.addText(String(label), { shape: pres.ShapeType.ellipse, x, y, w: d, h: d, fill: { color: color || C.accent1 },
    color: C.background1, bold: true, fontSize: 14, align: "center", valign: "middle", margin: 0, objectName: name });
const chartBase = {
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  legendFontFace: "+mn-lt", titleFontFace: "+mn-lt",
  catAxisLabelColor: HEX.ink, valAxisLabelColor: HEX.ink, dataLabelColor: HEX.ink,
  catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, dataLabelFontSize: 12, legendFontSize: 12,
  valGridLine: { color: "D5DDE3", size: 0.5 }, catGridLine: { style: "none" },
  showTitle: true, titleFontSize: 14, titleColor: HEX.navy,
};
const nova = (titulo, notas, secao) => {
  const s = pres.addSlide({ masterName: "CONTEUDO", sectionTitle: secao });
  s.addText(titulo, { placeholder: "title" });
  s.addNotes(notas);
  return s;
};

// 1. Capa
{
  const s = pres.addSlide({ masterName: "CAPA", sectionTitle: "Abertura" });
  s.addText("Ouvidoria com IA Generativa", { placeholder: "title" });
  s.addText("Priorização e minuta de resposta com RAG sobre o Fala.BR, usando Qwen3 local", { placeholder: "body" });
  s.addShape(pres.ShapeType.ellipse, { x: 6.9, y: 1.1, w: 2.6, h: 2.6, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, objectName: "Circulo destaque" });
  T(s, "8,75 mi", { x: 6.9, y: 1.85, w: 2.6, h: 0.8, fontSize: 36, bold: true, color: C.background1, align: "center", valign: "middle", fontFace: "Cambria" });
  T(s, "manifestações reais", { x: 6.9, y: 2.6, w: 2.6, h: 0.4, fontSize: 14, color: C.background1, align: "center" });
  T(s, "Aplicação IA_Gen  ·  Entrega 27/10/2026", { x: 0.6, y: 4.7, w: 6, h: 0.3, fontSize: 14, color: C.accent2, bold: true });
  s.addNotes("0:00-0:30. Apresentação do grupo e do tema. Cada integrante se apresenta em uma frase.");
}

// 2. Problema
{
  const s = nova("O problema: respostas padronizadas",
    "0:30-1:30. Retomar o estudo de caso: ouvidorias públicas recebem milhões de manifestações e respondem em modelo copia e cola. Servidores sobrecarregados, gestores sem métricas confiáveis. Números vêm da base completa processada por nós.",
    "Retomada");
  const stats = [["8,75 mi", "manifestações registradas entre 2014 e 2026"],
                 ["24 dias", "tempo médio de resolução na base completa"],
                 ["1.777", "órgãos e 309 assuntos diferentes"]];
  stats.forEach(([n, l], i) => {
    const x = 0.5 + i * 3.1;
    card(s, x, 1.4, 2.8, 1.8, `Card estatistica ${i + 1}`);
    T(s, n, { x: x + 0.2, y: 1.55, w: 2.4, h: 0.8, fontSize: 40, bold: true, color: C.accent1, fontFace: "Cambria", valign: "middle" });
    T(s, l, { x: x + 0.2, y: 2.35, w: 2.4, h: 0.75, fontSize: 14, valign: "top" });
  });
  card(s, 0.5, 3.45, 9.0, 1.55, "Bloco objetivo");
  T(s, "Objetivo", { x: 0.75, y: 3.57, w: 8.5, h: 0.3, fontSize: 16, bold: true, color: C.text2 });
  T(s, "Apoiar o servidor com prioridade e minuta de resposta fundamentadas na legislação, mantendo a decisão final com o humano.",
    { x: 0.75, y: 3.9, w: 8.5, h: 0.5, fontSize: 14 });
  T(s, "Registro real  →  busca semântica  →  minuta + prioridade  →  validação humana",
    { x: 0.75, y: 4.5, w: 8.5, h: 0.35, fontSize: 14, bold: true, color: C.accent1 });
}

// 3. Base
{
  const s = nova("Base: 8,75 milhões de manifestações reais",
    "1:30-3:00. 13 CSVs do Fala.BR (CGU), 2014 a 2026, lidos em blocos por causa do tamanho (2 GB). O total de 8.752.638 registros bate com o estudo de caso. Achado central: o CSV não tem o texto da manifestação, só metadados. Por isso o relato usado no experimento é sintético, gerado pelo modelo a partir de tipo, órgão e assunto. 2026 é ano parcial.",
    "Base e preparação");
  s.addChart(pres.charts.BAR, [{ name: "Manifestações (milhões)", labels:
    ["2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026*"],
    values: [0.02, 0.05, 0.09, 0.16, 0.35, 0.93, 0.90, 1.11, 1.22, 1.15, 1.56, 1.21] }], {
    ...chartBase, x: 0.5, y: 1.25, w: 5.2, h: 3.65, barDir: "col", chartColors: [HEX.teal],
    title: "Manifestações por ano (milhões)", showLegend: false, showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.0", valAxisHidden: true, valGridLine: { style: "none" }, catAxisLabelFontSize: 11,
  });
  T(s, "* 2026 parcial  ·  Fonte: Fala.BR/CGU", { x: 0.5, y: 4.9, w: 5.2, h: 0.25, fontSize: 10, color: C.accent5 });
  const itens = [
    ["Preparação", "Leitura em blocos (latin-1, “;”), 26 colunas normalizadas e agregação por ano, tipo, órgão e assunto."],
    ["Amostra", "90 casos concluídos de 2025 e 2026, estratificados por tipo de manifestação."],
  ];
  let y = 1.3;
  itens.forEach(([h, t]) => {
    T(s, h, { x: 6.0, y, w: 3.5, h: 0.3, fontSize: 16, bold: true, color: C.text2 });
    T(s, t, { x: 6.0, y: y + 0.32, w: 3.5, h: 0.95, fontSize: 14, valign: "top" });
    y += 1.4;
  });
  card(s, 6.0, 4.1, 3.5, 0.85, "Alerta texto ausente");
  T(s, "O CSV não traz o texto da manifestação: o relato é sintético.", { x: 6.15, y: 4.15, w: 3.2, h: 0.75, fontSize: 14, bold: true, color: C.accent3, valign: "middle" });
}

// 4. Solução
{
  const s = nova("Solução: do registro à validação humana",
    "3:00-4:30. Ler o diagrama da esquerda para a direita. Preparo offline (tracejado roxo): os CSVs viram indicadores por órgão e as cinco leis são quebradas por artigo e indexadas com bge-m3, 326 trechos. A cada manifestação (verde): a consulta vai à busca semântica, que traz os 4 artigos mais próximos; junto com o histórico real do órgão eles chegam ao Qwen3-VL de 8 bilhões de parâmetros, rodando no Ollama dentro do Kubernetes. A saída em JSON vai para o servidor, que valida e decide. A linha cinza 'A: sem RAG' é o baseline: o modelo recebe só o relato. Tudo em infraestrutura própria, o que responde à preocupação com a LGPD. Versão interativa em saida/diagrama_pipeline.html.",
    "Solução implementada");
  s.addImage({ path: path.join(__dirname, "saida", "diagrama_pipeline.png"), x: 1.25, y: 1.15, w: 7.5, h: 3.78,
    altText: "Diagrama do pipeline: preparo offline dos CSVs e das normas, busca semântica, Qwen3-VL local, sugestão e validação humana" });
  T(s, "Infraestrutura própria: Ollama no Kubernetes, RTX 3050 de 8 GB. Os textos não saem da instituição (LGPD).",
    { x: 0.5, y: 4.95, w: 9.0, h: 0.25, fontSize: 12, color: C.accent5, align: "center" });
}

// 5. Técnicas
{
  const s = nova("Quatro técnicas, um ciclo completo",
    "4:30-6:00. Cada técnica resolve uma parte do ciclo: priorização estruturada vira dado para roteamento; RAG dá base normativa; geração condicionada produz o rascunho com regras no prompt; sumarização agregada revela gargalos para a gestão. Importante: a sumarização usa números calculados em código.",
    "Técnicas utilizadas");
  const tec = [["Priorização estruturada", "Saída em JSON com alta, média ou baixa e uma justificativa de uma frase."],
               ["RAG com embeddings", "Chunking por artigo, busca por similaridade e os 4 trechos mais próximos no contexto."],
               ["Geração condicionada", "Minuta em segunda pessoa, sem inventar prazos, citando só o contexto recuperado."],
               ["Sumarização agregada", "Indicadores calculados em código na base inteira; o LLM apenas redige o resumo."]];
  tec.forEach(([h, t], i) => {
    const x = i % 2 === 0 ? 0.5 : 5.15, y = i < 2 ? 1.35 : 3.2;
    card(s, x, y, 4.35, 1.65, `Tecnica ${i + 1}`);
    bubble(s, x + 0.2, y + 0.2, 0.5, i + 1, C.accent1, `Numero tecnica ${i + 1}`);
    T(s, h, { x: x + 0.9, y: y + 0.18, w: 3.3, h: 0.4, fontSize: 16, bold: true, color: C.text2, valign: "middle" });
    T(s, t, { x: x + 0.9, y: y + 0.62, w: 3.3, h: 0.95, fontSize: 14, valign: "top" });
  });
}

// 6. Demonstração
{
  const s = nova("Demonstração: o mesmo caso, duas versões",
    "6:00-7:30. Caso 3 da amostra: denúncia sobre o sistema penitenciário. Mostrar entrada, saída A e saída B. A versão A cita uma lei com artigo que não está no corpus e não conseguimos verificar. A versão B não cita lei nenhuma e encaminha. Prompt completo está em 03_pipeline.py. Resumimos o relato para caber.",
    "Demonstração");
  const cols = [[0.5, 2.7, "Entrada", C.text2, "Relato sintético: falta de comida, remédio e água em presídios. Tentamos denunciar, mas ninguém dá atenção."],
                [3.4, 3.0, "A: sem RAG", C.accent5, "Prioridade: alta.\nCita “art. 30 da Lei 11.996/2009”, fora do corpus e sem verificação possível."],
                [6.6, 2.9, "B: com RAG", C.accent1, "Prioridade: alta.\nNão cita lei; encaminha à AGEPEN e aos órgãos apuratórios."]];
  cols.forEach(([x, w, h, cor, t], i) => {
    card(s, x, 1.3, w, 2.95, `Coluna demo ${i + 1}`);
    T(s, h, { x: x + 0.2, y: 1.4, w: w - 0.4, h: 0.4, fontSize: 16, bold: true, color: cor });
    T(s, t, { x: x + 0.2, y: 1.85, w: w - 0.4, h: 2.3, fontSize: 14, valign: "top" });
  });
  T(s, "Caso 3  ·  Denúncia  ·  Sistema Penitenciário  ·  Entrada: tipo, órgão, assunto e relato. Saída: JSON com prioridade, justificativa e minuta.",
    { x: 0.5, y: 4.45, w: 9.0, h: 0.6, fontSize: 12, color: C.accent5, valign: "top" });
}

// 7. Resultado 1: priorização
{
  const s = nova("Resultado 1: o RAG não ajudou a priorizar",
    "7:30-9:00. Avaliação em 90 casos contra o gabarito por regra (tipo + sensibilidade do assunto). A: 82,2% de concordância e F1 0,87. B: 67,8% e F1 0,72. Nenhum erro passou de um nível. O padrão do B: rebaixou 19 dos 37 casos de prioridade alta para média, contra 7 do A. Hipótese, não testada: o contexto normativo e o histórico de atraso deixam o modelo mais conservador. Ressalva: o gabarito é uma regra, não um julgamento humano.",
    "Resultados");
  s.addChart(pres.charts.BAR, [
    { name: "A: sem RAG", labels: ["Concordância (%)", "F1 macro (%)"], values: [82.2, 86.6] },
    { name: "B: com RAG", labels: ["Concordância (%)", "F1 macro (%)"], values: [67.8, 72.2] }], {
    ...chartBase, x: 0.5, y: 1.25, w: 5.2, h: 3.75, barDir: "col", chartColors: [HEX.gray, HEX.teal],
    title: "Prioridade vs. regra de referência (90 casos)", showLegend: true, legendPos: "b", showValue: true,
    dataLabelPosition: "outEnd", dataLabelFormatCode: "0", valAxisMinVal: 0, valAxisMaxVal: 100, valAxisHidden: true, valGridLine: { style: "none" },
  });
  T(s, "51%", { x: 6.0, y: 1.3, w: 3.5, h: 0.9, fontSize: 48, bold: true, color: C.accent3, fontFace: "Cambria", valign: "middle" });
  T(s, "dos casos de prioridade alta foram rebaixados para média pela versão B (19 de 37). No baseline foram 19% (7 de 37).",
    { x: 6.0, y: 2.2, w: 3.5, h: 1.2, fontSize: 14, valign: "top" });
  T(s, "Nenhum erro passou de um nível. O gabarito é uma regra por tipo e assunto, não um julgamento humano.",
    { x: 6.0, y: 3.6, w: 3.5, h: 1.2, fontSize: 14, color: C.accent5, valign: "top" });
}

// 8. Resultado 2: fundamentação
{
  const s = nova("Resultado 2: o RAG fundamenta as citações",
    "9:00-10:30. Medimos quantas citações de lei e artigo existem no corpus indexado e estavam no contexto recuperado. A: 3 de 46 (6,5%). B: 31 de 32 (96,9%). A diferença é grande e é o principal ganho do RAG. Mas a métrica só vê leis e artigos: contatos e promessas de ação são inventados em ambas as versões (por exemplo telefones da ANEEL). Contagem por regex: promessas de ação já realizada em 7 minutas de A e 6 de B.",
    "Resultados");
  s.addChart(pres.charts.BAR, [{ name: "Citações fundamentadas (%)", labels: ["A: sem RAG", "B: com RAG"], values: [6.5, 96.9] }], {
    ...chartBase, x: 0.5, y: 1.25, w: 4.6, h: 3.75, barDir: "col", chartColors: [HEX.gray, HEX.teal],
    title: "Citações presentes no corpus indexado (%)", showLegend: false, showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.0", valAxisMinVal: 0, valAxisMaxVal: 110, valAxisHidden: true, valGridLine: { style: "none" },
  });
  T(s, "46 vs 32", { x: 5.4, y: 1.3, w: 4.1, h: 0.8, fontSize: 40, bold: true, color: C.accent1, fontFace: "Cambria", valign: "middle" });
  T(s, "citações de lei e artigo em A e em B. Em B, 31 das 32 estão no contexto recuperado.",
    { x: 5.4, y: 2.1, w: 4.1, h: 0.9, fontSize: 14, valign: "top" });
  card(s, 5.4, 3.2, 4.1, 1.75, "Alerta alucinacao residual");
  T(s, [{ text: "Alucinação residual", options: { bold: true, breakLine: true, color: C.accent3 } },
        { text: "Em ambas as versões surgiram telefones inventados e promessas de ação já realizada (7 minutas em A, 6 em B).", options: {} }],
    { x: 5.55, y: 3.3, w: 3.8, h: 1.55, fontSize: 14, valign: "top" });
}

// 9. Resultado 3: sumarização
{
  const s = nova("Resultado 3: sumarização da base inteira",
    "10:30-12:00. Indicadores calculados em código sobre os 8,75 milhões de registros, ano de 2025, órgãos com pelo menos 5 mil manifestações. Atraso concentrado em órgãos municipais; os ministérios ficam perto de zero. O resumo escrito pelo LLM trouxe erros de número: disse 70% de reclamações quando o dado dá cerca de 49%, e citou um tempo médio federal que não estava na tabela. Decisão de projeto: números vêm do código, o modelo só redige.",
    "Resultados");
  s.addChart(pres.charts.BAR, [{ name: "% com atraso", labels: ["Prefeitura Municipal", "Câmara Municipal", "Prefeitura", "Min. da Saúde", "Min. Previdência", "Min. Trabalho"],
    values: [16.5, 14.4, 11.2, 0.6, 0.1, 0.1] }], {
    ...chartBase, x: 0.5, y: 1.25, w: 5.2, h: 3.75, barDir: "bar", chartColors: [HEX.teal], catAxisOrientation: "maxMin",
    title: "Manifestações respondidas com atraso, 2025 (%)", showLegend: false, showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.0", valAxisMinVal: 0, valAxisMaxVal: 20, valAxisHidden: true, valGridLine: { style: "none" }, catAxisLabelFontSize: 11,
  });
  T(s, "Atraso se concentra em órgãos municipais; ministérios federais ficam perto de zero.", { x: 6.0, y: 1.3, w: 3.5, h: 1.2, fontSize: 14, bold: true, color: C.text2, valign: "top" });
  card(s, 6.0, 2.75, 3.5, 2.2, "Alerta resumo LLM");
  T(s, [{ text: "O resumo do LLM errou números", options: { bold: true, breakLine: true, color: C.accent3 } },
        { text: "Disse 70% de reclamações (o dado dá cerca de 49%). Por isso o código calcula e o modelo só redige.", options: {} }],
    { x: 6.15, y: 2.85, w: 3.2, h: 2.0, fontSize: 14, valign: "top" });
}

// 10. Limitações
{
  const s = nova("Limitações e riscos observados",
    "12:00-13:30. Ser direto sobre o que não conseguimos afirmar. O relato sintético é gerado pelo mesmo modelo que o interpreta. O gabarito é regra. Amostra de 90 casos em uma execução. E a infraestrutura teve um pod reiniciado por falta de memória (limite de 8 GiB), que ampliamos para 16 GiB.",
    "Limitações");
  const itens = [["Relato sintético", "O mesmo modelo gera e interpreta o texto; a base real não traz relatos."],
                 ["Gabarito por regra", "A prioridade mede alinhamento a tipo e assunto, não julgamento humano."],
                 ["Alucinação residual", "Telefones e promessas de ação inventados, mesmo com RAG."],
                 ["Amostra pequena", "90 casos, uma execução, sem intervalo de confiança."],
                 ["Infraestrutura", "Janela de 4 a 8 mil tokens (não os 32 mil nominais) e pod sem memória com 8 GiB, ampliado para 16."]];
  itens.forEach(([h, t], i) => {
    const y = 1.3 + i * 0.74;
    card(s, 0.5, y, 9.0, 0.64, `Linha limitacao ${i + 1}`);
    bubble(s, 0.65, y + 0.12, 0.4, i + 1, C.accent3, `Numero limitacao ${i + 1}`);
    T(s, [{ text: h + ".  ", options: { bold: true, color: C.text2 } }, { text: t, options: {} }],
      { x: 1.25, y, w: 8.1, h: 0.64, fontSize: 14, valign: "middle" });
  });
}

// 11. Conclusões
{
  const s = nova("Conclusões e melhorias futuras",
    "13:30-15:00. Responder às três perguntas do enunciado: como se comporta (funciona de ponta a ponta, localmente), se atende (em parte: fundamenta bem, não melhorou a prioridade), aprendizados (validação humana segue obrigatória; números sempre calculados em código). Depois, melhorias futuras. Reservar tempo final para perguntas.",
    "Conclusões");
  card(s, 0.5, 1.3, 4.35, 3.7, "Coluna conclusoes");
  T(s, "O que concluímos", { x: 0.7, y: 1.4, w: 4.0, h: 0.4, fontSize: 18, bold: true, color: C.text2 });
  T(s, [
    { text: "Funciona de ponta a ponta, em infraestrutura própria", options: { bullet: true, breakLine: true } },
    { text: "Atende em parte: fundamenta citações (97%), mas não melhorou a prioridade", options: { bullet: true, breakLine: true } },
    { text: "Validação humana segue obrigatória", options: { bullet: true } }],
    { x: 0.7, y: 1.9, w: 4.0, h: 3.0, fontSize: 14, valign: "top", paraSpaceAfter: 8 });
  card(s, 5.15, 1.3, 4.35, 3.7, "Coluna melhorias");
  T(s, "Melhorias futuras", { x: 5.35, y: 1.4, w: 4.0, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
  T(s, [
    { text: "Usar texto real: pedidos de acesso à informação e Brasil Participativo", options: { bullet: true, breakLine: true } },
    { text: "Rótulos de prioridade feitos por servidores", options: { bullet: true, breakLine: true } },
    { text: "Calibrar a prioridade com exemplos no prompt", options: { bullet: true, breakLine: true } },
    { text: "Checar contatos e prazos da minuta automaticamente", options: { bullet: true } }],
    { x: 5.35, y: 1.9, w: 4.0, h: 3.0, fontSize: 14, valign: "top", paraSpaceAfter: 8 });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("ok", OUT);
})();
