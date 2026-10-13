"""Gera a mesma base sintética com seed 36, sem integrações externas."""
import argparse
import csv
import random
from pathlib import Path


def gerar(destino):
    rng = random.Random(36)
    modulos = [('Habitação', 'habitacao', 160, 0), ('Agricultura', 'agricultura', 176, 8),
               ('Comunicação', 'comunicacao', 192, -8), ('Laboratório', 'laboratorio', 208, 4),
               ('Suporte Médico', 'suporte medico', 224, -4), ('Dados', 'armazenamento', 240, 12)]
    campos = ['id', 'ciclo', 'modulo', 'tipo', 'codigo_sensor', 'carga_pct', 'latencia_observada_ms', 'tensao_v', 'corrente_a', 'status', 'mensagem']
    with Path(destino).open('w', encoding='utf-8', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        for ciclo in range(1, 31):
            for j, (modulo, tipo, codigo, deslocamento) in enumerate(modulos):
                carga = round(rng.uniform(15, 95), 2)
                pico = 70 if (ciclo + 3*j) % 13 == 0 else 0
                latencia = round(80 + 1.8*carga + deslocamento + rng.gauss(0, 5) + pico, 3)
                status = 'alerta' if pico else ('manutencao' if ciclo == 17 and j == 5 else 'ativo')
                escritor.writerow(dict(zip(campos, [6*(ciclo-1)+j+1, ciclo, modulo, tipo, codigo, carga, latencia, 12, round(.35 + carga*.005, 4), status, 'Pico simulado de latência' if pico else ('Inspeção programada' if status == 'manutencao' else 'Operação nominal') ])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destino', type=Path, default=Path(__file__).with_name('dados_aurora_siger.csv'))
    args = parser.parse_args()
    if args.destino.exists():
        parser.exit(1, 'Destino já existe; escolha outro --destino para preservar os dados.\n')
    gerar(args.destino)
    print(f'Base sintética criada: {args.destino}')
