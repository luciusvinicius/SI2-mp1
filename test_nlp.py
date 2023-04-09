import pytest

from sn.kb import KnowledgeBase

@pytest.fixture(scope="module", autouse=True)
def initialize_knowledge_base():
    kb = KnowledgeBase("bolt://localhost:7687", "neo4j", "Sussy_baka123321")
    kb.delete_all()
    
    yield kb
    
    kb.delete_all()
    kb.close()


def test_main(monkeypatch, initialize_knowledge_base):
    monkeypatch.setattr(__builtins__, 'input', lambda _: "CC")
    ... # TODO: turn NLP to classes for easy testing

