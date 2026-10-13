# SCIC — parte de Fernando

Projeto Integrador da Fase 6 da FIAP: Sistema de Comunicação Interplanetária da Colônia Aurora Siger. **Este repositório contém somente a parte de Fernando e contratos de integração. O trabalho completo ainda está pendente.**

## Estado

| Parte | Responsável | Estado |
|---|---|---|
| Dados simulados, leitura/validação, consulta básica, menu e estrutura de integração | Fernando | Implementados e testados |
| Bases numéricas, entradas/saídas e eletricidade básica | Fernando | Implementados, documentados e testados |
| Indicadores, erros, previsão e métricas | Caetano | Implementados, documentados e testados |
| Heap, prioridades e gestão inteligente | Joedson | Interface pendente |
| Trie e reflexão social/cultural/sustentável | Mylena | Interface pendente |
| Relatório conjunto, demonstração completa e ZIP final | Todos | Pendentes de integração e revisão |

**Cada integrante documenta e testa seu próprio módulo. Não há atribuição de consolidação documental à Mylena.** Os arquivos de protótipo integral anteriores foram preservados fora deste repositório como rascunhos locais; não foram incluídos nesta publicação.

## Executar

Requer Python 3.10 ou superior. Somente biblioteca padrão; nenhum pacote ou serviço externo é necessário.

```sh
python3 codigo_fonte.py
python3 codigo_fonte.py --demo
python3 -m unittest discover -s tests -v
```

A base padrão fica ao lado do código e funciona independentemente do diretório atual. Para carregar outro CSV com o contrato documentado: `python3 codigo_fonte.py --dados caminho.csv`. No menu, a opção 1 permite carregar outra base sem modificar arquivos. Uma leitura inválida preserva a base anterior; leitura válida invalida análises em cache.

- Opção 2: consulta simples por trecho do nome e ciclo. **Não é busca trie.**
- Opção 3: sensor em decimal/binário/hexadecimal, potência P=V×I e resistência equivalente sob hipótese resistiva.
- Opções 4–7: pontos de integração dos colegas. Hoje informam explicitamente o que está pendente, sem simular resultado de modelo, heap ou trie.
- Opção 8: estado do projeto. Opção 0: sair.

Para reproduzir a mesma base preservando a entregue:

```sh
python3 gerar_dados.py --destino /tmp/dados_scic_reproduzidos.csv
```

O comando recusa um destino que já existe. `gerar()` é a função de geração usada pelos testes em diretório temporário. Todas as observações são sintéticas e a semente é 36.

## Arquivos e contratos

- `codigo_fonte.py`: entrada principal e integração.
- `dados.py`, `dados_aurora_siger.csv`, `gerar_dados.py`: parte de dados de Fernando.
- `dispositivos.py`: conversões e eletricidade.
- `modulos/analise.py`: análise de Caetano (indicadores, erros, modelo e métricas); testes em `tests/test_caetano.py` e seção em [docs/relatorio_caetano.md](docs/relatorio_caetano.md).
- `modulos/alertas.py`, `modulos/consultas.py`: somente assinaturas/docstrings e `NotImplementedError`.
- `tests/test_fernando.py`: testes de Fernando; mocks verificam encaminhamento das interfaces, não algoritmos dos colegas.
- [docs/interfaces.md](docs/interfaces.md): campos, unidades, assinaturas e dependências.
- [docs/relatorio_fernando.md](docs/relatorio_fernando.md): seção técnica própria de Fernando.
- [docs/divisao_tarefas.md](docs/divisao_tarefas.md): divisão atualizada.
- [docs/requisitos_verificados.md](docs/requisitos_verificados.md): fonte e requisitos oficiais.
- [docs/testes_fernando.txt](docs/testes_fernando.txt) e [docs/exemplo_fernando.txt](docs/exemplo_fernando.txt): evidências reais da execução local.

Cada colega pode substituir seu arquivo de interface por implementação compatível e acrescentar seus testes/documentação. Ninguém deve editar os módulos alheios para apresentar sua parte como concluída.

## Limites e pendências de entrega

A base tem 180 registros de seis módulos ao longo de 30 ciclos. Latência em ms é atraso operacional didático; não modela propagação física entre planetas. Potência é elétrica de entrada, não radiada; sem duração em horas não se calcula energia. Sensores/interfaces reais são conceituais.

Ainda faltam os módulos dos colegas, avaliação integrada, `relatorio_tecnico.md/pdf` conjunto, vídeo real de até 5 minutos, URL Não listado em `link_video.txt` e ZIP final. Não se incluiu um vídeo ou relatório completo fictício. Conferir integrantes no portal e tabela de pontuação, cujas imagens estavam quebradas na leitura de 12/10/2026.

Preparação assistida por IA sob revisão de Fernando. Cada integrante deve entender, revisar e explicar sua parte e cumprir as normas institucionais de autoria. A publicação deste código não representa submissão na FIAP.
