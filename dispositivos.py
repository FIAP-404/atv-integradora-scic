"""Parte de Fernando: bases numéricas e eletricidade básica."""
import math


def converter_codigo(codigo):
    if not isinstance(codigo, int) or isinstance(codigo, bool) or codigo < 0:
        raise ValueError('Código deve ser inteiro não negativo')
    return {'decimal': codigo, 'binario': format(codigo, 'b'), 'hexadecimal': format(codigo, 'X')}


def calcular_eletricidade(tensao_v, corrente_a):
    for valor in (tensao_v, corrente_a):
        if not math.isfinite(valor) or valor < 0:
            raise ValueError('Tensão/corrente devem ser finitas e não negativas')
    potencia = tensao_v * corrente_a
    resistencia = None if corrente_a == 0 else tensao_v / corrente_a
    if not math.isfinite(potencia) or (resistencia is not None and not math.isfinite(resistencia)):
        raise ValueError('Resultado fora da faixa numérica suportada')
    return {'potencia_w': potencia, 'resistencia_equivalente_ohm': resistencia}
