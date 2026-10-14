"""SCIC: Sistema de Comunicação Interplanetária da Colônia Aurora Siger (protótipo)."""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
from dados import carregar, consultar
from dispositivos import converter_codigo, calcular_eletricidade
from modulos import analise, alertas, consultas

BASE = Path(__file__).resolve().parent


class Aplicacao:
    def __init__(self, caminho=BASE/'dados_aurora_siger.csv'):
        self.caminho = Path(caminho)
        self.registros = carregar(self.caminho)
        self.resultado_analise = None

    def recarregar(self, caminho):
        # Só troca a base depois da leitura bem-sucedida. Invalida análise antiga.
        novos = carregar(caminho)
        self.caminho, self.registros = Path(caminho), novos
        self.resultado_analise = None

    def analisar(self):
        resultado = analise.analisar(deepcopy(self.registros))
        if not isinstance(resultado, dict) or not isinstance(resultado.get('registros'), list) or not isinstance(resultado.get('resumo'), dict):
            raise ValueError('Caetano: retorno deve conter registros (lista) e resumo (dicionário)')
        self.resultado_analise = resultado
        return resultado

    def prever(self, carga):
        if not math.isfinite(carga) or not 0 <= carga <= 100:
            raise ValueError('Carga deve estar entre 0 e 100%')
        resultado = self.resultado_analise or self.analisar()
        return analise.prever(carga, deepcopy(resultado['resumo']))

    def fila_alertas(self):
        resultado = self.resultado_analise or self.analisar()
        return alertas.priorizar(deepcopy(resultado['registros']))

    def buscar_prefixo(self, prefixo):
        trie = consultas.construir_indice(deepcopy(self.registros))
        ids = set(trie.buscar(prefixo))
        return [r for r in self.registros if r['id'] in ids]


def mostrar(registros, limite=8):
    for r in registros[:limite]:
        print(f"#{r['id']} | ciclo {r['ciclo']} | {r['modulo']} | sensor {r['codigo_sensor']} | carga {r['carga_pct']:.2f}% | latência observada {r['latencia_observada_ms']:.3f} ms | {r['status']}")
    print(f'{len(registros)} encontrados; exibindo até {limite}.')


def mostrar_dispositivo(registro):
    print(f"Dispositivo simulado do registro #{registro['id']} ({registro['modulo']}):")
    print(json.dumps(converter_codigo(registro['codigo_sensor']), ensure_ascii=False))
    valores = calcular_eletricidade(registro['tensao_v'], registro['corrente_a'])
    print(f"P = {registro['tensao_v']} V × {registro['corrente_a']} A = {valores['potencia_w']:.4f} W")
    resistencia = valores['resistencia_equivalente_ohm']
    print('R equivalente (hipótese resistiva):', 'indefinida (corrente zero)' if resistencia is None else f'{resistencia:.4f} Ω')
    print('Entrada: sensores/medidores simulados em CSV. Saída: terminal; rede/USB são interfaces conceituais.')
    print('Potência elétrica de entrada; não potência radiada nem energia consumida. Não há enlace físico real.')


def demonstrar(app):
    print('SCIC — Aurora Siger — dados inteiramente simulados')
    print(f'Base carregada e validada: {len(app.registros)} registros.')
    mostrar(app.registros, 3)
    print('\nConsulta simples: Comunicação, ciclo 1 (a busca por prefixo com trie está na opção 7 do menu).')
    mostrar(consultar(app.registros, 'Comunicação', 1))
    mostrar_dispositivo(app.registros[0])


def menu(app):
    while True:
        print('\n1 Carregar CSV | 2 Consultar registros | 3 Bases e eletricidade\n4 Análise | 5 Previsão\n6 Alertas (heap) | 7 Busca por prefixo (trie) | 0 Sair')
        try:
            opcao = input('Opção: ').strip()
            if opcao == '0':
                return
            if opcao == '1':
                app.recarregar(input('Caminho do CSV: ').strip())
                print(f'Carregados {len(app.registros)} registros; análise anterior invalidada.')
            elif opcao == '2':
                nome = input('Trecho do nome do módulo (vazio=todos): ').strip()
                ciclo = input('Ciclo (vazio=todos): ').strip()
                mostrar(consultar(app.registros, nome, None if not ciclo else int(ciclo)))
            elif opcao == '3':
                identificador = int(input('Id do registro (exemplo 1): '))
                r = next((r for r in app.registros if r['id'] == identificador), None)
                if r is None:
                    print('Registro não encontrado.')
                else:
                    mostrar_dispositivo(r)
            elif opcao == '4':
                print(json.dumps(app.analisar()['resumo'], ensure_ascii=False, indent=2))
            elif opcao == '5':
                print('Latência prevista (ms):', app.prever(float(input('Carga (%): '))))
            elif opcao == '6':
                fila = app.fila_alertas()
                if len(fila):
                    print('Alerta mais urgente:', fila.retirar())
                else:
                    print('Fila vazia.')
            elif opcao == '7':
                mostrar(app.buscar_prefixo(input('Prefixo de módulo ou código hex (ex.: com, c0; vazio=todos): ')))
            else:
                print('Opção inválida.')
        except (ValueError, OSError) as exc:
            print('Não foi possível executar a opção:', exc)
        except EOFError:
            return


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dados', type=Path, default=BASE/'dados_aurora_siger.csv')
    parser.add_argument('--demo', action='store_true', help='Demonstração rápida, sem menu')
    args = parser.parse_args()
    try:
        app = Aplicacao(args.dados)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Falha ao carregar dados: {exc}\n')
    demonstrar(app) if args.demo else menu(app)


if __name__ == '__main__':
    main()
