# Contrato de integração — implementação atual

A infraestrutura de Fernando, a análise de Caetano, o heap de Joedson e a trie de Mylena estão implementados e integrados. A revisão de integração preserva os algoritmos e a responsabilidade de cada integrante.

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

**Implementado** (detalhes em `docs/relatorio_caetano.md`): divisão temporal de 60/20/20 dos ciclos presentes (nesta base, 1–18, 19–24 e 25–30); treino só com status `ativo`; reta escolhida contra a linha de base (média do treino) na validação; erro relativo com denominador na latência observada (`None` quando ela é zero); cada registro de saída também recebe `conjunto` (treino, validacao ou teste). O modelo fica em `resumo["modelo"]` (`inclinacao_ms_por_pct`, `intercepto_ms`, `faixa_treino_carga_pct`), e `prever` reproduz exatamente a `latencia_prevista_ms` dos registros.

## Joedson — modulos/alertas.py

`priorizar(registros_analisados) -> fila`.

A fila disponibiliza `inserir(alerta)`, `retirar() -> dict` e `__len__() -> int`. O alerta mantém `id`, `modulo`, `ciclo` e acrescenta `prioridade`, `justificativa`, `tipo`, `mensagem`, `nivel` e `essencialidade`. O max-heap usa heapify-up/down; retirar de fila vazia lança `IndexError`. Desempates usam essencialidade, ciclo e id. O menu demonstra a retirada do alerta mais urgente. A comparação com lista e a discussão de gestão inteligente estão implementadas e documentadas em `docs/relatorio_joedson.md`.

A demonstração recebe a análise real de Caetano; as fixtures isoladas dos testes de Joedson continuam próprias para verificar o heap independentemente do modelo.

## Mylena — modulos/consultas.py

`construir_indice(registros) -> trie`; `trie.buscar(prefixo) -> list[int]`.

Retornar **ids do campo id**, não posições na lista. Implementado: indexa módulo e código hexadecimal; ignorar caixa/acentos de nomes; prefixo ausente retorna lista vazia, vazio retorna todos os ids; não duplicar resultados. O menu mapeia os ids de volta aos registros e preserva a ordem de ciclo/id. A implementação efetiva da trie e seus testes/documentação são de Mylena. Ela também documenta a reflexão social/cultural/sustentável conectada ao sistema, com pelo menos três aspectos do enunciado.

## Fernando — infraestrutura

`Aplicacao` carrega dados, encaminha cópias independentes aos módulos e guarda o resultado da análise bem-sucedida para previsão/heap. Recarregar dados limpa esse cache. Resultado de análise precisa ter registros como lista e resumo como dicionário. A integração não deve alterar os dados originais; cada módulo valida seus próprios resultados e preserva o contrato.

`converter_codigo(int) -> dict`: decimal, binario, hexadecimal. `calcular_eletricidade(V,A) -> dict`: potencia_w, resistencia_equivalente_ohm (None se I=0). Resistência é apenas hipótese equivalente resistiva, não modelo de um transmissor real.

## Verificação integrada

Os 59 testes passaram após atualização dos testes obsoletos de Fernando. A evidência reproduzível está em `docs/testes_integrados.txt`; os testes de encaminhamento com mocks são distintos dos testes reais dos módulos. O relatório conjunto está em `relatorio_tecnico.pdf`. Vídeo e URL real continuam pendentes de Caetano; ver `PRE_ENTREGA.md`.
