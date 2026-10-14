"""Indexa duas colunas de cada registro do CSV:
  - 'modulo': nome do módulo (ex.: 'Comunicação');
  - 'codigo_sensor': código do sensor em hexadecimal, sem 0x (ex.: 192 -> 'C0').

Contrato (docs/interfaces.md): construir_indice(registros) -> trie;
trie.buscar(prefixo) -> lista de ids (campo 'id' do CSV), sem repetição.
"""
import unicodedata


def normalizar(texto):
    """Deixa o texto em minúsculas e sem acentos.

    Assim 'COMUNICAÇÃO', 'Comunicação' e 'comunicacao' viram a mesma chave
    ('comunicacao'), e o hexadecimal 'C0' é achado digitando 'c0' ou 'C0'.
    """
    decomposto = unicodedata.normalize('NFD', texto.casefold())
    # Categoria 'Mn' = marcas de acento separadas da letra (´ ~ ^ ¸ ...).
    return ''.join(c for c in decomposto if unicodedata.category(c) != 'Mn').strip()


class NoTrie:
    """Um nó da trie: um caractere do caminho a partir da raiz."""
    __slots__ = ('filhos', 'ids')

    def __init__(self):
        self.filhos = {}   # caractere -> NoTrie
        self.ids = set()   # ids dos registros cuja chave termina neste nó


class Trie:
    """Árvore de prefixos. Chaves que começam igual compartilham o mesmo caminho."""

    def __init__(self):
        self.raiz = NoTrie()

    def inserir(self, chave, id_registro):
        """Insere a chave caractere por caractere, criando só os nós que faltam."""
        no = self.raiz
        for caractere in normalizar(chave):
            no = no.filhos.setdefault(caractere, NoTrie())
        no.ids.add(id_registro)  # set: o mesmo id nunca aparece duas vezes

    def buscar(self, prefixo):
        """Retorna os ids (ordenados) dos registros cuja chave começa com o prefixo.

        Prefixo ausente -> []. Prefixo vazio -> todos os ids indexados.
        """
        if not isinstance(prefixo, str):
            raise ValueError('Prefixo deve ser texto')
        no = self.raiz
        for caractere in normalizar(prefixo):
            no = no.filhos.get(caractere)
            if no is None:  # o caminho não existe: nenhum registro tem esse prefixo
                return []
        # Do nó do prefixo para baixo, todo mundo "herda" o prefixo: coleta os ids.
        ids, pilha = set(), [no]
        while pilha:
            atual = pilha.pop()
            ids |= atual.ids
            pilha.extend(atual.filhos.values())
        return sorted(ids)


def construir_indice(registros):
    """Monta a trie a partir da lista de registros carregada por dados.carregar()."""
    trie = Trie()
    for registro in registros:
        try:
            id_registro, modulo, codigo = registro['id'], registro['modulo'], registro['codigo_sensor']
        except (KeyError, TypeError) as exc:
            raise ValueError(f'Registro sem o campo {exc} necessário para a trie') from exc
        if not isinstance(modulo, str) or not modulo.strip():
            raise ValueError('modulo deve ser texto não vazio')
        if not isinstance(codigo, int) or isinstance(codigo, bool) or codigo < 0:
            raise ValueError('codigo_sensor deve ser inteiro não negativo')
        trie.inserir(modulo, id_registro)
        trie.inserir(format(codigo, 'X'), id_registro)  # hexadecimal sem 0x, como em dispositivos.py
    return trie
