# SCIC — Sistema de Comunicação Interplanetária

Projeto integrador da Fase 6 da FIAP. O protótipo simula o monitoramento da colônia Aurora Siger com dados operacionais sintéticos, análise de latência, previsão, priorização de alertas e busca eficiente por prefixo.

## Funcionalidades

- Leitura, validação e consulta de registros em CSV, com opção para carregar outra base.
- Geração reproduzível de dados sintéticos para seis módulos da colônia.
- Conversão de códigos de sensores entre decimal, binário e hexadecimal.
- Cálculos de potência elétrica (`P = V × I`) e resistência equivalente sob hipótese resistiva.
- Indicadores operacionais e análise de latência, incluindo erros absoluto e relativo, ponto flutuante e métricas MAE, MSE, RMSE e R².
- Previsão de latência por carga com modelo simples e seleção validada contra uma linha de base.
- Fila de prioridade implementada com max-heap, critérios explicáveis, desempate e demonstração comparativa com lista.
- Trie para pesquisar prefixos de nomes de módulos e códigos hexadecimais.
- Exemplos de monitoramento contínuo, manutenção preditiva, redundância e gestão de microrrede.

## Requisitos

Python 3.10 ou superior. O projeto utiliza apenas a biblioteca padrão do Python.

## Como executar

Na pasta do projeto:

```bash
python codigo_fonte.py
```

Para executar uma demonstração rápida sem abrir o menu:

```bash
python codigo_fonte.py --demo
```

Para carregar um arquivo CSV diferente:

```bash
python codigo_fonte.py --dados caminho/para/dados.csv
```

O menu oferece carregamento de dados, consulta por módulo e ciclo, detalhes de dispositivos, análise, previsão, fila de alertas e busca por prefixo. A base padrão `dados_aurora_siger.csv` é localizada em relação ao próprio código, independentemente da pasta de onde o comando for executado.

## Dados

`dados_aurora_siger.csv` contém os registros simulados utilizados pela aplicação. Para gerar outra base:

```bash
python gerar_dados.py --destino caminho/para/novo_arquivo.csv
```

O gerador recusa sobrescrever um arquivo existente. A função `gerar()` também pode ser usada diretamente em outros scripts.

## Estrutura do projeto

| Caminho | Conteúdo |
|---|---|
| `codigo_fonte.py` | Aplicação principal, integração dos módulos, demonstração e menu interativo. |
| `dados.py` | Leitura, validação e consulta dos registros. |
| `dados_aurora_siger.csv` | Base operacional simulada. |
| `gerar_dados.py` | Geração reproduzível da base sintética. |
| `dispositivos.py` | Conversões numéricas e cálculos elétricos. |
| `modulos/analise.py` | Indicadores, divisão temporal, previsão e métricas de erro. |
| `modulos/alertas.py` | Max-heap, fila de alertas, monitoramento e simulações de gestão. |
| `modulos/consultas.py` | Trie para busca de prefixos normalizados. |
| `tests/` | Testes automatizados organizados por módulo e integrante. |
| `docs/` | Relatórios técnicos, contratos, exemplos de execução, testes e divisão de tarefas. |

## Executar os testes

```bash
python -m unittest discover -s tests -v
```

Os registros e resultados representam uma simulação didática. A latência é um indicador operacional, não um modelo de propagação física interplanetária. Os cálculos de potência descrevem entrada elétrica; sensores, redes e interfaces são conceituais.

## Documentação

Os relatórios individuais, exemplos de saída, contratos de integração e registros de testes estão na pasta [`docs/`](docs/). A documentação de cada módulo detalha as regras adotadas, os resultados e as limitações da simulação.

## Equipe e verificação integrada

Fernando dos Santos Motta (RM570046), Joedson da Silva Souza (RM573981), Caetano de Medeiros Bona (RM569262) e Mylena Ramalho da Silva Torquato (RM572383).

A suíte completa corrigida passou com **59 testes**: 13 de Fernando, 24 de Caetano, 13 de Joedson e 9 de Mylena. Ver [`docs/testes_integrados.txt`](docs/testes_integrados.txt). O relatório conjunto está em [`relatorio_tecnico.pdf`](relatorio_tecnico.pdf).

## Estado da entrega

**Pré-entrega: vídeo e URL real pendentes de Caetano.** Os módulos e o relatório estão disponíveis, mas `link_video.txt` só deve ser criado quando houver a URL real e verificada do vídeo YouTube Não listado, de até cinco minutos. Veja [`PRE_ENTREGA.md`](PRE_ENTREGA.md) para montar o pacote final. A existência do repositório ou do ZIP de pré-entrega não significa que o trabalho foi submetido no portal.
