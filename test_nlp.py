import pytest

from sn.kb import KnowledgeBase
from nlp.objects import Triples, Entity
from nlp.main import add_knowledge, init

class KnowledgeBaseMock(): #AQUI
    def add_knowledge(declarator, relation, tx):
        pass

@pytest.fixture
def kb(): 
    kb = KnowledgeBaseMock()
    yield kb 
    

@pytest.fixture
def nlp():
    nlp = init()
    yield nlp # ig is that way 

@pytest.fixture
def user():
    yield "CC"

def test_phrase1(user, nlp, kb): # com o fixture, a variável "nlp" (igual ao nome da função) já é definida automaticamente
    """ TEST: Diogo likes playing games"""
    print("TEST1")
    text = "Diogo likes playing games"
    doc = nlp(text)
    output = [
        Triples(ent1=Entity("Diogo", False), ent2=Entity("playing games", False), rel="like")
    ] 

    result = add_knowledge(user, doc, kb)
    
    assert len(result) == len(output)
    for element in result:
        assert element in output 


def test_phrase2(user, nlp, kb): # com o fixture, a variável "nlp" (igual ao nome da função) já é definida automaticamente
    """ TEST: Diogo likes making games"""
    text = "Diogo likes making games"
    doc = nlp(text)
    output = [
        Triples(ent1=Entity("Diogo", False), ent2=Entity("making games", False), rel="like")
    ]

    result = add_knowledge(user, doc, kb)
    
    assert len(result) == len(output)
    for element in result:
        assert element in output 

def test_phrase3(user, nlp, kb): 
    """ TEST: Diogo likes eating bananas"""
    text = "Diogo likes eating bananas"
    doc = nlp(text)
    output = [
        Triples(ent1=Entity("Diogo", False), ent2=Entity("eating bananas", False), rel="like")
    ] 

    result = add_knowledge(user, doc, kb)
    
    assert len(result) == len(output)
    for element in result:
        assert element in output 
    
    
def test_phrase4(user, nlp, kb):
    """ TEST: Diogo's favorite dish is pasta"""
    text = "Diogo's favorite dish is pasta" 
    doc = nlp(text)
    output = [
        # TODO ainda acho que aqui é "Diogo's favorite dish", não "favorite dish" (do jeito que tá definido pelo menos)
        Triples(ent1=Entity("favorite dish", False), rel="be", ent2=Entity("pasta", False)), 
        Triples(ent1=Entity("Diogo", False), rel="has", ent2=Entity("favorite dish", False)),
        Triples(ent1=Entity("Diogo favorite dish", False), ent2=Entity("favorite dish", False), rel="Instance")
    ] 

    result = add_knowledge(user, doc, kb)
    
    assert len(result) == len(output)
    for element in result:
        assert element in output 
    
def test_phrase5(user, nlp, kb): 
    """ TEST: Lucius likes Dinis's green house"""
    text = "Lucius likes Dinis's green house"
    doc = nlp(text)
    output = [ 
        Triples(ent1=Entity("Lucius", False), rel="like", ent2=Entity("Dinis green house", False)),
        Triples(ent1=Entity("Dinis", False), rel="has", ent2=Entity("Dinis green house", False)),
        Triples(ent1=Entity("Dinis green house", False), rel="Instance", ent2=Entity("green house", False))
    ] 

    result = add_knowledge(user, doc, kb)
    
    assert len(result) == len(output)
    for element in result:
        assert element in output 

def test_question1(user, nlp, kb):
    """ TEST: What does Diogo like? """
    text = "What does Diogo like?"
    doc = nlp(text)
    output = "Diogo", "like"
    
    assert False


def test_question2(user, nlp, kb):
    """ TEST: Does Diogo like beans? """
    
    assert False