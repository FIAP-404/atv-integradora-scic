"""PENDENTE — Caetano: indicadores, erros, modelo e métricas. Somente contrato."""


def analisar(registros):
    """Lista de registros -> {'registros': enriquecidos, 'resumo': dicionário}.

    Não alterar registros recebidos. Cada enriquecido mantém id e campos de origem,
    acrescenta latencia_prevista_ms, erro_absoluto_ms, erro_relativo (fração ou None).
    Resumo documenta treino/validação/teste, unidades, modelo e métricas reais.
    """
    raise NotImplementedError('Caetano: análise numérica/modelo/métricas pendentes')


def prever(carga_pct, resumo):
    """Usa modelo previamente treinado em resumo e retorna latência em ms (float)."""
    raise NotImplementedError('Caetano: previsão pendente')
