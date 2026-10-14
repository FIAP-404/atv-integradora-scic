# Seção técnica de Joedson: heap, prioridades e gestão inteligente da comunicação

Seção de Joedson para o relatório conjunto. Código em `modulos/alertas.py`; testes em `tests/test_joedson.py`.

> **Resultados integrados.** Os números abaixo foram atualizados com a saída real de `analise.analisar`, de Caetano. A demonstração reproduzível está em `docs/exemplo_joedson.txt`; as fixtures unitárias originais permanecem isoladas nos testes.

## 1.4 Priorização de alertas com heap

### Representação

`priorizar(registros_analisados)` devolve uma `FilaAlertas`, conforme o contrato de `docs/interfaces.md`. A fila tem três operações: `inserir`, `retirar` e `len`.

Cada alerta é um **dicionário novo**, e os registros recebidos não são alterados. Ele guarda:

- `id`, `modulo`, `ciclo`, `tipo` e `mensagem`;
- `prioridade` (de 0 a 100) e `nivel` (CRÍTICO, ALTO, MÉDIO ou BAIXO);
- `essencialidade`;
- `justificativa`, com os motivos da nota em texto.

Um registro vira alerta quando atende a **pelo menos uma** destas condições:

- o status é `alerta` ou `manutencao`;
- a latência observada está **mais de 20 % acima** da prevista;
- a tensão está fora de **12 V ± 10 %**.

As duas últimas regras permitem que o monitoramento aponte problemas mesmo em módulos que ainda constam como "ativo".

### Critério de prioridade

| Critério | Pontos | Por quê |
|---|---|---|
| Status | alerta = 40, manutenção = 15 | O que já falhou vem antes do que está em manutenção |
| Essencialidade | suporte médico e comunicação = 25; habitação = 20; armazenamento = 15; agricultura = 10; laboratório = 5 | Suporte de vida e enlace sustentam a colônia |
| Latência acima do previsto | até 20, proporcional ao desvio relativo (50 % ou mais vale 20) | O desvio relativo compara módulos de escalas diferentes. O teto impede que o atraso, sozinho, passe à frente de tudo |
| Tensão fora de 12 V ± 10 % | 10 | Um problema elétrico pode derrubar o módulo |
| Ciclos aguardando | +1 por ciclo, até 5 | Evita que um alerta antigo fique esquecido |

O **desvio relativo** é `(observada − prevista) / prevista`, calculado a partir da `latencia_prevista_ms` de Caetano. O sinal é mantido porque só um atraso acima do previsto deve aumentar a prioridade. Se a prevista estiver ausente ou for zero, o critério vale 0, e a justificativa informa que a previsão está indisponível.

O **desempate** (`mais_urgente`) segue esta ordem: prioridade, depois essencialidade, depois o registro mais antigo e, por fim, o menor id. Com isso, a enfermaria vem antes dos dados quando as notas empatam.

### Organização no heap (Capítulo 4)

O heap segue a lógica do código em C da apostila:

- é um **vetor**, em que `len(vetor)` faz o papel de `n`;
- os índices são `2i+1` (filho esquerdo), `2i+2` (filho direito) e `(i−1)//2` (pai);
- a troca de posições usa uma variável `temp`;
- o **heapify-up** é feito na inserção, e o **heapify-down**, recursivo, na retirada da raiz;
- `construir_max_heap` reproduz o exemplo da apostila: `[35, 12, 90, 4, 77, 51, 23]` vira `[90, 77, 51, 4, 12, 35, 23]`.

Custos: inserir e retirar custam O(log n); consultar o topo custa O(1).

`FilaAlertas` é apenas a "casca" pedida pelo contrato do menu. Toda a lógica está nas funções de heap. Retirar de uma fila vazia lança `IndexError`, como propõe o contrato.

### Resultado integrado

Dos 180 registros, **15 viraram alertas**. O mais urgente, que fica na raiz do heap, é o **#117 Comunicação, ciclo 20, com 89,28 pontos**:

- status alerta: +40;
- comunicação: +25;
- latência 48 % acima do previsto: +19,28;
- aguardando: +5.

Em seguida vêm os picos do Suporte Médico (88,0 e 87,6 pontos).

O vetor não fica totalmente ordenado, porque o heap só garante que cada pai é mais urgente que os filhos. Mesmo assim, a raiz é sempre o mais urgente.

### Vantagem sobre uma lista simples

Numa lista sem ordem, achar o mais urgente exige percorrer tudo: O(n) por atendimento e O(n²) no total. No heap, o total fica em O(n log n). As comparações contadas pelo próprio módulo confirmam isso:

| n alertas | Heap | Lista | Lista ÷ heap | Mesma ordem? |
|---|---|---|---|---|
| 100 | 1.034 | 4.950 | 4,8× | sim |
| 1.000 | 17.029 | 499.500 | 29,3× | sim |
| 2.000 | 38.065 | 1.999.000 | 52,5× | sim |

## 1.7 Gerenciamento inteligente da comunicação

O módulo segue as três camadas do Capítulo 12:

- **Coleta:** os registros de sensores (latência, tensão e corrente).
- **Comunicação:** o enlace do módulo Comunicação.
- **Processamento:** o heap e as regras abaixo.

**Monitoramento contínuo.** `monitoramento_continuo` lê os 30 ciclos em ordem e insere cada anomalia na fila. Houve **0 detecções antecipadas** nesta base com o modelo integrado: todos os registros identificados já estavam marcados como alerta ou manutenção.

**Automação com validação humana.** `atender_proximo` mostra a justificativa e a ação sugerida, e pede a confirmação do operador com `input` (s/n). Se a ação for rejeitada, ou se a resposta for inválida, o alerta volta para a fila. A decisão final é sempre humana.

**Manutenção preditiva.** A análise acompanha o **desvio** da latência em relação à prevista, e não a latência bruta. Assim, uma variação normal de carga não é confundida com desgaste. Os passos são:

1. calcular a taxa por diferença finita regressiva;
2. confirmar a tendência só se o desvio subir por 3 ciclos seguidos, mais de 2 pontos percentuais por ciclo;
3. confirmada a tendência, projetar pelo **método de Euler** (Capítulo 6) até o desvio passar de 20 %.

Nesta base, **nenhum módulo tem tendência confirmada**. O Laboratório aparece como "pico recente, acompanhar". Isso é coerente com a geração dos dados: picos isolados, sem desgaste progressivo.

**Redundância.** O enlace de Comunicação teve **2 ciclos com anomalia em 30** e está normal no ciclo 30. A base tem um único enlace, então o sistema recomenda um **enlace reserva** como melhoria, justificada por essas anomalias recorrentes.

**Microrredes.** A demanda no ciclo 30 é a soma de P = V × I, cálculo de Fernando: **48,36 W**. Com 80 % disponível (38,69 W), por exemplo numa tempestade de poeira que reduz a geração solar, o módulo entra em contingência, à semelhança da operação ilhada do Capítulo 12:

- Suporte Médico, Comunicação e Habitação são preservados.
- Um **segundo heap**, com a regra "menos essencial primeiro", coloca em modo econômico o Laboratório (−4,83 W), os Dados (−3,52 W) e a Agricultura (−3,08 W).
- A demanda cai para **36,93 W**.

## Limitações

- Os pesos foram definidos pela equipe e deveriam ser validados com os responsáveis pelos módulos.
- A fila contém todos os alertas do histórico. Por isso, o critério de espera satura em 5 para alertas antigos.
- A projeção de Euler supõe taxa constante.
- A base tem um único enlace de comunicação, então a redundância fica como proposta.
- A redução para modo econômico é fixa, em 50 %.

## Evidências

- `python3 -m unittest discover -s tests -p test_joedson.py -v`: **13 testes passaram**, saída em `docs/testes_joedson.txt`.
- `python3 -m unittest discover -s tests -v`: **59 testes passaram**, saída em `docs/testes_integrados.txt`.
- Demonstração integrada: `python3 -c "from dados import carregar; from modulos import analise,alertas; alertas.demonstrar(analise.analisar(carregar('dados_aurora_siger.csv'))['registros'])"`. Saída em `docs/exemplo_joedson.txt`.
