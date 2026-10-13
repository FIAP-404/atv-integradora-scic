"""Testes de Caetano: indicadores, erros, previsão e métricas (modulos/analise.py)."""
import copy
import json
import io
import math
import statistics
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from dados import carregar
from modulos import analise

BASE = Path(__file__).resolve().parent.parent / 'dados_aurora_siger.csv'


def registro(id, ciclo, carga, latencia, status='ativo', modulo='Comunicação'):
    return {'id': id, 'ciclo': ciclo, 'modulo': modulo, 'tipo': 'comunicacao', 'codigo_sensor': 192,
            'carga_pct': carga, 'latencia_observada_ms': latencia, 'tensao_v': 12.0,
            'corrente_a': 0.5, 'status': status, 'mensagem': 'teste'}


def base_exata():
    """Latência = 2 x carga + 100 em todos os ciclos, com um pico fora da reta no treino."""
    regs = [registro(i, ciclo, carga, 2 * carga + 100)
            for i, (ciclo, carga) in enumerate(((c, 10.0 + 3 * c) for c in range(1, 31)), start=1)]
    regs.append(registro(99, 5, 50.0, 400.0, status='alerta'))
    return regs


class MatematicaTest(unittest.TestCase):
    def test_reta_recupera_coeficientes_exatos(self):
        inclinacao, intercepto = analise.ajustar_reta([0, 1, 2, 3], [5, 7, 9, 11])
        self.assertAlmostEqual(inclinacao, 2.0)
        self.assertAlmostEqual(intercepto, 5.0)

    def test_reta_confere_com_a_biblioteca_padrao(self):
        regs = carregar(BASE)
        x, y = [r['carga_pct'] for r in regs], [r['latencia_observada_ms'] for r in regs]
        inclinacao, intercepto = analise.ajustar_reta(x, y)
        referencia = statistics.linear_regression(x, y)
        self.assertAlmostEqual(inclinacao, referencia.slope, places=9)
        self.assertAlmostEqual(intercepto, referencia.intercept, places=9)

    def test_reta_exige_cargas_diferentes(self):
        with self.assertRaises(ValueError):
            analise.ajustar_reta([50, 50], [100, 120])
        with self.assertRaises(ValueError):
            analise.ajustar_reta([50], [100])

    def test_metricas_conferidas_a_mao(self):
        # erros 1, -1, 2, 0 -> MAE 1, MSE 6/4 = 1,5, RMSE ~1,2247
        m = analise.metricas([10, 20, 30, 40], [9, 21, 28, 40])
        self.assertEqual(m['n'], 4)
        self.assertEqual(m['mae_ms'], 1.0)
        self.assertEqual(m['mse_ms2'], 1.5)
        self.assertAlmostEqual(m['rmse_ms'], math.sqrt(1.5), places=3)
        self.assertAlmostEqual(m['r2'], 1 - 6 / 500, places=4)

    def test_metricas_casos_limite(self):
        self.assertIsNone(analise.metricas([], [])['mae_ms'])
        self.assertIsNone(analise.metricas([5, 5], [5, 5])['r2'])  # sem variação: R² indefinido

    def test_erro_relativo_usa_observada_e_trata_zero(self):
        self.assertAlmostEqual(analise.erro_relativo(200.0, 150.0), 0.25)
        self.assertIsNone(analise.erro_relativo(0.0, 10.0))
        self.assertIsNone(analise.erro_relativo(1e-12, 10.0))  # tolerância de ponto flutuante


class AnaliseTest(unittest.TestCase):
    def test_nao_altera_entrada_e_preserva_campos(self):
        regs = base_exata()
        original = copy.deepcopy(regs)
        resultado = analise.analisar(regs)
        self.assertEqual(regs, original)
        for entrada, saida in zip(regs, resultado['registros']):
            self.assertIsNot(entrada, saida)
            for campo, valor in entrada.items():
                self.assertEqual(saida[campo], valor)
            for campo in ('latencia_prevista_ms', 'erro_absoluto_ms', 'erro_relativo', 'conjunto'):
                self.assertIn(campo, saida)

    def test_limpeza_tira_pico_do_treino(self):
        resumo = analise.analisar(base_exata())['resumo']
        self.assertAlmostEqual(resumo['modelo']['inclinacao_ms_por_pct'], 2.0)
        self.assertAlmostEqual(resumo['modelo']['intercepto_ms'], 100.0)
        self.assertEqual(resumo['metricas']['teste']['nominal']['mae_ms'], 0.0)

    def test_teste_nao_influencia_o_modelo(self):
        # A validação PODE mudar o modelo (ela escolhe reta x média); o teste, nunca.
        regs = base_exata()
        alterados = [dict(r, latencia_observada_ms=r['latencia_observada_ms'] * 3) if r['ciclo'] >= 25 else r
                     for r in regs]
        r1 = analise.analisar(regs)['resumo']
        r2 = analise.analisar(alterados)['resumo']
        self.assertEqual(r1['modelo'], r2['modelo'])
        self.assertEqual(r1['selecao_na_validacao'], r2['selecao_na_validacao'])
        self.assertNotEqual(r1['metricas']['teste'], r2['metricas']['teste'])

    def test_divisao_acompanha_a_base_carregada(self):
        def base(ciclos):
            return [registro(c, c, 10.0 + 2 * c, 2 * (10.0 + 2 * c) + 100) for c in range(1, ciclos + 1)]
        self.assertEqual(analise.analisar(base(30))['resumo']['divisao']['ciclos'],
                         {'treino': [1, 18], 'validacao': [19, 24], 'teste': [25, 30]})
        resumo = analise.analisar(base(60))['resumo']
        self.assertEqual(resumo['divisao']['ciclos']['teste'], [49, 60])
        self.assertEqual(sum(resumo['divisao']['registros'].values()), 60)  # nenhum ciclo fica de fora
        resumo = analise.analisar(base(15))['resumo']
        self.assertEqual(resumo['divisao']['ciclos'], {'treino': [1, 9], 'validacao': [10, 12], 'teste': [13, 15]})
        self.assertEqual(resumo['metricas']['teste']['nominal']['n'], 3)
        with self.assertRaises(ValueError):
            analise.analisar(base(2))

    def test_indicador_conta_ciclos_distintos(self):
        regs = [registro(1, 1, 20.0, 140.0), registro(2, 2, 40.0, 180.0), registro(3, 40, 60.0, 220.0)]
        self.assertEqual(analise.indicadores(regs)['ciclos'], 3)

    def test_validacao_cai_para_media_se_reta_for_pior(self):
        # Treino com tendência, validação sem: a reta perde da média na validação.
        regs = [registro(i, c, 10.0 * (i % 9) + 5, 2 * (10.0 * (i % 9) + 5) + 100) for i, c in
                enumerate(range(1, 19), start=1)]
        regs += [registro(100 + c, c, 90.0, 150.0) for c in range(19, 31)]
        resumo = analise.analisar(regs)['resumo']
        self.assertEqual(resumo['selecao_na_validacao']['escolhido'], 'linha de base')
        self.assertEqual(resumo['modelo']['inclinacao_ms_por_pct'], 0.0)

    def test_erro_relativo_none_quando_observada_zero(self):
        regs = base_exata() + [registro(200, 26, 40.0, 0.0)]
        saida = {r['id']: r for r in analise.analisar(regs)['registros']}
        self.assertIsNone(saida[200]['erro_relativo'])
        self.assertEqual(saida[200]['erro_absoluto_ms'], 180.0)

    def test_base_vazia_e_rejeitada(self):
        with self.assertRaises(ValueError):
            analise.analisar([])


class PreverTest(unittest.TestCase):
    def setUp(self):
        self.resumo = analise.analisar(base_exata())['resumo']

    def test_previsao_usa_o_modelo(self):
        self.assertAlmostEqual(analise.prever(50, self.resumo), 200.0)
        self.assertAlmostEqual(analise.prever(0, self.resumo), 100.0)

    def test_rejeita_carga_invalida_e_resumo_sem_modelo(self):
        for carga in (-1, 100.5, math.nan, math.inf, '50', True, False):
            with self.assertRaises(ValueError):
                analise.prever(carga, self.resumo)
        with self.assertRaises(ValueError):
            analise.prever(50, {})

    def test_rejeita_saida_negativa(self):
        resumo = {'modelo': {'inclinacao_ms_por_pct': -5.0, 'intercepto_ms': 10.0}}
        with self.assertRaises(ValueError):
            analise.prever(50, resumo)


class BaseRealTest(unittest.TestCase):
    def setUp(self):
        self.resultado = analise.analisar(carregar(BASE))

    def test_resumo_e_serializavel_em_json(self):
        texto = json.dumps(self.resultado['resumo'], ensure_ascii=False)
        self.assertEqual(json.loads(texto)['modelo'], self.resultado['resumo']['modelo'])

    def test_modelo_proximo_da_regra_de_geracao(self):
        # Gerador: 80 + 1,8 x carga + deslocamento de módulo (média ~2 ms) + ruído.
        modelo = self.resultado['resumo']['modelo']
        self.assertAlmostEqual(modelo['inclinacao_ms_por_pct'], 1.8, delta=0.1)
        self.assertAlmostEqual(modelo['intercepto_ms'], 82.0, delta=5.0)

    def test_divisao_e_metricas_coerentes(self):
        resumo = self.resultado['resumo']
        self.assertEqual(resumo['divisao']['registros'], {'treino': 108, 'validacao': 36, 'teste': 36})
        self.assertEqual(resumo['selecao_na_validacao']['escolhido'], 'reta')
        for conjunto in ('treino', 'validacao', 'teste'):
            m = resumo['metricas'][conjunto]
            self.assertGreater(m['nominal']['r2'], 0.9)
            self.assertLess(m['nominal']['rmse_ms'], m['todos']['rmse_ms'])  # picos pioram o erro
            self.assertLessEqual(m['nominal']['mae_ms'], m['nominal']['rmse_ms'])

    def test_prever_reproduz_a_previsao_de_cada_registro(self):
        resumo = self.resultado['resumo']
        for r in self.resultado['registros']:
            self.assertEqual(analise.prever(r['carga_pct'], resumo), r['latencia_prevista_ms'])

    def test_selecao_e_metricas_de_validacao_concordam(self):
        resumo = self.resultado['resumo']
        self.assertEqual(resumo['selecao_na_validacao']['rmse_reta_ms'],
                         resumo['metricas']['validacao']['nominal']['rmse_ms'])

    def test_demonstrar_aceita_latencia_zero_e_nao_repete_exemplo(self):
        regs = carregar(BASE)
        alvo = next(r for r in regs if r['ciclo'] == 25)
        alvo['latencia_observada_ms'] = 0.0
        alvo['status'] = 'alerta'
        saida = io.StringIO()
        with redirect_stdout(saida):
            analise.demonstrar(regs)
        texto = saida.getvalue()
        self.assertIn('n/d, observada = 0', texto)
        self.assertEqual(texto.count(f"#{alvo['id']} "), 1)

    def test_picos_tem_erro_relativo_alto(self):
        for r in self.resultado['registros']:
            if r['status'] == 'alerta':
                self.assertGreater(r['erro_relativo'], 0.15)


if __name__ == '__main__':
    unittest.main()
