# Seção técnica de Fernando — dados, menu, dispositivos e integração

Esta é a documentação da parte de Fernando, preparada com assistência de IA e sujeita à sua revisão. Não substitui o relatório técnico conjunto. Modelos, erros, métricas, heap, trie, gestão inteligente e reflexão social permanecem sob responsabilidade dos respectivos integrantes.

## Contexto e organização

O SCIC organiza telemetria operacional sintética da Aurora Siger. A base contém 180 registros de seis módulos (Habitação, Agricultura, Comunicação, Laboratório, Suporte Médico e Dados) ao longo de 30 ciclos. Cada linha identifica o registro, ciclo, módulo/tipo, código de sensor decimal, carga percentual, latência observada em ms, tensão em V, corrente em A, status e mensagem.

Os milissegundos representam atrasos operacionais didáticos dos módulos; não representam o tempo de propagação de sinais entre planetas. Não foi assumida distância física, velocidade de propagação ou infraestrutura real. Nenhum valor foi medido no mundo real.

O gerador usa semente 36: carga uniforme 15–95%; latência = 80 + 1,8×carga + deslocamento de módulo + ruído normal de desvio 5 ms + picos de 70 ms quando (ciclo+3×índice do módulo) é múltiplo de 13. Os deslocamentos, na ordem dos módulos acima, são 0, 8, −8, 4, −4 e 12 ms. A tensão é 12 V e a corrente é 0,35+0,005×carga, arredondada a quatro casas. Picos recebem status alerta; Dados no ciclo 17 recebe manutenção programada. Essas regras produzem cenários para análise posterior; não são um modelo de previsão treinado nem políticas de prioridade.

Os códigos de sensor são 160, 176, 192, 208, 224 e 240. A base original foi preservada; o gerador permite reproduzi-la em outro caminho e recusa sobrescrever um destino existente pela CLI. Latência prevista, erros e prioridade não foram preenchidos previamente: são produzidos pelos módulos integrados dos colegas.

## Leitura e validação

`csv.DictReader` converte CSV em dicionários; listas organizam a sequência temporal. A leitura valida esquema exato, número de colunas, textos obrigatórios, id único/positivo, ciclo positivo, código não negativo, números finitos/não negativos, carga ≤100% e status conhecido. Entradas inválidas falham com linha e motivo. A leitura não imputa medições e não remove anomalias silenciosamente. Latência e corrente zero são aceitas, exigindo tratamento adequado nos cálculos posteriores.

Registros são ordenados por ciclo/id. A consulta básica filtra trecho de nome e ciclo, sem alterar dados e sem se apresentar como trie. Ao carregar outro arquivo pelo menu, a troca só ocorre depois de validação bem-sucedida e invalida resultados anteriores; arquivo inválido preserva a base carregada.

## Entrada, saída, bases e eletricidade

Sensores/medidores de carga, latência, tensão e corrente poderiam originar registros. Aqui o CSV é entrada simulada. Terminal é saída para consulta; relatórios e outros arquivos poderiam exibir resultados na integração. Rede ou USB são interfaces conceituais para transporte local; não há dispositivo físico conectado.

No registro #1, Habitação/ciclo 1, código decimal 160 = binário 10100000 = hexadecimal A0. A representação é feita com formatação Python; não é endereço real de rede. Todos os códigos são identificadores didáticos não negativos.

A tensão 12 V e corrente 0,5565 A dão potência P=V×I=6,678 W. É potência elétrica de entrada, não potência radiada; perdas e eficiência de um transmissor não foram modeladas. Sem duração dos ciclos em horas, não se estima energia em Wh. Sob hipótese puramente resistiva, R=V/I≈21,5633 Ω neste registro; isso não afirma que um transmissor seja resistor ideal. Corrente zero produz potência zero e resistência equivalente indefinida (`None`), sem divisão por zero.

A aritmética usa floats; arredonda apenas a apresentação dos resultados e verifica finitude dos cálculos. A discussão de erros absoluto/relativo e métricas cabe ao módulo de Caetano; não foram criados resultados substitutos nesta etapa.

## Menu e integração

`codigo_fonte.py` carrega automaticamente a base ao lado do código e permite carregar outro CSV, consultar registros e exibir bases/eletricidade. Opções de análise, previsão, heap e trie chamam assinaturas documentadas em `docs/interfaces.md`. Todas essas interfaces estão implementadas: análise e previsão por Caetano, heap por Joedson e trie por Mylena. Fernando mantém a infraestrutura e os testes de integração, preservando os algoritmos dos colegas.

As funções dos colegas recebem cópias para preservar a base original. Análise bem-sucedida é guardada para previsão/heap e removida ao trocar dados. Resultado deve ser lista de registros enriquecidos e resumo como dicionário. Trie retorna ids públicos; a infraestrutura resolve esses ids para mostrar registros, eliminando repetição de resultados. Cada colega é responsável por validar seu retorno, testar e documentar seu próprio algoritmo.

## Evidências e limites

Comando da suíte completa: `python3 -m unittest discover -s tests -v` — **59 testes passaram** após a atualização dos dois testes de integração obsoletos. A saída está em `docs/testes_integrados.txt`. São 13 testes de Fernando, 24 de Caetano, 13 de Joedson e 9 de Mylena; as saídas individuais estão em `docs/testes_<integrante>.txt`.

Os 13 testes de Fernando cobrem dados, bases, eletricidade, recarga transacional, encaminhamento com mocks, CLI fora da pasta e a integração real da trie com o menu. A busca verifica ids esperados, caixa/acentos, hexadecimal, prefixo ausente/vazio e preservação dos registros. Mocks continuam verificando somente o encaminhamento, sem substituir os testes reais.

`python3 codigo_fonte.py --demo` produz `docs/exemplo_fernando.txt`: dados, consulta básica, bases e eletricidade. Análise, previsão, heap e trie são acessíveis pelo menu; `--demo` é apenas a demonstração curta.

Os três módulos estão integrados e o relatório conjunto está em `relatorio_tecnico.pdf`. A gravação do vídeo foi atribuída a Caetano. Ainda faltam sua URL real, validação da duração/visibilidade e inclusão de `link_video.txt` no ZIP antes da submissão. Nenhuma submissão foi realizada nesta revisão.
