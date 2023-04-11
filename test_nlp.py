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
        Triples(ent1=Entity("Diogo"), ent2=Entity("playing games"), rel="likes")
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
        Triples(ent1=Entity("Diogo"), ent2=Entity("making games"), rel="likes")
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
        Triples(ent1=Entity("Diogo"), ent2=Entity("eating bananas"), rel="likes")
    ] 

    result = add_knowledge(user, doc, kb)
    
    assert len(result) == len(output)
    for element in result:
        assert element in output 
    #lucio, a vcs deu static method is not callable qnd 
    # Tenta correr o test knowledge base, ele é suposto funfar
    ## Ok, n era suposto
    # há algum motivo para o metodo ser static?
def test_phrase4(user, nlp, kb):
    """ TEST: Diogo's favorite dish is pasta"""
    text = "Diogo's favorite dish is pasta" 
    doc = nlp(text)
    output = [
        # TODO ainda acho que aqui é "Diogo's favorite dish", não "favorite dish" (do jeito que tá definido pelo menos)
        Triples(ent1=Entity("favorite dish"), rel="is", ent2=Entity("pasta")), # N era "Diogo's favorite dish"? ent pasta é ent1 não? do jeito q tá tá "dish is pasta" ent1 ou ent2 é indiferente, mas neste caso acho que pasta é que vai ser ent2 por causa como está definido o loop
        Triples(ent1=Entity("Diogo"), rel="has", ent2=Entity("favorite dish")),# também, mas 'pasta is dish' é uma informação, 
        Triples(ent1=Entity("Diogo's favorite dish"), ent2=Entity("favorite dish"), rel="Instance")
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
        Triples(ent1=Entity("Lucius"), rel="likes", ent2=Entity("Dinis's green house")),
        Triples(ent1=Entity("Dinis"), rel="has", ent2=Entity("Dinis's green house")),
        Triples(ent1=Entity("Dinis's green house"), rel="Instance", ent2=Entity("green house"))
    ] 

    result = add_knowledge(user, doc, kb)
    
    assert len(result) == len(output)
    for element in result:
        assert element in output 