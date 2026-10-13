# Contrato de integração — proposta v1

Somente a infraestrutura e funções de Fernando estão implementadas. Os contratos dos colegas são pontos explícitos de integração e continuam levantando `NotImplementedError`. Cada responsável implementa, documenta e testa seu próprio módulo.

## Registro base

CSV UTF-8 com exatamente estes campos, em qualquer ordem, sem cabeçalho duplicado. `dados.carregar(caminho)` retorna lista de dicionários ordenada por `(ciclo,id)`.

| Campo | Tipo após leitura | Domínio/unidade |
|---|---|---|
| id | int | Único, positivo |
| ciclo | int | Positivo; ordem temporal, duração não definida |
| modulo | str | Não vazio, nome legível |
| tipo | str | Não vazio; classificação descritiva |
| codigo_sensor | int | Decimal não negativo |
| carga_pct | float | Finito, 0–100% |
| latencia_observada_ms | float | Finito, não negativo, ms; zero é permitido |
| tensao_v | float | Finito, não negativo, V |
| corrente_a | float | Finito, não negativo, A; zero é permitido |
| status | str | ativo / alerta / manutencao |
| mensagem | str | Não vazia, texto descritivo da simulação |

Fernando não cria previsões, erros ou prioridades pré-calculados no CSV. Consulta básica por trecho de nome/ciclo não substitui o requisito de trie. Código hexadecimal para consulta proposta: `format(codigo_sensor, 'X')`, sem `0x`.

## Caetano — modulos/analise.py

`analisar(registros) -> {'registros': list[dict], 'resumo': dict}`.

Manter ids e campos de origem nos registros de saída; acrescentar `latencia_prevista_ms`, `erro_absoluto_ms` e `erro_relativo` (fração, ou None quando referência zero). Documentar denominador adotado, tolerâncias, limpeza, divisão de dados, modelo, métricas e unidades. O resumo conterá o modelo ou parâmetros necessários à estimativa, além dos indicadores e resultados calculados. Não usar saídas derivadas como atributos de treino. Definir e documentar treino/validação/teste com separação adequada; os ciclos 1–18, 19–24 e 25–30 são uma possibilidade para esta base, não ajuste obrigatório imposto por Fernando.

`prever(carga_pct, resumo) -> float` em ms. O menu valida entrada finita 0–100%; Caetano deve documentar faixa de treino, extrapolação e limitações e validar saídas do modelo. O objeto resumo deve ser serializável em JSON ou suas estruturas devem ser adaptadas por acordo do grupo.

## Joedson — modulos/alertas.py

`priorizar(registros_analisados) -> fila`.

A fila disponibiliza `inserir(alerta)`, `retirar() -> dict` e `__len__() -> int`. O alerta mantém `id`, `modulo`, `ciclo` e acrescenta `prioridade`, `justificativa`; campos adicionais podem ser definidos/documentados por Joedson. Definir limiar, criticidade, desempate e comportamento de fila vazia (proposta: `IndexError`). O menu verifica tamanho e demonstra uma retirada do mais urgente. Heapify-up/down e explicação da vantagem sobre lista são responsabilidade do módulo, ainda pendente.

Depende da análise para usar os erros. Pode ser preparado com fixtures sintéticas de mesmo esquema, sem esperar o modelo final. Discussão de sensores, monitoramento, redundância, automação, manutenção preditiva e microrredes deve partir dos resultados reais depois da integração.

## Mylena — modulos/consultas.py

`construir_indice(registros) -> trie`; `trie.buscar(prefixo) -> list[int]`.

Retornar **ids do campo id**, não posições na lista. Proposta: indexar módulo e código hexadecimal; ignorar caixa/acentos de nomes; prefixo ausente retorna lista vazia, vazio retorna todos os ids; não duplicar resultados. O menu mapeia os ids de volta aos registros e preserva a ordem de ciclo/id. A implementação efetiva da trie e seus testes/documentação são de Mylena. Ela também documenta a reflexão social/cultural/sustentável conectada ao sistema, com pelo menos três aspectos do enunciado.

## Fernando — infraestrutura

`Aplicacao` carrega dados, encaminha cópias independentes aos módulos e guarda o resultado da análise bem-sucedida para previsão/heap. Recarregar dados limpa esse cache. Resultado de análise precisa ter registros como lista e resumo como dicionário. A integração não deve alterar os dados originais; cada módulo valida seus próprios resultados e preserva o contrato.

`converter_codigo(int) -> dict`: decimal, binario, hexadecimal. `calcular_eletricidade(V,A) -> dict`: potencia_w, resistencia_equivalente_ohm (None se I=0). Resistência é apenas hipótese equivalente resistiva, não modelo de um transmissor real.

## Verificação antes de integrar

Cada responsável entrega função executável, teste e documentação do próprio módulo; o teste do menu com mocks confirma somente passagem de argumentos. Depois, todos executam suas suítes juntas e fazem uma demonstração integrada. Conferir ausência de vazamento treino/teste, ordem de urgência, ids da trie, unidades e explicação das limitações. Consolidar o relatório em conjunto, sem atribuir sua escrita à Mylena. Nenhuma parte de colegas é declarada pronta neste repositório.
