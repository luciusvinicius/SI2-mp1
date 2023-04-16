import pytest

from sn.kb import KnowledgeBase, Relation, EntityType, RelType
from nlp.objects import Triples, Entity
from nlp.main import add_knowledge, init, query_knowledge


class KnowledgeBaseMock(): #AQUI
    def add_knowledge(declarator, relation, tx):
        pass

@pytest.fixture(autouse=True)
def initialize_knowledge_base():
    kb = KnowledgeBaseMock()
    yield kb
    

@pytest.fixture
def nlp():
    nlp = init()
    yield nlp # ig is that way 

@pytest.fixture
def user():
    yield "CC"

def test_phrase1(user, nlp, initialize_knowledge_base): # com o fixture, a variável "nlp" (igual ao nome da função) já é definida automaticamente
    """ TEST: Diogo likes playing games"""
    print("TEST1")
    text = "Diogo likes playing games"
    doc = nlp(text)
    output = [
        Triples(ent1=Entity("Diogo", False), ent2=Entity("playing games", False), rel="like")
    ] 
    
    kb = initialize_knowledge_base

    result = add_knowledge(user, doc, kb)
    
    assert len(result) == len(output)
    for element in result:
        assert element in output 


def test_phrase2(user, nlp, initialize_knowledge_base): # com o fixture, a variável "nlp" (igual ao nome da função) já é definida automaticamente
    """ TEST: Diogo likes making games"""
    text = "Diogo likes making games"
    doc = nlp(text)
    output = [
        Triples(ent1=Entity("Diogo", False), ent2=Entity("making games", False), rel="like")
    ]
    
    kb = initialize_knowledge_base

    result = add_knowledge(user, doc, kb)
    
    assert len(result) == len(output)
    for element in result:
        assert element in output 

def test_phrase3(user, nlp, initialize_knowledge_base): 
    """ TEST: Diogo likes eating bananas"""
    text = "Diogo likes eating bananas"
    doc = nlp(text)
    output = [
        Triples(ent1=Entity("Diogo", False), ent2=Entity("eating bananas", False), rel="like")
    ] 
    
    kb = initialize_knowledge_base

    result = add_knowledge(user, doc, kb)
    
    assert len(result) == len(output)
    for element in result:
        assert element in output 
    
    
def test_phrase4(user, nlp, initialize_knowledge_base):
    """ TEST: Diogo's favorite dish is pasta"""
    text = "Diogo's favorite dish is pasta" 
    doc = nlp(text)
    output = [
        # TODO ainda acho que aqui é "Diogo's favorite dish", não "favorite dish" (do jeito que tá definido pelo menos)
        Triples(ent1=Entity("Diogo's favorite dish", False), rel="be", ent2=Entity("pasta", False)), 
        Triples(ent1=Entity("Diogo", False), rel="has", ent2=Entity("Diogo's favorite dish", False)),
        Triples(ent1=Entity("Diogo's favorite dish", False), ent2=Entity("favorite dish", False), rel="Instance")
    ] 
    
    kb = initialize_knowledge_base

    result = add_knowledge(user, doc, kb)
    
    assert len(result) == len(output)
    for element in result:
        assert element in output 
    
def test_phrase5(user, nlp, initialize_knowledge_base): 
    """ TEST: Lucius likes Dinis's green house"""
    text = "Lucius likes Dinis's green house"
    doc = nlp(text)
    output = [ 
        Triples(ent1=Entity("Lucius", False), rel="like", ent2=Entity("Dinis's green house", False)),
        Triples(ent1=Entity("Dinis", False), rel="has", ent2=Entity("Dinis's green house", False)),
        Triples(ent1=Entity("Dinis's green house", False), rel="Instance", ent2=Entity("green house", False))
    ] 
    
    kb = initialize_knowledge_base

    result = add_knowledge(user, doc, kb)

    assert len(result) == len(output)
    for element in result:
        assert element in output 

def test_phrase6(user, nlp, initialize_knowledge_base):
    """ TEST: Lucius doesn't like Dinis's green house"""
    text = "Lucius doesn't like Dinis's green house"
    doc = nlp(text)
    output = [
        Triples(ent1=Entity("Lucius", False), rel="like", ent2=Entity("Dinis's green house", False)),
        Triples(ent1=Entity("Dinis", False), rel="has", ent2=Entity("Dinis's green house", False)),
        Triples(ent1=Entity("Dinis's green house", False), rel="Instance", ent2=Entity("green house", False))
    ]
    output[0].not_ = True
    output[1].not_ = False
    output[2].not_ = False

    kb: KnowledgeBase = initialize_knowledge_base

    result = add_knowledge(user, doc, kb)

    assert len(result) == len(output)
    for element in result:
        assert element in output

def test_phrase7(user, nlp, initialize_knowledge_base):
    """ TEST: The director is 65 years old"""
    text = "The director is 65 years old"
    doc = nlp(text)
    output = [
        Triples(ent1=Entity("director", False), rel="be", ent2=Entity("65 years old", False)),
    ]

    kb: KnowledgeBase = initialize_knowledge_base

    result = add_knowledge(user, doc, kb)
    assert len(result) == len(output)
    for element in result:
        assert element in output

def test_phrase8(user, nlp, initialize_knowledge_base):
    """ TEST: Diogo's book looks like Dinis's book"""
    text = "Diogo's book looks like Dinis's book"
    doc = nlp(text)
    output = [
        Triples(ent1=Entity("Diogo's book", False), rel="Instance", ent2=Entity("book", False)),
        Triples(ent1=Entity("Diogo", False), rel="has", ent2=Entity("Diogo's book", False)),
        Triples(ent1=Entity("Dinis's book", False), rel="Instance", ent2=Entity("book", False)),
        Triples(ent1=Entity("Dinis", False), rel="has", ent2=Entity("Dinis's book", False)),
        Triples(ent1=Entity("Diogo's book", False), rel="look like", ent2=Entity("Dinis's book", False)),
    ]

    kb: KnowledgeBase = initialize_knowledge_base

    result = add_knowledge(user, doc, kb)

    assert len(result) == len(output)
    for element in result:
        assert element in output
