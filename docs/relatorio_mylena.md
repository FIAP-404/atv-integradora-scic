# Seção técnica de Mylena: trie e reflexão social, cultural e sustentável

Seção de Mylena para o relatório conjunto, preparada com assistência de IA e sujeita à revisão da autora. Código em `modulos/consultas.py`; testes em `tests/test_mylena.py`; exemplo real de execução em `docs/exemplo_mylena.txt`.

## 1.5 Busca de registros com trie

### O que é uma trie e como funciona

Uma trie (árvore de prefixos) é uma árvore em que cada nó representa um caractere. O caminho da raiz até um nó forma um prefixo, e chaves que começam igual compartilham o mesmo caminho. Na base da Aurora Siger, por exemplo, `c0` (código hexadecimal do sensor da Comunicação) e `comunicacao` dividem o primeiro nó `c` e só se separam depois:

```
raiz
└─ c
   ├─ 0                          ● C0 (sensor 192, Comunicação)
   └─ o → m → u → n → i → c → a → c → a → o   ● Comunicação
```

Para **inserir**, percorre-se a chave caractere por caractere a partir da raiz, criando só os nós que ainda não existem. No último nó, guarda-se o id do registro. Para **buscar por prefixo**, desce-se pelo caminho do prefixo digitado. Se o caminho não existe, nenhum registro começa com aquele prefixo. Se existe, coletam-se os ids de todos os nós abaixo dele.

### O que é indexado

O módulo indexa duas colunas de cada registro do CSV:

| Módulo | Chave do nome (normalizada) | `codigo_sensor` (decimal) | Chave hexadecimal |
|---|---|---|---|
| Habitação | `habitacao` | 160 | `a0` |
| Agricultura | `agricultura` | 176 | `b0` |
| Comunicação | `comunicacao` | 192 | `c0` |
| Laboratório | `laboratorio` | 208 | `d0` |
| Suporte Médico | `suporte medico` | 224 | `e0` |
| Dados | `dados` | 240 | `f0` |

O hexadecimal é gerado com `format(codigo, 'X')`, sem `0x`, a mesma conversão usada em `dispositivos.py`. Assim a busca conecta a trie ao conteúdo de bases numéricas: o código do sensor, tratado como identificador, pode ser digitado em hexadecimal.

A **normalização** transforma o texto em minúsculas e remove acentos (`casefold` e decomposição Unicode, descartando as marcas de acento). Por isso `COMUNICAÇÃO`, `Comunicação` e `comunicacao` geram a mesma chave, e `C0` equivale a `c0`.

### Representação no código

- `NoTrie` guarda um dicionário `filhos` (caractere → nó) e um conjunto `ids` com os registros cuja chave termina naquele nó.
- `Trie` oferece `inserir(chave, id)`, `buscar(prefixo)` e `contar_nos()`.
- `construir_indice(registros)` percorre os registros e insere o nome do módulo e o código hexadecimal de cada um, validando os campos obrigatórios.

Os resultados são **ids do campo `id` do CSV**, e não posições na lista, como pede o contrato de `docs/interfaces.md`. O conjunto de ids evita repetição: o registro #3 entra por duas chaves (`comunicacao` e `c0`) e aparece uma vez só. O retorno é ordenado, e o menu converte os ids de volta em registros, preservando a ordem de ciclo e id. Prefixo inexistente retorna lista vazia, e prefixo vazio retorna todos os ids.

### Resultados (execução real)

Base de 180 registros, 12 chaves distintas (6 nomes e 6 códigos). A trie tem 70 nós, contra 73 caracteres somados das chaves; a diferença é o prefixo compartilhado. Buscas de exemplo (saída completa em `docs/exemplo_mylena.txt`):

| Busca | Registros | Módulos encontrados |
|---|---|---|
| `com` | 30 | Comunicação |
| `COMUNICAÇÃO` | 30 | Comunicação (mesma chave de `com`) |
| `lab` | 30 | Laboratório |
| `su` | 30 | Suporte Médico |
| `c0` | 30 | Comunicação (pelo código hexadecimal) |
| `d` | 60 | Dados (nome) e Laboratório (código `D0`) |
| `xyz` | 0 | nenhum |
| (vazio) | 180 | todos |

A busca `d` mostra um efeito a ser explicado ao usuário: um prefixo curto pode casar com um nome de módulo e com um código hexadecimal ao mesmo tempo, porque os dois tipos de chave estão na mesma árvore.

### Por que a trie é adequada

A consulta por prefixo é exatamente o que a trie organiza: todas as chaves com o mesmo começo ficam sob o mesmo nó. Depois de digitar `co`, o sistema já está no nó certo, e `com` só continua a descida. Isso serve ao uso previsto no menu, em que a pessoa digita o começo de um nome ou código e recebe os registros compatíveis.

Numa lista simples, cada consulta compara o prefixo com os 180 registros, e o custo cresce com o tamanho da base. Na trie, o custo para chegar ao nó do prefixo depende do tamanho do prefixo, e não da quantidade de registros. A coleta dos resultados custa proporcionalmente ao que é devolvido. Além disso, a trie agrupa: 12 chaves distintas apontam para 180 registros.

**Vale ser honesto sobre a escala:** com 180 registros e 12 chaves, a diferença de tempo em relação a uma lista é imperceptível. A vantagem é de organização e de crescimento (mais módulos, sensores e comandos), e este protótipo a demonstra, mas não a mede.

### Limitações

- A busca é por **início** da chave. `medico` não encontra `Suporte Médico`, porque o nome é indexado inteiro, e não palavra por palavra.
- Só nome do módulo e código hexadecimal são indexados. Mensagens de alerta e outros campos não entram.
- A normalização cuida de acento e caixa, mas não corrige erros de digitação.
- `Aplicacao.buscar_prefixo` reconstrói a trie a cada busca (cópia dos dados e indexação). Isso é aceitável nesta escala, mas uma versão maior guardaria o índice pronto.
- Prefixos curtos misturam nomes e códigos (veja a busca `d`).

### Testes e evidências

- `python3 -m unittest tests.test_mylena -v`: **10 testes passaram**. Eles cobrem a normalização, prefixos compartilhados, prefixo ausente e vazio, ausência de duplicados, busca por módulo (com acento e caixa diferentes) e por código hexadecimal, rejeição de registros incompletos, a integração com a aplicação e a função de demonstração.
- `python3 -m unittest discover -s tests -v`: **60 testes passaram** na suíte completa.
- A demonstração com a base real foi gerada por `demonstrar(...)` e está em `docs/exemplo_mylena.txt`.

## 1.8 Reflexão social, cultural e sustentável

O SCIC é um protótipo com dados simulados, mas as decisões que ele organiza (qual alerta atender primeiro, qual módulo reduzir quando falta energia) seriam tomadas por pessoas e afetariam uma comunidade. Esta seção discute cinco pontos, sempre a partir do que o protótipo faz.

### Uso eficiente da comunicação e sustentabilidade

Numa colônia, energia e atenção são recursos finitos. O heap de alertas ajuda a gastar atenção onde há mais risco: o alerta mais urgente sai primeiro, em vez de a equipe percorrer tudo. O balanço de microrrede do módulo de Joedson mostra o lado da energia: no ciclo 30, a demanda soma **48,36 W**, e com 80 % disponível (38,69 W) o sistema entra em contingência. Preserva Suporte Médico, Comunicação e Habitação e coloca Laboratório, Agricultura e Dados em modo econômico, o que leva a demanda para **36,93 W**. A ideia é cortar o desperdício antes de cortar o essencial.

Duas ressalvas: esses números vêm de uma simulação com hipóteses simples (por exemplo, redução fixa de 50 %), e a trie, em si, não economiza energia de forma mensurável nesta escala. A contribuição para a sustentabilidade está nas decisões de priorização, e não na busca.

### Conhecimentos tradicionais indígenas e decisões sobre recursos

Há muitos povos indígenas no Brasil, com saberes distintos, então não cabe generalizar. Em termos gerais, muitas dessas tradições tratam o território como algo a ser cuidado, e não apenas explorado, e valorizam usar o necessário e decidir pensando na coletividade e no longo prazo. Essa é uma inspiração para o desenho do sistema, e não uma regra técnica.

O protótipo oferece um ponto concreto para aplicá-la. Na tabela de essencialidade, a Agricultura vale 10 pontos e o Laboratório 5, e na contingência esses módulos são os primeiros a entrar em modo econômico. Se a Agricultura representa a produção de alimento da colônia, considerá-la menos essencial que a comunicação é uma decisão que merece revisão por quem conhece o cultivo. Como os pesos foram definidos pela própria equipe (uma limitação já registrada na seção de Joedson), a recomendação é validá-los com os responsáveis pelos módulos e torná-los fáceis de revisar.

### Diversidade cultural e sistemas não excludentes

Um sistema pode excluir por detalhes pequenos. Na busca, a normalização de acentos e caixa existe para que `Médico`, `MEDICO` e `medico` cheguem ao mesmo resultado. Assim, quem usa teclado sem acento ou digita de modos diferentes não fica de fora, e quem prefere códigos pode usar o hexadecimal em vez do nome.

O protótipo tem limites: a interface é só em português e em terminal, e a base não contém dados pessoais nem classifica pessoas. Um risco mais sutil é o viés de critério: os pesos de prioridade e os limiares foram escolhidos por poucas pessoas, com dados simulados. Numa colônia real, essas definições refletiriam um único ponto de vista, a menos que fossem discutidas com representantes dos módulos e da comunidade. As mensagens de alerta devem se manter técnicas e neutras, como as do CSV (por exemplo, "Pico simulado de latência"), sem linguagem que culpe ou rotule pessoas ou grupos.

### Transparência nas decisões baseadas em dados

Uma decisão automatizada só pode ser questionada se puder ser explicada. Cada alerta do heap carrega uma justificativa em texto que mostra de onde vieram os pontos (por exemplo, "status alerta (+40); módulo comunicacao (+25)", seguidos dos pontos de latência e de espera). A busca por trie devolve ids que levam direto aos registros do CSV, então qualquer resultado pode ser conferido na base. Os dados são declarados como simulados, as seções técnicas listam suas limitações e o código é comentado. A transparência também exige não esconder o que o sistema não sabe, como a distinção entre dado simulado e medição real.

### A equipe humana continua responsável

O protótipo recomenda, mas não age sozinho. O módulo de alertas inclui `atender_proximo`, que mostra a justificativa e a ação sugerida e pede a confirmação do operador; se a ação é rejeitada, o alerta volta para a fila. Na opção 6 do menu, o sistema apenas exibe o alerta mais urgente, e em nenhum ponto do protótipo uma ação é executada automaticamente. Isso importa porque uma automação sem supervisão poderia reduzir um módulo que, naquele momento, é crítico, ou repetir um viés dos pesos sem que ninguém perceba. A trie, por sua vez, é apenas uma ferramenta de consulta: quem decide é a equipe.

## Síntese

O SCIC apoia o uso mais eficiente da comunicação ao priorizar alertas pelo risco e ao propor um modo de contingência que corta primeiro o que é menos essencial, reduzindo desperdício. Para que isso seja responsável, os critérios precisam ser revisáveis e discutidos com quem conhece cada módulo, as decisões precisam ser explicadas e a palavra final precisa ser humana. A busca por trie contribui para a inclusão ao aceitar variações de acento e caixa e ao permitir consultar tanto por nome quanto por código.
