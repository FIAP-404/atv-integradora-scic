# Roteiro do vídeo — SCIC (até 5 minutos)

Narração única (Caetano), com demonstração ao vivo no terminal. São cerca de 440 palavras escritas, umas 500 quando os números são falados por extenso. Somando uns 50 s de digitação e trocas de cena, o vídeo dá **4min15** num ritmo normal (145 palavras/min) e **4min40** num ritmo calmo (130 palavras/min). Os tempos das cenas abaixo usam o ritmo calmo. Os números falados foram arredondados de propósito ("quase 92%"), mas continuam corretos; os valores exatos aparecem na tela. Todos saíram da execução real do código atual da `main`.

## Antes de gravar (checklist)

1. `git pull` na pasta do projeto, para gravar com o código final.
2. Abrir **dois terminais** na pasta do projeto, com fonte grande (zoom de 150% ou mais):
   - **Terminal A:** vai rodar o menu.
   - **Terminal B:** vai rodar a demonstração da análise.
3. No PowerShell, nos dois terminais, rodar uma vez `$env:PYTHONIOENCODING="utf-8"` para evitar erro com o símbolo Ω.
4. Ensaiar uma vez com cronômetro. Se passar de 4min45, corte primeiro a frase do log de n no heap e depois a do registro 161.
5. Gravar a tela e o microfone, com OBS ou com o Xbox Game Bar (`Win + Alt + R`).

---

## Cena 1 — Abertura (0:00–0:20)

**Tela:** README do repositório no GitHub ou slide com os nomes.

> Oi, eu sou o Caetano Bona, e esse é o SCIC, o Sistema de Comunicação Interplanetária da Colônia Aurora Siger. É o projeto integrador da Fase 6 da FIAP, que eu fiz com o Fernando Motta, o Joedson Souza e a Mylena Torquato.

## Cena 2 — Dados, bases numéricas e eletricidade (0:20–1:15) · parte de Fernando

**Terminal A:**
```
python codigo_fonte.py
```
Digitar `2`, depois `Comunicação`, depois `1`.

> A base é a parte do Fernando. São 180 registros de seis módulos em 30 ciclos. A entrada é esse CSV, validado campo por campo, e a saída, o terminal.

Digitar `3`, depois `3`.

> O código do sensor é 192 em decimal. Em binário, um, um e seis zeros, e em hexadecimal, C zero. Com 12 volts e 0,74 ampère, tensão vezes corrente dá quase 9 watts.

## Cena 3 — Indicadores, erros, previsão e métricas (1:15–2:55) · parte de Caetano

**Terminal B:**
```
python -c "from dados import carregar; from modulos.analise import demonstrar; demonstrar(carregar('dados_aurora_siger.csv'))"
```

> A minha parte foi a análise. Quase 92% dos registros estão em operação normal, e a latência média fica em uns 190 milissegundos.
>
> Para prever a latência pela carga, separei os ciclos por tempo em treino, validação e teste, e tirei os picos do treino.
>
> A regressão deu latência igual a 1,79 vezes a carga, mais 82 milissegundos. Na validação ela errou uns 8 milissegundos, contra 43 de quem só chuta a média.

*(Rolar até as métricas.)*

> No teste, em operação normal, o MAE foi 5,7 e o RMSE 7,7 milissegundos, com R quadrado de 0,96. Mas com os picos o RMSE sobe para quase 22, por isso não dá pra olhar um número só. No registro 161, o erro relativo chega a quase 35%, e é isso que marca a anomalia. Como float não é exato, arredondei tudo na precisão do CSV.

**Terminal A:** digitar `5`, depois `70`.

> Com 70% de carga, a previsão é de uns 208 milissegundos. Acima de 95% seria extrapolação.

## Cena 4 — Heap de alertas e gestão inteligente (2:55–3:45) · parte de Joedson

**Terminal A:** digitar `6`.

> O max-heap é do Joedson. São 15 alertas. A nota junta status, importância do módulo, atraso acima do previsto e tempo de espera. O mais urgente é o registro 117, da Comunicação, com uns 89 pontos.
>
> Ele guarda o heap num vetor, e inserir ou retirar custa ordem de log de n. Com mil alertas, deu 17 mil comparações, contra quase 500 mil numa lista.
>
> Na gestão inteligente, com 80% da energia, a microrrede preserva os módulos essenciais, e a demanda cai de uns 48 para 37 watts.

## Cena 5 — Trie e reflexão (3:45–4:30) · parte de Mylena

**Terminal A:** digitar `7`, depois `com`.

> A busca é da Mylena. Ela fez uma trie que indexa o nome e o código hexadecimal, sem diferenciar acento nem maiúscula. "com" traz os 30 registros da Comunicação. O custo depende do tamanho do prefixo.
>
> Na reflexão, a gente falou de energia, cortando o desperdício antes do essencial. Falou dos saberes indígenas, que fizeram a gente rever o peso baixo da Agricultura. De inclusão, porque a busca aceita jeitos diferentes de escrever. E de transparência, com a palavra final sempre humana.

## Cena 6 — Encerramento (4:30–4:40)

**Terminal A:** digitar `0`.

> Como limitação, os dados são simulados e os pesos foram definidos pela equipe. Obrigado!

---

## Depois de gravar

1. Confira a duração: precisa ficar **abaixo de 5:00**.
2. Faça o upload no YouTube com visibilidade **Não listado**.
3. Abra o link numa janela anônima para confirmar que funciona.
4. Crie `link_video.txt` na raiz do projeto, só com a URL.
5. Monte o ZIP com `codigo_fonte.py`, `dados_aurora_siger.csv`, `relatorio_tecnico.pdf`, `README.md` e `link_video.txt`. Recomendo incluir também `dados.py`, `dispositivos.py`, `gerar_dados.py`, `modulos/` e `tests/`, porque o `codigo_fonte.py` depende deles para rodar.
6. Entregue no portal antes de **23h59 de hoje (13/10)**. Confira se os quatro integrantes estão no grupo 36.
