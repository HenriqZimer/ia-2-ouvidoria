# Exemplos qualitativos

## Acerto de prioridade (caso 1)
- **Tipo/Assunto:** Solicitação / Transporte Rodoviário
- **Órgão:** Agência Nacional de Transportes Terrestres
- **Prioridade de referência:** média

**Relato (sintético):** Aqui no meu bairro, tá difícil pegar ônibus direto pra cidade, só tem horários ruins e muita espera. Já fui várias vezes e voltei pra casa sem chegar nem perto do destino. Queremos um transporte mais organizado, sem essas rotas tortas e horários que nem a gente consegue acompanhar.

**A (sem RAG)** prioridade=média
> Prezado cidadão, agradecemos sua manifestação sobre o transporte rodoviário em seu bairro. A Agência Nacional de Transportes Terrestres (ANTT) monitora e fiscaliza o setor, e sua sugestão será encaminhada à concessionária responsável para análise. A legislação vigente, a Lei nº 12.587/2011, art. 2º, prevê a necessidade de serviços públicos eficientes e acessíveis. Pedimos paciência enquanto se busca melhoria contínua. Agradecemos sua participação e esperamos sua colaboração em futuras iniciativas.

**B (com RAG)** prioridade=média
> Prezado cidadão, agradecemos sua manifestação sobre o transporte rodoviário em seu bairro. A Agência Nacional de Transportes Terrestres está empenhada em promover a melhoria da oferta de serviços, conforme o disposto na Lei 13.460/2017, que assegura direito à adequada prestação dos serviços públicos. Sua solicitação será encaminhada à autoridade responsável para análise e acompanhamento. Agradecemos sua participação e reforçamos nosso compromisso com a acessibilidade e a qualidade do transporte público.

**Trechos recuperados:** Decreto 9.492/2018 art. 20; Lei 12.527/2011 art. 10; Lei 13.460/2017 art. 5; Lei 14.129/2021 art. 14

## Divergência de prioridade (caso 6)
- **Tipo/Assunto:** Reclamação / Energia
- **Órgão:** Agência Nacional de Energia Elétrica
- **Prioridade de referência:** média

**Relato (sintético):** Essa conta de luz tá me matando, tô pagando mais de R$500 por mês e ainda assim a conta não desce. Já liguei pra AGU e pra ANEEL, mas ninguém me respondeu direito. Vou ficar com isso até a gente ficar sem energia, hein?

**A (sem RAG)** prioridade=alta
> Prezado cidadão, compreendemos sua preocupação com o custo da conta de energia e a falta de atendimento. A ANEEL é o órgão responsável por regular o setor e pode ser contatada via seu site ou telefone 0800 77 00 123. Você também pode acessar o portal da AGU para denúncias ou buscar assistência jurídica gratuita. Sua situação é importante e estamos aqui para apoiar. Não se desespere — há meios legais e institucionais para resolver isso.

**B (com RAG)** prioridade=alta
> Prezado cidadão, sua manifestação foi recebida e estamos tomando providências imediatas. A ANEEL é responsável pela regulação do setor elétrico e já foi notificada sobre seu caso. Solicite, se possível, um atendimento presencial ou via telefone com o número 0800 77 00 00, que é o canal oficial de atendimento da agência. Não se preocupe, estamos aqui para ajudar. Sua segurança e bem-estar são nossas prioridades.

**Trechos recuperados:** Lei 12.527/2011 art. 15; Lei 12.527/2011 art. 12; Lei 13.460/2017 art. 9; Lei 12.527/2011 art. 16

## Baseline cita norma inexistente no corpus (caso 3)
- **Tipo/Assunto:** Denúncia / Sistema Penitenciário
- **Órgão:** Agência Estadual de Administração do Sistema Penitenciário - AGEPEN
- **Prioridade de referência:** alta

**Relato (sintético):** Fiquei sabendo que em alguns presídios daqui a situação tá piorando, com falta de comida, remédio e até água corrente. A gente tá tentando denunciar, mas parece que ninguém tá ligando. A gente quer ver mudança, não só na boca dos chefes, mas na realidade dos presos.

**A (sem RAG)** prioridade=alta
> Cidadão, sua denúncia é recebida com seriedade e compromisso. A AGEPEN tem o dever legal de garantir os direitos fundamentais dos presos, conforme o art. 30 da Lei nº 11.996/2009, que assegura alimentação, medicamentos e condições mínimas de saúde. Sua preocupação é válida e nossa atuação se dará com urgência. Agradecemos sua participação cidadã e reforçamos que a justiça e a dignidade devem prevalecer, mesmo dentro das penitenciárias. Continue informando, pois sua voz é essencial para a mudança.

**B (com RAG)** prioridade=alta
> Cidadão, seu relato foi recebido com a máxima atenção. A denúncia sobre falta de alimentos, medicamentos e água nos presídios é considerada de alta prioridade, pois envolve risco à saúde e dignidade humana. Já foi encaminhada à AGEPEN e aos órgãos apuratórios competentes para investigação imediata. Agradecemos sua denúncia e reforçamos que a mudança só será real se a administração pública agir com responsabilidade. Ficaremos atentos ao andamento do caso e, se necessário, atualizaremos seu acompanhamento.

**Trechos recuperados:** Decreto 9.492/2018 art. 22; Decreto 9.492/2018 art. 20; Decreto 9.492/2018 art. 16; Decreto 9.492/2018 art. 3
