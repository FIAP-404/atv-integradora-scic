# Seção técnica de Caetano: indicadores, erros, previsão e métricas

Seção de Caetano para o relatório conjunto. Código em `modulos/analise.py`; testes em `tests/test_caetano.py` (24 testes, saída em `docs/testes_caetano.txt`); demonstração em `docs/exemplo_caetano.txt`. Usa somente a biblioteca padrão do Python, e as fórmulas foram escritas à mão para que cada passo possa ser explicado.

## 1. Indicadores operacionais

Os indicadores **descrevem** a base; eles não fazem previsão. `analisar` calcula sobre os 180 registros:

| Indicador | Valor | Leitura |
|---|---|---|
| Disponibilidade (status `ativo`) | 91,67 % (165 de 180) | 14 registros em alerta e 1 em manutenção |
| Latência média | 189,263 ms (mín. 100,224; máx. 323,304) | Atraso operacional típico do enlace |
| Latência média por módulo | de 177,634 ms (Suporte Médico) a 201,170 ms (Laboratório) | O Laboratório opera com mais carga média (60,88 %) e tem a maior latência |
| Alertas por módulo | 2 a 3 por módulo | Os picos estão espalhados; nenhum módulo concentra falhas |

## 2. Divisão dos dados

| Conjunto | Ciclos | Registros | Uso |
|---|---|---|---|
| Treino | 1–18 (60 % dos ciclos) | 108 | Calcular a reta |
| Validação | 19–24 (20 %) | 36 | Decidir se a reta é melhor que uma linha de base |
| Teste | 25–30 (20 %) | 36 | Medir o desempenho final, sem nenhuma decisão tomada a partir dele |

A divisão é **temporal**: o modelo nunca vê ciclos futuros, como aconteceria na colônia de verdade. As faixas são calculadas a partir dos ciclos presentes na base (60/20/20), então outra base carregada pelo menu também é dividida inteira; com menos de 3 ciclos a análise é recusada. A validação influencia o modelo de propósito, porque é ela que escolhe entre a reta e a linha de base. O teste, não: um teste automatizado triplica as latências dos ciclos 25–30 e confere que modelo e seleção continuam idênticos e que só as métricas de teste mudam, ou seja, que não há vazamento do teste para o modelo.

**Limpeza:** a reta é ajustada só com registros `ativo` do treino. Os 9 registros de pico ou manutenção do treino ficam fora do ajuste porque não representam a operação nominal: um pico soma cerca de 70 ms e puxaria a reta para cima. Esses registros **não são apagados**. Eles recebem previsão e erro como todos os outros, e o erro alto é justamente o que permite ao heap do Joedson identificá-los. O status é um campo de entrada da base, e nenhuma saída derivada (previsão ou erro) é usada como atributo de treino.

## 3. Modelo de previsão

Regressão linear simples por **mínimos quadrados**: a reta que minimiza a soma dos erros ao quadrado.

```
inclinação = Σ(x − x̄)(y − ȳ) / Σ(x − x̄)²        intercepto = ȳ − inclinação · x̄
```

Resultado: **latência prevista = 1,7945 × carga + 82,0437 ms**. Cada ponto percentual de carga acrescenta cerca de 1,8 ms de atraso.

Como os dados são sintéticos, dá para conferir o resultado com a regra do gerador do Fernando: 80 + 1,8 × carga + deslocamento do módulo (média de +2 ms) + ruído. O modelo recuperou ≈1,8 e ≈82 sem ter acesso a essa regra, o que indica que ele aprende a relação real e não o ruído.

**Validação:** a reta foi comparada com uma linha de base ingênua, que sempre prevê a média do treino. RMSE da reta: 8,315 ms; RMSE da linha de base: 43,066 ms. A reta foi escolhida. Se fosse pior que a média, o código usaria a média automaticamente (há um teste para esse caso).

**`prever(carga_pct, resumo)`** lê a inclinação e o intercepto do `resumo`, que é serializável em JSON, e aplica a mesma fórmula usada em `analisar`. Um teste confere que `prever` reproduz exatamente a `latencia_prevista_ms` de todos os 180 registros. A função rejeita cargas fora de 0–100 % ou não finitas, um resumo sem modelo e saídas negativas ou não finitas. A faixa de carga do treino é **15,67 % a 94,95 %**. Fora dela, por exemplo em 100 % (261,494 ms), a previsão é uma **extrapolação**: nada garante que a relação continue linear com o sistema saturado.

## 4. Erros por registro

Cada registro de saída mantém todos os campos de origem e acrescenta:

- `latencia_prevista_ms`;
- `erro_absoluto_ms` = |observada − prevista|, em ms;
- `erro_relativo` = erro absoluto ÷ **latência observada**, como fração (0,05 = 5 %);
- `conjunto` (treino, validação ou teste).

**Denominador:** a observada é o valor real medido, por isso é a referência. Se ela for zero, a divisão não é definida e o erro relativo é `None`. O Joedson calcula o **seu** desvio em relação à prevista, com sinal, porque para ele importa se o atraso ficou acima do esperado. São duas perguntas diferentes, e cada módulo documenta a sua.

**Por que existem os dois erros:** 8 ms de erro pesam muito mais numa latência de 100 ms (8 %) do que numa de 300 ms (2,7 %). O erro absoluto mostra o tamanho do erro; o relativo permite comparar módulos e cargas diferentes. Exemplos do teste: o registro #145 (ativo) errou 0,312 ms (0,2 %); o #161 (pico no Suporte Médico) errou 75,521 ms (34,7 %).

## 5. Ponto flutuante

O computador guarda números reais em binário com precisão finita: `0.1 + 0.2` resulta em `0.30000000000000004`. Para lidar com isso:

- os coeficientes são arredondados a 4 casas **antes** de qualquer previsão, e previsões e erros a 3 casas, a mesma resolução da latência no CSV (0,001 ms). Mais casas seriam falsa precisão. Arredondar os coeficientes primeiro garante que a análise e `prever` deem o mesmo número;
- comparações com zero usam tolerância (`math.isclose`) em vez de `== 0`. Isso protege o denominador do erro relativo e o cálculo da reta, que não existe se todas as cargas forem iguais;
- R² fica `None` quando os valores observados não variam (divisão por zero).

## 6. Métricas

| Conjunto | Grupo | n | MAE (ms) | MSE (ms²) | RMSE (ms) | R² |
|---|---|---|---|---|---|---|
| Treino | nominal | 99 | 7,873 | 85,476 | 9,245 | 0,9456 |
| Treino | todos | 108 | 12,478 | 436,873 | 20,902 | 0,7710 |
| Validação | nominal | 33 | 7,250 | 69,139 | 8,315 | 0,9617 |
| Validação | todos | 36 | 12,610 | 500,003 | 22,361 | 0,7586 |
| **Teste** | **nominal** | 33 | **5,737** | 58,726 | **7,663** | **0,9618** |
| Teste | todos | 36 | 11,173 | 479,273 | 21,892 | 0,7632 |

- **MAE** (erro absoluto médio): em operação normal, a previsão erra em média cerca de 6 ms no teste.
- **MSE** (erro quadrático médio): eleva os erros ao quadrado, então pune erros grandes. A unidade é ms², o que dificulta a leitura direta.
- **RMSE** (raiz do MSE): volta para ms. Fica acima do MAE porque erros grandes pesam mais.
- **R²**: fração da variação da latência explicada pela carga. O valor 0,96 indica que a carga explica cerca de 96 % da variação em operação normal.

## 7. Interpretação e limitações

- **Nenhum número isolado prova a qualidade do modelo.** O R² de 0,96 só tem valor porque se repete em treino, validação e teste (não houve sobreajuste), porque a reta é cinco vezes melhor que a linha de base e porque os coeficientes batem com a regra conhecida dos dados.
- **Picos:** com os picos incluídos, o RMSE do teste sobe de 7,7 para 21,9 ms e o R² cai para 0,76. Isso não é defeito do modelo. A carga não explica um pico, e por isso um erro relativo alto funciona como sinal de anomalia, que é o que alimenta a prioridade do heap do Joedson.
- **RMSE ≈ 7,7 ms** é próximo do ruído do gerador (desvio de 5 ms) somado ao deslocamento por módulo, que o modelo ignora. Para melhorar seria preciso usar o módulo como entrada, mas o contrato `prever(carga, resumo)` recebe só a carga.
- A base tem 180 registros sintéticos. A latência é um atraso operacional didático e não modela propagação física entre planetas. Resultados com dados reais exigiriam nova validação.
