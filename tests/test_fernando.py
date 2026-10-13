"""Testes da parte de Fernando; mocks verificam somente o encaminhamento das interfaces."""
import csv
import io
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from codigo_fonte import BASE, Aplicacao, demonstrar, menu
from dados import CAMPOS, carregar, consultar
from dispositivos import calcular_eletricidade, converter_codigo
from gerar_dados import gerar


class DadosTest(unittest.TestCase):
    def setUp(self):
        self.base = carregar(BASE/'dados_aurora_siger.csv')

    def arquivo(self, pasta, registros):
        caminho = Path(pasta)/'teste.csv'
        with caminho.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS)
            w.writeheader()
            w.writerows(registros)
        return caminho

    def test_base_coerente_e_reproduzivel(self):
        self.assertEqual(len(self.base), 180)
        self.assertEqual(len({r['modulo'] for r in self.base}), 6)
        self.assertEqual(len({r['id'] for r in self.base}), 180)
        self.assertEqual({r['ciclo'] for r in self.base}, set(range(1, 31)))
        self.assertEqual([r['id'] for r in self.base], list(range(1, 181)))
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d)/'reproduzido.csv'
            gerar(destino)
            self.assertEqual(destino.read_bytes(), (BASE/'dados_aurora_siger.csv').read_bytes())

    def test_consulta_por_modulo_e_ciclo(self):
        self.assertEqual(len(consultar(self.base, 'COMUNICAÇÃO')), 30)
        self.assertEqual([r['id'] for r in consultar(self.base, 'comunicação', 1)], [3])
        self.assertEqual(consultar(self.base, 'inexistente'), [])

    def test_ordena_sem_modificar_medicoes(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.arquivo(d, list(reversed(self.base[:3])))
            self.assertEqual(carregar(p), self.base[:3])

    def test_rejeita_campos_invalidos_com_numero_de_linha(self):
        casos = [('id', 0), ('id', '1.2'), ('ciclo', -1), ('codigo_sensor', -1),
                 ('modulo', ' '), ('tipo', ''), ('mensagem', ''), ('status', 'falha'),
                 ('carga_pct', 101), ('carga_pct', -1), ('latencia_observada_ms', 'nan'),
                 ('corrente_a', 'inf'), ('tensao_v', -1)]
        with tempfile.TemporaryDirectory() as d:
            for campo, valor in casos:
                with self.subTest(campo=campo, valor=valor):
                    registro = dict(self.base[0], **{campo: valor})
                    p = self.arquivo(d, [registro])
                    with self.assertRaisesRegex(ValueError, 'linha 2'):
                        carregar(p)

    def test_rejeita_duplicado_vazio_e_formato_inconsistente(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.arquivo(d, [self.base[0], self.base[0]])
            with self.assertRaisesRegex(ValueError, 'id duplicado'):
                carregar(p)
            self.arquivo(d, [])
            with self.assertRaisesRegex(ValueError, 'não contém registros'):
                carregar(p)
            p.write_text('id,modulo\n1,Habitação\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Cabeçalho'):
                carregar(p)
            self.arquivo(d, [self.base[0]])
            p.write_text(p.read_text(encoding='utf-8').rstrip() + ',EXTRA\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'colunas inconsistente'):
                carregar(p)

    def test_zero_observado_e_corrente_sao_validos(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.arquivo(d, [dict(self.base[0], latencia_observada_ms=0, corrente_a=0)])
            self.assertEqual(carregar(p)[0]['latencia_observada_ms'], 0)


class DispositivosTest(unittest.TestCase):
    def test_conversao_conhecida_e_zero(self):
        self.assertEqual(converter_codigo(160), {'decimal': 160, 'binario': '10100000', 'hexadecimal': 'A0'})
        self.assertEqual(int(converter_codigo(192)['hexadecimal'], 16), 192)
        self.assertEqual(converter_codigo(0)['binario'], '0')
        for valor in (-1, 1.2, True):
            with self.assertRaises(ValueError):
                converter_codigo(valor)

    def test_potencia_resistencia_e_corrente_zero(self):
        resultado = calcular_eletricidade(12, .5565)
        self.assertAlmostEqual(resultado['potencia_w'], 6.678)
        self.assertAlmostEqual(resultado['resistencia_equivalente_ohm'], 12/.5565)
        self.assertEqual(calcular_eletricidade(12, 0), {'potencia_w': 0, 'resistencia_equivalente_ohm': None})
        for v, i in ((-1, 2), (math.nan, 1), (1, math.inf), (1e308, 1e308)):
            with self.assertRaises(ValueError):
                calcular_eletricidade(v, i)


class AplicacaoTest(unittest.TestCase):
    def test_recarregar_transacional_e_invalida_cache(self):
        app = Aplicacao()
        app.resultado_analise = {'anterior': True}
        originais = app.registros
        with self.assertRaises(OSError):
            app.recarregar(BASE/'arquivo_inexistente.csv')
        self.assertIs(app.registros, originais)
        self.assertEqual(app.resultado_analise, {'anterior': True})
        app.recarregar(BASE/'dados_aurora_siger.csv')
        self.assertIsNone(app.resultado_analise)

    def test_interfaces_reais_continuam_pendentes(self):
        app = Aplicacao()
        # Análise/previsão (Caetano) e fila (Joedson) já implementadas; resta a trie.
        for acao in (lambda: app.buscar_prefixo('com'),):
            with self.assertRaises(NotImplementedError):
                acao()

    def test_encaminha_interfaces_sem_implementar_modulos(self):
        app = Aplicacao()
        # Somente doubles de teste: nenhum algoritmo dos colegas é implementado.
        resultado = {'registros': [dict(app.registros[0], erro_absoluto_ms=5)], 'resumo': {'modelo': 'double de teste'}}
        with patch('codigo_fonte.analise.analisar', return_value=resultado) as analisar:
            app.analisar()
            self.assertIsNot(analisar.call_args.args[0], app.registros)
        with patch('codigo_fonte.analise.prever', return_value=123) as prever:
            self.assertEqual(app.prever(70), 123)
            prever.assert_called_once_with(70, resultado['resumo'])
        with patch('codigo_fonte.alertas.priorizar', return_value='fila double') as priorizar:
            self.assertEqual(app.fila_alertas(), 'fila double')
            priorizar.assert_called_once_with(resultado['registros'])
        with patch('codigo_fonte.consultas.construir_indice') as indice:
            indice.return_value.buscar.return_value = [3, 3]
            self.assertEqual([r['id'] for r in app.buscar_prefixo('com')], [3])
            indice.return_value.buscar.assert_called_once_with('com')
        with patch('codigo_fonte.analise.analisar', return_value={}):
            with self.assertRaisesRegex(ValueError, 'retorno'):
                app.analisar()

    def test_demo_e_menu_tratam_pendencias_e_entrada_invalida(self):
        app = Aplicacao()
        saida = io.StringIO()
        entradas = ['9', '3', 'texto', '4', '7', 'com', '8', '0']
        with patch('builtins.input', side_effect=entradas), patch('sys.stdout', saida):
            menu(app)
            demonstrar(app)
        texto = saida.getvalue()
        self.assertIn('Opção inválida', texto)
        self.assertIn('Não foi possível executar', texto)
        self.assertIn('inclinacao_ms_por_pct', texto)  # opção 4: resumo real de Caetano
        self.assertIn('Mylena:', texto)
        self.assertIn('PENDENTE', texto)
        self.assertIn('6.6780 W', texto)

    def test_cli_de_outro_diretorio_e_erro_legivel(self):
        with tempfile.TemporaryDirectory() as d:
            processo = subprocess.run([sys.executable, str(BASE/'codigo_fonte.py'), '--demo'], cwd=d, capture_output=True, text=True)
            self.assertEqual(processo.returncode, 0, processo.stderr)
            self.assertIn('180 registros', processo.stdout)
            processo = subprocess.run([sys.executable, str(BASE/'codigo_fonte.py'), '--dados', str(Path(d)/'ausente.csv')], cwd=d, capture_output=True, text=True)
            self.assertEqual(processo.returncode, 1)
            self.assertIn('Falha ao carregar dados', processo.stderr)
            self.assertNotIn('Traceback', processo.stderr)


if __name__ == '__main__':
    unittest.main()
