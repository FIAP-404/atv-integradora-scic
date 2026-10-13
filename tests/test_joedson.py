"""Testes de Joedson: heap, prioridades e gestão (modulos/alertas.py).

A análise de Caetano ainda não está pronta. Para testar sem esperar, usamos
uma ANÁLISE PROVISÓRIA (somente nos testes): latencia_prevista_ms = 80 + 1,8 x carga,
a parte determinística da regra de geração descrita em docs/relatorio_fernando.md.
Ela NÃO substitui o modelo de Caetano.
"""
import copy
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from dados import carregar
from modulos import alertas

BASE = Path(__file__).resolve().parent.parent / 'dados_aurora_siger.csv'


def analise_provisoria(registros):
    """Imita o formato de saída de Caetano (somente para testes/demonstração)."""
    saida = []
    for r in registros:
        novo = dict(r)
        novo['latencia_prevista_ms'] = 80 + 1.8 * r['carga_pct']
        novo['erro_absoluto_ms'] = abs(r['latencia_observada_ms'] - novo['latencia_prevista_ms'])
        novo['erro_relativo'] = novo['erro_absoluto_ms'] / novo['latencia_prevista_ms']
        saida.append(novo)
    return saida


def registro(id, ciclo=1, tipo='comunicacao', status='ativo', obs=100.0, prev=100.0, tensao=12.0):
    return {'id': id, 'ciclo': ciclo, 'modulo': tipo.title(), 'tipo': tipo, 'codigo_sensor': 1,
            'carga_pct': 50.0, 'latencia_observada_ms': obs, 'latencia_prevista_ms': prev,
            'tensao_v': tensao, 'corrente_a': 0.5, 'status': status, 'mensagem': 'teste'}


def silencioso(funcao, *args):
    with redirect_stdout(io.StringIO()):
        return funcao(*args)


class TestHeap(unittest.TestCase):
    def test_construir_max_heap_reproduz_exemplo_da_apostila(self):
        vetor = [{'id': i, 'ciclo': 1, 'prioridade': p, 'essencialidade': 0}
                 for i, p in enumerate([35, 12, 90, 4, 77, 51, 23])]
        alertas.construir_max_heap(vetor, alertas.mais_urgente)
        self.assertEqual([a['prioridade'] for a in vetor], [90, 77, 51, 4, 12, 35, 23])

    def test_retirada_sempre_em_ordem_de_urgencia(self):
        fila = alertas.FilaAlertas()
        for i in range(200):
            fila.inserir({'id': i + 1, 'ciclo': (i * 7) % 30 + 1, 'prioridade': float((i * 37) % 11),
                          'essencialidade': (i * 3) % 4 * 5})
            self.assertTrue(alertas.heap_valido(fila.vetor, alertas.mais_urgente))
        saida = []
        while len(fila):
            saida.append(fila.retirar())
            self.assertTrue(alertas.heap_valido(fila.vetor, alertas.mais_urgente))
        chave = [(a['prioridade'], a['essencialidade'], -a['ciclo'], -a['id']) for a in saida]
        self.assertEqual(chave, sorted(chave, reverse=True))

    def test_fila_vazia_lanca_index_error(self):
        with self.assertRaises(IndexError):
            alertas.FilaAlertas().retirar()
        self.assertIsNone(alertas.remover_topo([], alertas.mais_urgente))

    def test_heap_faz_menos_comparacoes_que_lista_e_mesma_ordem(self):
        for n, heap, lista, mesma in silencioso(alertas.comparar_heap_com_lista, [200, 1000]):
            self.assertTrue(mesma)
            self.assertLess(heap, lista)


class TestPrioridade(unittest.TestCase):
    def test_criterios_somados_e_justificativa(self):
        r = registro(1, ciclo=1, tipo='comunicacao', status='alerta', obs=160, prev=100)
        prioridade, motivos = alertas.calcular_prioridade(r, ciclo_atual=4)
        self.assertEqual(prioridade, 40 + 25 + 20 + 3)   # status + módulo + latência (saturada) + espera
        self.assertEqual(len(motivos), 4)

    def test_empate_favorece_modulo_mais_essencial(self):
        medico = alertas.criar_alerta(registro(2, tipo='suporte medico', status='alerta'), 1)
        dados = alertas.criar_alerta(registro(1, tipo='armazenamento', status='alerta', obs=125, prev=100), 1)
        self.assertEqual(medico['prioridade'], 65)
        self.assertEqual(dados['prioridade'], 65)
        self.assertTrue(alertas.mais_urgente(medico, dados))

    def test_desvio_e_tensao_detectam_anomalia_com_status_ativo(self):
        self.assertTrue(alertas.registro_anomalo(registro(1, obs=130, prev=100)))
        self.assertTrue(alertas.registro_anomalo(registro(2, tensao=10.0)))
        self.assertFalse(alertas.registro_anomalo(registro(3, obs=110, prev=100)))

    def test_prevista_ausente_ou_zero_nao_quebra(self):
        r = registro(1, status='alerta', prev=0)
        self.assertIsNone(alertas.desvio_relativo(r))
        self.assertIn('indisponível', alertas.criar_alerta(r, 1)['justificativa'])


class TestContratoComBaseReal(unittest.TestCase):
    def setUp(self):
        self.analisados = analise_provisoria(carregar(BASE))

    def test_priorizar_respeita_contrato_e_nao_altera_entrada(self):
        original = copy.deepcopy(self.analisados)
        fila = alertas.priorizar(self.analisados)
        self.assertEqual(self.analisados, original)
        self.assertGreater(len(fila), 0)
        alerta = fila.retirar()
        for campo in ('id', 'modulo', 'ciclo', 'prioridade', 'justificativa'):
            self.assertIn(campo, alerta)
        self.assertEqual(alerta['prioridade'], max([alerta['prioridade']] + [a['prioridade'] for a in fila.vetor]))

    def test_todos_os_registros_em_alerta_entram_na_fila(self):
        fila = alertas.priorizar(self.analisados)
        ids_fila = {a['id'] for a in fila.vetor}
        for r in self.analisados:
            if r['status'] != 'ativo':
                self.assertIn(r['id'], ids_fila)

    def test_menu_do_fernando_retira_mais_urgente(self):
        from codigo_fonte import Aplicacao
        app = Aplicacao()
        resultado = {'registros': self.analisados, 'resumo': {'modelo': 'provisório de teste'}}
        with patch('codigo_fonte.analise.analisar', return_value=resultado):
            fila = app.fila_alertas()
        self.assertGreater(len(fila), 0)
        self.assertIn('justificativa', fila.retirar())

    def test_atender_rejeitado_devolve_a_fila(self):
        fila = alertas.priorizar(self.analisados)
        tamanho = len(fila)
        silencioso(alertas.atender_proximo, fila, 'n')
        self.assertEqual(len(fila), tamanho)
        silencioso(alertas.atender_proximo, fila, 's')
        self.assertEqual(len(fila), tamanho - 1)

    def test_gestao_executa_sobre_a_base(self):
        silencioso(alertas.monitoramento_continuo, self.analisados)
        preditiva = silencioso(alertas.manutencao_preditiva, self.analisados)
        self.assertEqual(len(preditiva), 6)
        self.assertIsNotNone(silencioso(alertas.avaliar_enlace_comunicacao, self.analisados))
        micro = silencioso(alertas.balanco_microrrede, self.analisados, 0.8)
        self.assertLessEqual(micro['capacidade_w'], micro['demanda_w'])
        cortados = [m for m, _ in micro['cortes']]
        for preservado in ('Suporte Médico', 'Comunicação', 'Habitação'):
            self.assertNotIn(preservado, cortados)


if __name__ == '__main__':
    unittest.main()
