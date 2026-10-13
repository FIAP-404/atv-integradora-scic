"""Caetano - indicadores, erros, previsão e métricas.

Contrato (docs/interfaces.md):
    analisar(registros) -> {'registros': list[dict], 'resumo': dict}
    prever(carga_pct, resumo) -> float (ms)

Passo a passo de analisar():
  1. Indicadores operacionais da base inteira (descrevem, não preveem).
  2. Divisão temporal por ciclo: 60% iniciais = treino, 20% = validação,
     20% finais = teste. Na base de 30 ciclos: 1-18, 19-24 e 25-30.
  3. Limpeza: o modelo aprende só com registros 'ativo' do treino. Picos
     ('alerta') e inspeções ('manutencao') não são operação nominal.
  4. Modelo: regressão linear simples por mínimos quadrados,
     latencia = inclinacao x carga + intercepto (só o treino entra na conta).
  5. Validação: compara a reta com uma linha de base (sempre prever a média
     do treino). A reta só é aceita se errar menos na validação.
  6. Erros por registro: absoluto (ms) e relativo (fração da observada).
  7. Métricas MAE, MSE, RMSE e R² em cada conjunto, separando operação
     nominal de todos os registros (com picos).

Usa somente a biblioteca padrão do Python. Os registros recebidos NÃO são
alterados: cada registro de saída é um dicionário novo.
"""
import math
from statistics import fmean as media

PROPORCOES = {'treino': 0.6, 'validacao': 0.2, 'teste': 0.2}
STATUS_NOMINAL = 'ativo'
CASAS = 3       # a latência do CSV tem 3 casas decimais (resolução de 0,001 ms)
CASAS_COEF = 4  # coeficientes guardados no resumo; analisar e prever usam os MESMOS


# =============================================================================
# 1. FUNÇÕES MATEMÁTICAS BÁSICAS
# =============================================================================

def ajustar_reta(cargas, latencias):
    """Mínimos quadrados: a reta que minimiza a soma dos erros ao quadrado.

    inclinacao = soma((x - mx)(y - my)) / soma((x - mx)^2)
    intercepto = my - inclinacao * mx
    Escrita à mão para explicar a conta; os testes conferem contra
    statistics.linear_regression.
    """
    if len(cargas) < 2:
        raise ValueError('Caetano: são necessários pelo menos 2 registros de treino')
    mx, my = media(cargas), media(latencias)
    sxx = sum((x - mx) ** 2 for x in cargas)
    if math.isclose(sxx, 0.0, abs_tol=1e-12):
        raise ValueError('Caetano: todas as cargas do treino são iguais; a reta não é definida')
    sxy = sum((x - mx) * (y - my) for x, y in zip(cargas, latencias))
    inclinacao = sxy / sxx
    return inclinacao, my - inclinacao * mx


def aplicar_reta(carga, inclinacao, intercepto):
    """Única fórmula de previsão, usada por analisar e por prever."""
    return round(inclinacao * carga + intercepto, CASAS)


def erro_relativo(observada, prevista):
    """Fração |observada - prevista| / observada; None quando a observada é zero.

    Comparar com tolerância (math.isclose) em vez de '== 0': em ponto flutuante
    um valor calculado pode ficar muito perto de zero sem ser exatamente zero.
    """
    if math.isclose(observada, 0.0, abs_tol=1e-9):
        return None
    return abs(observada - prevista) / abs(observada)


def soma_erros_quadrados(observadas, previstas):
    return sum((o - p) ** 2 for o, p in zip(observadas, previstas))


def metricas(observadas, previstas):
    """MAE, MSE e RMSE em ms (MSE em ms²) e R² (adimensional)."""
    n = len(observadas)
    if n == 0:
        return {'n': 0, 'mae_ms': None, 'mse_ms2': None, 'rmse_ms': None, 'r2': None}
    ss_res = soma_erros_quadrados(observadas, previstas)
    mse = ss_res / n
    mo = media(observadas)
    ss_tot = sum((o - mo) ** 2 for o in observadas)
    r2 = None if math.isclose(ss_tot, 0.0, abs_tol=1e-12) else 1 - ss_res / ss_tot
    return {
        'n': n,
        'mae_ms': round(sum(abs(o - p) for o, p in zip(observadas, previstas)) / n, CASAS),
        'mse_ms2': round(mse, CASAS),
        'rmse_ms': round(math.sqrt(mse), CASAS),
        'r2': None if r2 is None else round(r2, 4),
    }


# =============================================================================
# 2. INDICADORES OPERACIONAIS
# =============================================================================

def indicadores(registros):
    """Resumo descritivo da base: geral e por módulo."""
    contagem = {}
    for r in registros:
        contagem[r['status']] = contagem.get(r['status'], 0) + 1
    por_modulo = {}
    for nome in sorted({r['modulo'] for r in registros}):
        grupo = [r for r in registros if r['modulo'] == nome]
        latencias = [r['latencia_observada_ms'] for r in grupo]
        por_modulo[nome] = {
            'registros': len(grupo),
            'carga_media_pct': round(media([r['carga_pct'] for r in grupo]), 2),
            'latencia_media_ms': round(media(latencias), CASAS),
            'latencia_maxima_ms': max(latencias),
            'alertas': sum(r['status'] == 'alerta' for r in grupo),
        }
    latencias = [r['latencia_observada_ms'] for r in registros]
    return {
        'registros': len(registros),
        'ciclos': len({r['ciclo'] for r in registros}),
        'contagem_status': contagem,
        'disponibilidade_pct': round(100 * contagem.get(STATUS_NOMINAL, 0) / len(registros), 2),
        'carga_media_pct': round(media([r['carga_pct'] for r in registros]), 2),
        'latencia_media_ms': round(media(latencias), CASAS),
        'latencia_minima_ms': min(latencias),
        'latencia_maxima_ms': max(latencias),
        'por_modulo': por_modulo,
    }


# =============================================================================
# 3. DIVISÃO DOS DADOS
# =============================================================================

def dividir_ciclos(ciclos):
    """Ciclos distintos em ordem -> {ciclo: conjunto}, sem misturar passado e futuro.

    Validação e teste ficam com 20% dos ciclos cada (pelo menos 1); o treino,
    com o restante. Assim qualquer base carregada é dividida inteira.
    """
    ordenados = sorted(set(ciclos))
    n = len(ordenados)
    n_validacao = max(1, round(n * PROPORCOES['validacao']))
    n_teste = max(1, round(n * PROPORCOES['teste']))
    n_treino = n - n_validacao - n_teste
    if n_treino < 1:
        raise ValueError(f'Caetano: a base tem {n} ciclo(s); são necessários pelo menos 3 '
                         'para separar treino, validação e teste')
    nomes = ['treino'] * n_treino + ['validacao'] * n_validacao + ['teste'] * n_teste
    return dict(zip(ordenados, nomes))


def faixas_de_ciclos(conjunto_por_ciclo):
    faixas = {}
    for ciclo, nome in conjunto_por_ciclo.items():
        inicio, fim = faixas.get(nome, (ciclo, ciclo))
        faixas[nome] = [min(inicio, ciclo), max(fim, ciclo)]
    return {nome: faixas[nome] for nome in PROPORCOES}


def nominais(registros, nome):
    return [r for r in registros if r['conjunto'] == nome and r['status'] == STATUS_NOMINAL]


def metricas_do_conjunto(registros, nome):
    grupo = [r for r in registros if r['conjunto'] == nome]
    nominal = nominais(registros, nome)
    return {
        'nominal': metricas([r['latencia_observada_ms'] for r in nominal],
                            [r['latencia_prevista_ms'] for r in nominal]),
        'todos': metricas([r['latencia_observada_ms'] for r in grupo],
                          [r['latencia_prevista_ms'] for r in grupo]),
    }


# =============================================================================
# 4. CONTRATO: analisar e prever
# =============================================================================

def analisar(registros):
    """Lista de registros -> {'registros': enriquecidos, 'resumo': dicionário}.

    Cada registro de saída mantém id e campos de origem e acrescenta
    conjunto, latencia_prevista_ms, erro_absoluto_ms e erro_relativo.
    """
    if not registros:
        raise ValueError('Caetano: base vazia, nada a analisar')
    conjunto_por_ciclo = dividir_ciclos(r['ciclo'] for r in registros)
    marcados = [dict(r, conjunto=conjunto_por_ciclo[r['ciclo']]) for r in registros]

    # Treino: somente ciclos de treino E operação nominal (limpeza).
    treino = nominais(marcados, 'treino')
    cargas = [r['carga_pct'] for r in treino]
    inclinacao, intercepto = ajustar_reta(cargas, [r['latencia_observada_ms'] for r in treino])
    inclinacao, intercepto = round(inclinacao, CASAS_COEF), round(intercepto, CASAS_COEF)
    media_treino = round(media([r['latencia_observada_ms'] for r in treino]), CASAS_COEF)

    # Validação: a reta precisa errar menos que "sempre prever a média".
    # Mesmo n nos dois lados, então comparar a soma dos erros² = comparar RMSE.
    validacao = nominais(marcados, 'validacao')
    observadas_val = [r['latencia_observada_ms'] for r in validacao]
    previstas_reta = [aplicar_reta(r['carga_pct'], inclinacao, intercepto) for r in validacao]
    previstas_base = [aplicar_reta(r['carga_pct'], 0.0, media_treino) for r in validacao]
    usar_reta = (not validacao or
                 soma_erros_quadrados(observadas_val, previstas_reta) <
                 soma_erros_quadrados(observadas_val, previstas_base))
    if not usar_reta:
        inclinacao, intercepto = 0.0, media_treino

    saida = []
    for novo in marcados:
        prevista = aplicar_reta(novo['carga_pct'], inclinacao, intercepto)
        relativo = erro_relativo(novo['latencia_observada_ms'], prevista)
        novo['latencia_prevista_ms'] = prevista
        novo['erro_absoluto_ms'] = round(abs(novo['latencia_observada_ms'] - prevista), CASAS)
        novo['erro_relativo'] = None if relativo is None else round(relativo, 4)
        saida.append(novo)

    resumo = {
        'unidades': {'latencia': 'ms', 'carga': '% (0-100)', 'erro_relativo': 'fração da latência observada'},
        'indicadores': indicadores(registros),
        'divisao': {
            'criterio': 'temporal por ciclo, 60/20/20 dos ciclos (o modelo nunca vê ciclos futuros)',
            'ciclos': faixas_de_ciclos(conjunto_por_ciclo),
            'registros': {nome: sum(r['conjunto'] == nome for r in saida) for nome in PROPORCOES},
            'limpeza': f"treino usa só status '{STATUS_NOMINAL}'; "
                       f"{sum(r['conjunto'] == 'treino' for r in saida) - len(treino)} "
                       'registros de pico/manutenção ficaram fora do ajuste',
        },
        'modelo': {
            'tipo': 'regressao_linear_simples' if usar_reta else 'media_do_treino',
            'formula': 'latencia_prevista_ms = inclinacao * carga_pct + intercepto',
            'inclinacao_ms_por_pct': inclinacao,
            'intercepto_ms': intercepto,
            'registros_treino': len(treino),
            'faixa_treino_carga_pct': [min(cargas), max(cargas)],
        },
        'selecao_na_validacao': {
            'registros_nominais': len(validacao),
            'rmse_reta_ms': metricas(observadas_val, previstas_reta)['rmse_ms'],
            'rmse_linha_de_base_media_ms': metricas(observadas_val, previstas_base)['rmse_ms'],
            'escolhido': ('reta' if validacao else 'reta (sem registros nominais para validar)')
                         if usar_reta else 'linha de base',
        },
        'metricas': {nome: metricas_do_conjunto(saida, nome) for nome in PROPORCOES},
        'erro_relativo': {
            'denominador': 'latencia_observada_ms (valor real medido)',
            'quando_zero': 'None (divisão por zero não é definida)',
        },
        'ponto_flutuante': f'coeficientes com {CASAS_COEF} casas, previsões e erros com {CASAS} '
                           '(resolução do CSV); comparações com zero usam tolerância (math.isclose)',
    }
    return {'registros': saida, 'resumo': resumo}


def prever(carga_pct, resumo):
    """Usa o modelo guardado em resumo e retorna a latência prevista em ms."""
    if (isinstance(carga_pct, bool) or not isinstance(carga_pct, (int, float))
            or not math.isfinite(carga_pct) or not 0 <= carga_pct <= 100):
        raise ValueError('Caetano: carga deve ser um número finito entre 0 e 100%')
    try:
        inclinacao = float(resumo['modelo']['inclinacao_ms_por_pct'])
        intercepto = float(resumo['modelo']['intercepto_ms'])
    except (KeyError, TypeError, ValueError):
        raise ValueError('Caetano: resumo sem modelo treinado; execute analisar() antes') from None
    prevista = aplicar_reta(carga_pct, inclinacao, intercepto)
    if not math.isfinite(prevista) or prevista < 0:
        raise ValueError(f'Caetano: modelo produziu latência inválida ({prevista})')
    return prevista


# =============================================================================
# 5. DEMONSTRAÇÃO (gera docs/exemplo_caetano.txt)
# =============================================================================

def formatar_relativo(valor):
    return 'n/d, observada = 0' if valor is None else f'{valor:.1%}'


def demonstrar(registros):
    resultado = analisar(registros)
    resumo = resultado['resumo']
    ind, mod = resumo['indicadores'], resumo['modelo']
    print(f"Registros: {ind['registros']} | ciclos: {ind['ciclos']} | status: {ind['contagem_status']}")
    print(f"Disponibilidade (status ativo): {ind['disponibilidade_pct']}%")
    print(f"Latência média: {ind['latencia_media_ms']} ms (mín {ind['latencia_minima_ms']}, máx {ind['latencia_maxima_ms']})")
    print('\nIndicadores por módulo:')
    for nome, dados in ind['por_modulo'].items():
        print(f"  {nome:15} carga média {dados['carga_media_pct']:6.2f}% | latência média "
              f"{dados['latencia_media_ms']:8.3f} ms | máx {dados['latencia_maxima_ms']:8.3f} ms | alertas {dados['alertas']}")
    print(f"\nDivisão: {resumo['divisao']['ciclos']} -> {resumo['divisao']['registros']} registros")
    print(f"Limpeza: {resumo['divisao']['limpeza']}")
    print(f"\nModelo ({mod['tipo']}): latência = {mod['inclinacao_ms_por_pct']} x carga + {mod['intercepto_ms']} ms")
    print(f"Faixa de carga do treino: {mod['faixa_treino_carga_pct'][0]}% a {mod['faixa_treino_carga_pct'][1]}%")
    sel = resumo['selecao_na_validacao']
    print(f"Validação: RMSE reta {sel['rmse_reta_ms']} ms x linha de base (média) "
          f"{sel['rmse_linha_de_base_media_ms']} ms -> escolhido: {sel['escolhido']}")
    print('\nMétricas (nominal = só status ativo; todos = inclui picos):')
    for nome, grupos in resumo['metricas'].items():
        for grupo, m in grupos.items():
            print(f"  {nome:9} {grupo:7} n={m['n']:3} | MAE {m['mae_ms']} ms | MSE {m['mse_ms2']} ms² | "
                  f"RMSE {m['rmse_ms']} ms | R² {m['r2']}")
    print('\nExemplos de registros do teste:')
    teste = [r for r in resultado['registros'] if r['conjunto'] == 'teste']
    exemplos = teste[:3] + [r for r in teste[3:] if r['status'] == 'alerta'][:2]
    for r in exemplos:
        print(f"  #{r['id']} {r['modulo']:15} ciclo {r['ciclo']} [{r['status']}] carga {r['carga_pct']}% | "
              f"observada {r['latencia_observada_ms']} | prevista {r['latencia_prevista_ms']} | "
              f"erro {r['erro_absoluto_ms']} ms ({formatar_relativo(r['erro_relativo'])})")
    print('\nPrevisões (prever):')
    for carga in (20, 50, 90, 100):
        aviso = '' if mod['faixa_treino_carga_pct'][0] <= carga <= mod['faixa_treino_carga_pct'][1] else '  <- extrapolação'
        print(f"  carga {carga:3}% -> {prever(carga, resumo)} ms{aviso}")
    print(f"\nPonto flutuante: 0.1 + 0.2 = {0.1 + 0.2!r}; "
          f"math.isclose(0.1 + 0.2, 0.3) = {math.isclose(0.1 + 0.2, 0.3)}")
    return resultado
