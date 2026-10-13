"""
Joedson - heap, prioridades e gestão inteligente da comunicação.

Contrato (docs/interfaces.md):
    priorizar(registros_analisados) -> fila
    fila.inserir(alerta) | fila.retirar() -> dict | len(fila)
Cada alerta mantém id, modulo e ciclo e acrescenta prioridade e justificativa.

Conteúdos das apostilas usados:
  - Cap. 4: max-heap em vetor, índices 2*i+1 / 2*i+2 / (i-1)//2, heapify-up,
    heapify-down (recursivo), construirMaxHeap, O(log n) para inserir/remover;
  - Cap. 3: comparação O(n log n) x O(n²);
  - Cap. 6: erro relativo, diferença finita e método de Euler;
  - Cap. 12: monitoramento contínuo, automação, manutenção preditiva,
    redundância e microrredes.

Os registros recebidos são os da análise do Caetano: campos da base do Fernando
mais latencia_prevista_ms, erro_absoluto_ms e erro_relativo. Os registros
recebidos NÃO são alterados: cada alerta é um dicionário novo.
Usa somente a biblioteca padrão do Python.
"""


# =============================================================================
# 1. CRITÉRIO DE PRIORIDADE
#    Todos os pesos ficam juntos aqui para a regra ser transparente e revisável.
# =============================================================================

PESO_STATUS = {"alerta": 40, "manutencao": 15, "ativo": 0}

# Importância de cada tipo de módulo da base para a colônia
PESO_ESSENCIALIDADE = {
    "suporte medico": 25,
    "comunicacao": 25,
    "habitacao": 20,
    "armazenamento": 15,
    "agricultura": 10,
    "laboratorio": 5,
}
ESSENCIALIDADE_PADRAO = 5      # tipo desconhecido

PONTOS_MAX_LATENCIA = 20       # até 20 pontos pelo atraso
DESVIO_SATURACAO = 0.50        # 50% acima do previsto já vale os 20 pontos
LIMITE_DESVIO = 0.20           # acima de 20% o atraso é considerado anomalia
TENSAO_NOMINAL_V = 12.0        # tensão de alimentação da base
TOLERANCIA_TENSAO = 0.10       # faixa aceitável: 10,8 V a 13,2 V
PONTOS_TENSAO = 10
PONTOS_MAX_ESPERA = 5          # +1 ponto por ciclo aguardando, no máximo 5


def desvio_relativo(registro):
    """
    Desvio relativo COM SINAL = (observada - prevista) / prevista.
    Positivo = comunicação mais lenta que o previsto. Usa a latência prevista
    pela análise do Caetano. Devolve None se a prevista faltar ou for zero.
    """
    prevista = registro.get("latencia_prevista_ms")
    if prevista is None or prevista == 0:
        return None
    return (registro["latencia_observada_ms"] - prevista) / prevista


def tensao_fora_da_faixa(registro):
    return abs(registro["tensao_v"] - TENSAO_NOMINAL_V) > TENSAO_NOMINAL_V * TOLERANCIA_TENSAO


def registro_anomalo(registro):
    """
    Um registro vira alerta quando:
      - o status não é 'ativo' (alerta ou manutenção), OU
      - a latência está mais de 20% acima da prevista, OU
      - a tensão está fora de 12 V ± 10%.
    As duas últimas regras deixam o monitoramento achar problemas mesmo com
    o módulo ainda marcado como 'ativo'.
    """
    desvio = desvio_relativo(registro)
    atraso = desvio is not None and desvio > LIMITE_DESVIO
    return registro["status"] != "ativo" or atraso or tensao_fora_da_faixa(registro)


def calcular_prioridade(registro, ciclo_atual):
    """
    Soma 5 critérios (nota de 0 a 100) e devolve também os motivos:
      1) status ....................... até 40
      2) essencialidade do módulo ..... até 25
      3) latência acima do previsto ... até 20 (proporcional ao desvio relativo)
      4) tensão fora da faixa ......... 10
      5) ciclos aguardando ............ até 5
    """
    motivos = []

    pontos_status = PESO_STATUS.get(registro["status"], 0)
    if pontos_status > 0:
        motivos.append(f"status {registro['status']} (+{pontos_status})")

    pontos_modulo = PESO_ESSENCIALIDADE.get(registro["tipo"], ESSENCIALIDADE_PADRAO)
    motivos.append(f"módulo {registro['tipo']} (+{pontos_modulo})")

    # O teto evita que só o atraso passe por cima de todos os outros critérios
    pontos_latencia = 0
    desvio = desvio_relativo(registro)
    if desvio is None:
        motivos.append("latência prevista indisponível (+0)")
    elif desvio > 0:
        pontos_latencia = min(desvio / DESVIO_SATURACAO, 1.0) * PONTOS_MAX_LATENCIA
        if pontos_latencia >= 1:
            motivos.append(f"latência {desvio * 100:.0f}% acima do previsto (+{pontos_latencia:.1f})")

    pontos_tensao = 0
    if tensao_fora_da_faixa(registro):
        pontos_tensao = PONTOS_TENSAO
        motivos.append(f"tensão {registro['tensao_v']:.1f} V fora de 12 V ± 10% (+{PONTOS_TENSAO})")

    # Evita que um alerta antigo fique esquecido no fim da fila
    ciclos_esperando = ciclo_atual - registro["ciclo"]
    pontos_espera = min(ciclos_esperando, PONTOS_MAX_ESPERA)
    if pontos_espera > 0:
        motivos.append(f"aguardando há {ciclos_esperando} ciclo(s) (+{pontos_espera})")

    total = pontos_status + pontos_modulo + pontos_latencia + pontos_tensao + pontos_espera
    # round() evita ruído de ponto flutuante na exibição e nos empates (Cap. 6)
    return round(total, 2), motivos


def nivel_do_alerta(prioridade):
    if prioridade >= 70:
        return "CRÍTICO"
    elif prioridade >= 45:
        return "ALTO"
    elif prioridade >= 25:
        return "MÉDIO"
    else:
        return "BAIXO"


def criar_alerta(registro, ciclo_atual):
    """Cria um alerta NOVO (o registro recebido não é alterado)."""
    prioridade, motivos = calcular_prioridade(registro, ciclo_atual)
    return {
        "id": registro["id"],
        "modulo": registro["modulo"],
        "ciclo": registro["ciclo"],
        "tipo": registro["tipo"],
        "mensagem": registro["mensagem"],
        "prioridade": prioridade,
        "nivel": nivel_do_alerta(prioridade),
        "justificativa": "; ".join(motivos),
        "essencialidade": PESO_ESSENCIALIDADE.get(registro["tipo"], ESSENCIALIDADE_PADRAO),
    }


def mais_urgente(a, b):
    """
    Regra de comparação do max-heap (True se 'a' é mais urgente que 'b'):
      1º maior prioridade;
      2º empate -> módulo mais essencial;
      3º empate -> registro mais antigo (ciclo menor);
      4º empate -> menor id (ordem de chegada).
    """
    CONTADOR["comparacoes"] += 1
    if a["prioridade"] != b["prioridade"]:
        return a["prioridade"] > b["prioridade"]
    elif a["essencialidade"] != b["essencialidade"]:
        return a["essencialidade"] > b["essencialidade"]
    elif a["ciclo"] != b["ciclo"]:
        return a["ciclo"] < b["ciclo"]
    else:
        return a["id"] < b["id"]


CONTADOR = {"comparacoes": 0}     # usado na comparação heap x lista


# =============================================================================
# 2. MAX-HEAP - mesma lógica do código em C do Cap. 4
#    O vetor é uma lista Python; len(vetor) faz o papel do n do C.
#    'compara' é passada como parâmetro: o mesmo heap serve para alertas e
#    para o corte de cargas da microrrede.
# =============================================================================

def pai(i):
    return (i - 1) // 2


def filho_esquerdo(i):
    return 2 * i + 1


def filho_direito(i):
    return 2 * i + 2


def trocar(vetor, i, j):
    temp = vetor[i]
    vetor[i] = vetor[j]
    vetor[j] = temp


def heapify_up(vetor, i, compara):
    """Sobe o elemento da posição i enquanto ele for mais urgente que o pai."""
    while i > 0:
        p = pai(i)
        if compara(vetor[i], vetor[p]):
            trocar(vetor, i, p)
            i = p
        else:
            break


def heapify_down(vetor, n, i, compara):
    """Desce o elemento da posição i trocando com o filho mais urgente."""
    maior = i
    esq = filho_esquerdo(i)
    dir = filho_direito(i)
    if esq < n and compara(vetor[esq], vetor[maior]):
        maior = esq
    if dir < n and compara(vetor[dir], vetor[maior]):
        maior = dir
    if maior != i:
        trocar(vetor, i, maior)
        heapify_down(vetor, n, maior, compara)


def inserir_no_heap(vetor, item, compara):
    """O(log n): coloca no fim do vetor e aplica heapify-up."""
    vetor.append(item)
    heapify_up(vetor, len(vetor) - 1, compara)


def remover_topo(vetor, compara):
    """O(log n): retira a raiz, coloca o último no lugar e aplica heapify-down."""
    if len(vetor) == 0:
        return None
    raiz = vetor[0]
    ultimo = vetor.pop()
    if len(vetor) > 0:
        vetor[0] = ultimo
        heapify_down(vetor, len(vetor), 0, compara)
    return raiz


def construir_max_heap(vetor, compara):
    """construirMaxHeap - O(n): heapify-down do último nó com filhos até a raiz."""
    n = len(vetor)
    for i in range(n // 2 - 1, -1, -1):
        heapify_down(vetor, n, i, compara)


def heap_valido(vetor, compara):
    """Confere a propriedade do max-heap: nenhum filho mais urgente que o pai."""
    for i in range(1, len(vetor)):
        if compara(vetor[i], vetor[pai(i)]):
            return False
    return True


class FilaAlertas:
    """
    Fila de prioridade exigida pelo contrato do menu (inserir, retirar, len).
    É só uma "casca": toda a lógica está nas funções de heap acima.
    """

    def __init__(self):
        self.vetor = []

    def inserir(self, alerta):
        inserir_no_heap(self.vetor, alerta, mais_urgente)

    def retirar(self):
        if len(self.vetor) == 0:
            raise IndexError("fila de alertas vazia")
        return remover_topo(self.vetor, mais_urgente)

    def __len__(self):
        return len(self.vetor)

    def topo(self):
        """O(1): o mais urgente sem retirar. None se vazia."""
        if len(self.vetor) == 0:
            return None
        return self.vetor[0]

    def mostrar(self, limite=10):
        """Mostra as primeiras posições do vetor do heap com pai e filhos."""
        n = len(self.vetor)
        if n == 0:
            print("  (fila vazia)")
        for i in range(min(n, limite)):
            a = self.vetor[i]
            texto_pai = "-"
            if i > 0:
                texto_pai = f"{pai(i)}"
            print(f"  posição {i} (pai {texto_pai}) | [{a['nivel']}] {a['prioridade']:.1f} pts | "
                  f"#{a['id']} {a['modulo']} ciclo {a['ciclo']} - {a['mensagem']}")
        if n > limite:
            print(f"  ... mais {n - limite} alerta(s) no vetor")


def priorizar(registros_analisados):
    """
    CONTRATO: recebe os registros analisados e devolve a FilaAlertas com
    todos os registros anômalos. Cada alerta entra com inserir (heapify-up).
    O 'ciclo atual' é o maior ciclo da base (usado no critério de espera).
    """
    fila = FilaAlertas()
    if len(registros_analisados) == 0:
        return fila
    ciclo_atual = max([r["ciclo"] for r in registros_analisados])
    for r in registros_analisados:
        if registro_anomalo(r):
            fila.inserir(criar_alerta(r, ciclo_atual))
    return fila


# =============================================================================
# 3. GESTÃO INTELIGENTE DA COMUNICAÇÃO (Cap. 12)
#    Funções de apoio que partem dos mesmos registros analisados.
# =============================================================================

ACOES_SUGERIDAS = {
    "comunicacao": "Reagendar transmissões não urgentes e, se houver, comutar para enlace redundante",
    "suporte medico": "Priorizar o canal da enfermaria e verificar a alimentação de 12 V",
    "habitacao": "Verificar o suporte de vida e confirmar com a equipe de manutenção",
    "armazenamento": "Redistribuir o processamento e adiar backups pesados",
    "agricultura": "Agendar inspeção dos sensores no próximo ciclo",
    "laboratorio": "Compactar dados e transmitir na janela de menor tráfego",
}


def ciclos_da_base(registros):
    return range(1, max([r["ciclo"] for r in registros]) + 1)


def registros_do_ciclo(registros, ciclo):
    lista = []
    for r in registros:
        if r["ciclo"] == ciclo:
            lista.append(r)
    return lista


def nomes_dos_modulos(registros):
    """Módulos na ordem do primeiro ciclo."""
    return [r["modulo"] for r in registros_do_ciclo(registros, 1)]


def historico_do_modulo(registros, modulo):
    lista = []
    for r in registros:
        if r["modulo"] == modulo:
            lista.append(r)
    return lista


# ---------- monitoramento contínuo ----------

def monitoramento_continuo(registros_analisados, mostrar=True):
    """
    Lê os ciclos em ordem, como se as leituras chegassem em tempo real, e
    insere cada anomalia na fila (heapify-up). Conta as DETECÇÕES ANTECIPADAS:
    anomalia achada pelo desvio de latência enquanto o status ainda era 'ativo'.
    """
    fila = FilaAlertas()
    antecipadas = []
    ciclo_final = max([r["ciclo"] for r in registros_analisados])
    for ciclo in ciclos_da_base(registros_analisados):
        novos = 0
        for r in registros_do_ciclo(registros_analisados, ciclo):
            if registro_anomalo(r):
                fila.inserir(criar_alerta(r, ciclo_final))
                novos += 1
                if r["status"] == "ativo":
                    antecipadas.append(r)
        if mostrar and novos > 0:
            topo = fila.topo()
            print(f"Ciclo {ciclo}: +{novos} alerta(s) | fila com {len(fila)} | "
                  f"mais urgente: #{topo['id']} {topo['modulo']} ({topo['prioridade']:.1f} pts)")
    if mostrar:
        print(f"\nDetecções antecipadas (status 'ativo', mas latência > {LIMITE_DESVIO * 100:.0f}% acima do previsto): "
              f"{len(antecipadas)}")
        for r in antecipadas:
            print(f"  #{r['id']} {r['modulo']} ciclo {r['ciclo']}: {desvio_relativo(r) * 100:.0f}% acima")
    return fila, antecipadas


# ---------- automação com validação humana ----------

def atender_proximo(fila, decisao_operador=None):
    """
    Retira o alerta mais urgente e sugere uma ação. A ação só vale com a
    confirmação do operador ("s"); com "n" ou resposta inválida o alerta
    volta para a fila. Sem decisão informada, pergunta com input().
    Devolve o alerta, ou None se a fila estiver vazia.
    """
    if len(fila) == 0:
        print("Nenhum alerta pendente.")
        return None
    alerta = fila.retirar()
    print(f"\n>>> ALERTA MAIS URGENTE: [{alerta['nivel']}] {alerta['prioridade']:.1f} pts | "
          f"#{alerta['id']} {alerta['modulo']} ciclo {alerta['ciclo']} - {alerta['mensagem']}")
    print("    Justificativa:", alerta["justificativa"])
    print("    Ação sugerida:", ACOES_SUGERIDAS.get(alerta["tipo"], "Encaminhar para a equipe técnica"))
    if decisao_operador is None:
        decisao_operador = input("    Operador(a), confirma a ação? (s/n): ")
    if decisao_operador == "s":
        print("    Decisão: CONFIRMADA pelo operador")
    elif decisao_operador == "n":
        fila.inserir(alerta)
        print("    Decisão: REJEITADA - o alerta voltou para a fila")
    else:
        fila.inserir(alerta)
        print("    Resposta inválida: o alerta voltou para a fila")
    print("    Alertas restantes:", len(fila))
    return alerta


# ---------- manutenção preditiva (diferença finita + Euler, Cap. 6) ----------

def manutencao_preditiva(registros_analisados, mostrar=True):
    """
    Para cada módulo, acompanha o DESVIO relativo da latência em relação à
    prevista (assim a variação normal de carga não é confundida com desgaste):
      1) taxa por diferença finita regressiva: taxa_k = d[k] - d[k-1] (h = 1 ciclo);
      2) tendência CONFIRMADA se o desvio subiu nos 3 últimos ciclos seguidos,
         cada vez mais de 2 pontos percentuais (pico isolado não conta);
      3) se confirmada, projeta pelo método de Euler d[k+1] = d[k] + h * taxa
         até passar do limite de 20%.
    """
    resultados = []
    for modulo in nomes_dos_modulos(registros_analisados):
        desvios = []
        for r in historico_do_modulo(registros_analisados, modulo):
            d = desvio_relativo(r)
            if d is not None:
                desvios.append(d)
        if len(desvios) < 4:
            resultados.append({"modulo": modulo, "situacao": "dados insuficientes", "ciclos_ate_limite": -1})
            continue
        taxas = []
        for k in range(1, len(desvios)):
            taxas.append(desvios[k] - desvios[k - 1])
        ultimas = taxas[-3:]
        subidas = 0
        for t in ultimas:
            if t > 0.02:
                subidas += 1
        taxa_media = sum(ultimas) / len(ultimas)
        ciclos_ate_limite = -1
        if subidas == 3:
            h = 1
            d = desvios[-1]
            passos = 0
            while d <= LIMITE_DESVIO and passos < 50:
                d = d + h * taxa_media          # método de Euler
                passos += 1
            ciclos_ate_limite = passos
            situacao = f"TENDÊNCIA DE ALTA: passa de 20% em {passos} ciclo(s)"
        elif desvios[-1] > LIMITE_DESVIO:
            situacao = "pico recente sem tendência: acompanhar"
        else:
            situacao = "estável"
        resultados.append({"modulo": modulo, "desvio_atual": desvios[-1], "taxa_media": taxa_media,
                           "situacao": situacao, "ciclos_ate_limite": ciclos_ate_limite})
    if mostrar:
        print("\n=== MANUTENÇÃO PREDITIVA (desvio da latência em relação à prevista) ===")
        for r in resultados:
            if r["situacao"] == "dados insuficientes":
                print(f"{r['modulo']}: dados insuficientes")
            else:
                print(f"{r['modulo']}: desvio atual {r['desvio_atual'] * 100:.1f}% | "
                      f"taxa {r['taxa_media'] * 100:.1f} p.p./ciclo | {r['situacao']}")
    return resultados


# ---------- comunicação e redundância ----------

def avaliar_enlace_comunicacao(registros_analisados, mostrar=True):
    """
    Avalia o módulo de comunicação: quantos ciclos ficou anômalo e como está
    no último ciclo. A base tem um único enlace; a redundância é recomendada
    como melhoria (enlace reserva) quando há anomalias recorrentes.
    """
    historico = []
    for r in registros_analisados:
        if r["tipo"] == "comunicacao":
            historico.append(r)
    if len(historico) == 0:
        print("Nenhum módulo de comunicação na base.")
        return None
    anomalos = 0
    for r in historico:
        if registro_anomalo(r):
            anomalos += 1
    ultimo = historico[-1]
    if registro_anomalo(ultimo):
        decisao = "Enlace degradado agora: reagendar tráfego não urgente; acionar enlace reserva (proposto)"
    elif anomalos > 0:
        decisao = "Enlace normal agora, mas com anomalias no histórico: justificar um enlace redundante"
    else:
        decisao = "Enlace estável em todos os ciclos"
    if mostrar:
        print("\n=== ENLACE DE COMUNICAÇÃO E REDUNDÂNCIA ===")
        print(f"Ciclos analisados: {len(historico)} | ciclos com anomalia: {anomalos}")
        d = desvio_relativo(ultimo)
        texto_desvio = "indisponível" if d is None else f"{d * 100:.1f}%"
        print(f"Último ciclo ({ultimo['ciclo']}): {ultimo['latencia_observada_ms']:.1f} ms, "
              f"desvio {texto_desvio}, status {ultimo['status']}")
        print("Recomendação:", decisao)
    return {"ciclos": len(historico), "ciclos_anomalos": anomalos, "decisao": decisao}


# ---------- microrrede: corte de cargas com o mesmo heap ----------

def menos_essencial(a, b):
    """Heap de corte: sai primeiro o menos essencial; empate -> quem consome mais."""
    if a["essencialidade"] != b["essencialidade"]:
        return a["essencialidade"] < b["essencialidade"]
    return a["potencia_w"] > b["potencia_w"]


def balanco_microrrede(registros_analisados, fracao_disponivel=0.8, mostrar=True):
    """
    No último ciclo, soma a potência de entrada (P = V x I, cálculo do Fernando)
    e simula que só 'fracao_disponivel' dela está disponível (ex.: tempestade
    de poeira reduzindo a geração solar). Em déficit, a microrrede entra em
    contingência (parecida com a operação ilhada do Cap. 12): módulos com
    essencialidade >= 20 são preservados e os outros vão para modo econômico
    (50% da potência), na ordem dada por um heap.
    """
    ultimo = max([r["ciclo"] for r in registros_analisados])
    demanda = 0.0
    fila_corte = []
    for r in registros_do_ciclo(registros_analisados, ultimo):
        potencia = r["tensao_v"] * r["corrente_a"]
        demanda += potencia
        essencialidade = PESO_ESSENCIALIDADE.get(r["tipo"], ESSENCIALIDADE_PADRAO)
        if essencialidade < 20:
            inserir_no_heap(fila_corte, {"modulo": r["modulo"], "essencialidade": essencialidade,
                                         "potencia_w": potencia}, menos_essencial)
    capacidade = demanda * fracao_disponivel
    restante = demanda
    cortes = []
    while restante > capacidade and len(fila_corte) > 0:
        m = remover_topo(fila_corte, menos_essencial)
        economia = m["potencia_w"] * 0.5
        restante = restante - economia
        cortes.append([m["modulo"], economia])
    if mostrar:
        print(f"\n=== MICRORREDE (ciclo {ultimo}, {fracao_disponivel * 100:.0f}% da demanda disponível) ===")
        print(f"Demanda: {demanda:.2f} W | capacidade: {capacidade:.2f} W")
        if len(cortes) == 0:
            print("Modo NORMAL: nenhum corte necessário.")
        else:
            print("Modo de CONTINGÊNCIA: cargas não essenciais em modo econômico:")
            for modulo, economia in cortes:
                print(f"  - {modulo}: -{economia:.2f} W")
            print(f"Demanda após os cortes: {restante:.2f} W")
            if restante > capacidade:
                print(f"Faltam {restante - capacidade:.2f} W: cobrir com baterias.")
        print("Preservados: suporte médico, comunicação e habitação.")
    return {"demanda_w": demanda, "capacidade_w": capacidade, "cortes": cortes, "demanda_final_w": restante}


# ---------- heap x lista (Cap. 3) ----------

def comparar_heap_com_lista(tamanhos=[100, 500, 1000, 2000], mostrar=True):
    """
    Insere n alertas e atende todos nas duas estruturas, contando comparações.
    Prioridades geradas por fórmula fixa, para o resultado ser reproduzível.
    """
    resultados = []
    for n in tamanhos:
        alertas = []
        for i in range(n):
            alertas.append({"id": i + 1, "ciclo": 1, "prioridade": (i * 7919) % 1000 / 10,
                            "essencialidade": 25})
        CONTADOR["comparacoes"] = 0
        heap = []
        for a in alertas:
            inserir_no_heap(heap, a, mais_urgente)
        ordem_heap = []
        while len(heap) > 0:
            ordem_heap.append(remover_topo(heap, mais_urgente)["id"])
        comparacoes_heap = CONTADOR["comparacoes"]

        CONTADOR["comparacoes"] = 0
        lista = []
        for a in alertas:
            lista.append(a)
        ordem_lista = []
        while len(lista) > 0:
            indice = 0
            for i in range(1, len(lista)):        # percorre tudo: O(n)
                if mais_urgente(lista[i], lista[indice]):
                    indice = i
            ordem_lista.append(lista.pop(indice)["id"])
        comparacoes_lista = CONTADOR["comparacoes"]
        resultados.append([n, comparacoes_heap, comparacoes_lista, ordem_heap == ordem_lista])
    if mostrar:
        print("\n=== HEAP x LISTA SIMPLES (inserir n alertas e atender todos) ===")
        for n, ch, cl, igual in resultados:
            print(f"n = {n}: heap {ch} | lista {cl} comparações | lista/heap = {cl / ch:.1f}x | mesma ordem: {igual}")
        print("Heap: O(log n) por operação -> O(n log n). Lista: O(n) por atendimento -> O(n²).")
    return resultados


def demonstrar_passo_a_passo():
    """Exemplo do Cap. 4: inserir 35, 12, 90, 4, 77 e retirar todos."""
    print("\n=== PASSO A PASSO DO MAX-HEAP (exemplo do Cap. 4) ===")
    heap = []
    for i, p in enumerate([35, 12, 90, 4, 77]):
        inserir_no_heap(heap, {"id": i + 1, "ciclo": 1, "prioridade": p, "essencialidade": 0}, mais_urgente)
        print(f"inserir {p} -> vetor {[a['prioridade'] for a in heap]}")
    while len(heap) > 0:
        a = remover_topo(heap, mais_urgente)
        print(f"retirar {a['prioridade']} -> vetor {[x['prioridade'] for x in heap]}")


def demonstrar(registros_analisados):
    """Demonstração completa desta parte (para o vídeo e para docs/exemplo_joedson.txt)."""
    print(f"Registros analisados recebidos: {len(registros_analisados)}")
    fila = priorizar(registros_analisados)
    print(f"\n=== FILA DE PRIORIDADE: {len(fila)} alertas ===")
    fila.mostrar(8)
    print("Propriedade de max-heap válida?", heap_valido(fila.vetor, mais_urgente))
    atender_proximo(fila, "s")
    atender_proximo(fila, "n")
    demonstrar_passo_a_passo()
    comparar_heap_com_lista()
    print("\n=== MONITORAMENTO CONTÍNUO ===")
    monitoramento_continuo(registros_analisados)
    manutencao_preditiva(registros_analisados)
    avaliar_enlace_comunicacao(registros_analisados)
    balanco_microrrede(registros_analisados, 1.0)
    balanco_microrrede(registros_analisados, 0.8)
