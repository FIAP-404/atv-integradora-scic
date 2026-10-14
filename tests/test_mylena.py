"""Testes da trie de Mylena (modulos/consultas.py)."""
import unittest

from codigo_fonte import BASE, Aplicacao
from dados import carregar
from modulos.consultas import Trie, construir_indice, normalizar


class NormalizarTest(unittest.TestCase):
    def test_remove_acentos_e_caixa(self):
        self.assertEqual(normalizar('COMUNICAÇÃO'), 'comunicacao')
        self.assertEqual(normalizar('Suporte Médico'), 'suporte medico')
        self.assertEqual(normalizar('  C0 '), 'c0')


class TrieTest(unittest.TestCase):
    def test_prefixos_compartilham_caminho(self):
        t = Trie()
        t.inserir('Comunicação', 1)
        t.inserir('Comando', 2)
        t.inserir('Controle', 3)
        self.assertEqual(t.buscar('com'), [1, 2])
        self.assertEqual(t.buscar('co'), [1, 2, 3])
        self.assertEqual(t.buscar('controle'), [3])

    def test_ausente_vazio_e_sem_duplicados(self):
        t = Trie()
        t.inserir('Dados', 7)
        t.inserir('D0', 7)  # mesmo id por duas chaves: aparece uma vez só
        self.assertEqual(t.buscar('xyz'), [])
        self.assertEqual(t.buscar('d'), [7])
        self.assertEqual(t.buscar(''), [7])
        self.assertEqual(t.buscar('dadosx'), [])  # prefixo maior que a chave

    def test_prefixo_invalido(self):
        with self.assertRaises(ValueError):
            Trie().buscar(None)


class IndiceTest(unittest.TestCase):
    def setUp(self):
        self.base = carregar(BASE / 'dados_aurora_siger.csv')
        self.trie = construir_indice(self.base)

    def test_busca_por_modulo_ignora_acento_e_caixa(self):
        esperado = sorted(r['id'] for r in self.base if r['modulo'] == 'Comunicação')
        self.assertEqual(len(esperado), 30)
        for consulta in ('com', 'COM', 'comunicação', 'Comunicacao'):
            with self.subTest(consulta=consulta):
                self.assertEqual(self.trie.buscar(consulta), esperado)

    def test_busca_por_codigo_hexadecimal(self):
        # codigo_sensor 192 = C0 (Comunicação); 'c0' e 'C0' valem igual.
        esperado = sorted(r['id'] for r in self.base if r['codigo_sensor'] == 192)
        self.assertEqual(self.trie.buscar('c0'), esperado)
        self.assertEqual(self.trie.buscar('C0'), esperado)

    def test_retorna_ids_do_csv_unicos_e_vazio_retorna_todos(self):
        todos = sorted(r['id'] for r in self.base)
        self.assertEqual(self.trie.buscar(''), todos)
        resultado = self.trie.buscar('c')  # 'Comunicação' e hex 'C0' do mesmo registro
        self.assertEqual(len(resultado), len(set(resultado)))
        self.assertEqual(self.trie.buscar('naoexiste'), [])

    def test_registro_incompleto_e_rejeitado(self):
        with self.assertRaises(ValueError):
            construir_indice([{'id': 1, 'modulo': 'X'}])
        with self.assertRaises(ValueError):
            construir_indice([{'id': 1, 'modulo': 'X', 'codigo_sensor': -1}])

    def test_integracao_com_a_aplicacao_preserva_ordem_de_ciclo_e_id(self):
        app = Aplicacao()
        resultado = app.buscar_prefixo('lab')
        self.assertTrue(resultado)
        self.assertEqual({r['modulo'] for r in resultado}, {'Laboratório'})
        self.assertEqual([(r['ciclo'], r['id']) for r in resultado],
                         sorted((r['ciclo'], r['id']) for r in resultado))


if __name__ == '__main__':
    unittest.main()
