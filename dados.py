"""Parte de Fernando: contrato, leitura e validação dos dados sintéticos."""
import csv
import math
from pathlib import Path

CAMPOS = ('id', 'ciclo', 'modulo', 'tipo', 'codigo_sensor', 'carga_pct',
          'latencia_observada_ms', 'tensao_v', 'corrente_a', 'status', 'mensagem')
STATUS = {'ativo', 'alerta', 'manutencao'}


def carregar(caminho):
    """Retorna lista de dicionários em ordem de ciclo/id; falha sem imputar valores."""
    registros, ids = [], set()
    with Path(caminho).open(encoding='utf-8', newline='') as arquivo:
        leitor = csv.DictReader(arquivo)
        cabecalho = leitor.fieldnames or []
        if set(cabecalho) != set(CAMPOS) or len(cabecalho) != len(CAMPOS):
            raise ValueError('Cabeçalho deve conter exatamente: ' + ', '.join(CAMPOS))
        for linha, item in enumerate(leitor, start=2):
            try:
                if None in item or any(v is None for v in item.values()):
                    raise ValueError('número de colunas inconsistente')
                for campo in ('modulo', 'tipo', 'status', 'mensagem'):
                    item[campo] = item[campo].strip()
                    if not item[campo]:
                        raise ValueError(f'{campo} vazio')
                for campo in ('id', 'ciclo', 'codigo_sensor'):
                    item[campo] = int(item[campo])
                if item['id'] <= 0 or item['ciclo'] <= 0 or item['codigo_sensor'] < 0:
                    raise ValueError('id/ciclo devem ser positivos; código não negativo')
                if item['id'] in ids:
                    raise ValueError('id duplicado')
                for campo in ('carga_pct', 'latencia_observada_ms', 'tensao_v', 'corrente_a'):
                    item[campo] = float(item[campo])
                    if not math.isfinite(item[campo]) or item[campo] < 0:
                        raise ValueError(f'{campo} deve ser finito e não negativo')
                if item['carga_pct'] > 100:
                    raise ValueError('carga_pct deve estar entre 0 e 100')
                if item['status'] not in STATUS:
                    raise ValueError('status deve ser ativo, alerta ou manutencao')
                ids.add(item['id'])
                registros.append(item)
            except (ValueError, TypeError) as exc:
                raise ValueError(f'CSV, linha {linha}: {exc}') from exc
    if not registros:
        raise ValueError('CSV não contém registros')
    return sorted(registros, key=lambda r: (r['ciclo'], r['id']))


def consultar(registros, modulo='', ciclo=None):
    """Consulta básica por trecho do nome; NÃO substitui a trie pendente de Mylena."""
    return [r for r in registros if modulo.casefold() in r['modulo'].casefold()
            and (ciclo is None or r['ciclo'] == ciclo)]
