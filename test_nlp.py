import pytest

from sn.kb import KnowledgeBase, Relation, EntityType, RelType
from nlp.objects import Triples, Entity
from nlp.main import add_knowledge, init, query_knowledge


class KnowledgeBaseMock(): #AQUI
    def add_knowledge(declarator, relation, tx):
        pass

@pytest.fixture(autouse=True)
def initialize_knowledge_base():
    kb = KnowledgeBase("bolt://localhost:7687", "neo4j", "Sussy_baka123321")
    kb.delete_all()
    
    yield kb
    
    kb.delete_all()
    kb.close()

@pytest.fixture()
def data1(initialize_knowledge_base):

    kb = initialize_knowledge_base

    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "cringe", EntityType.TYPE, "is", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "person", EntityType.TYPE, "is" , RelType.INHERITS))
    kb.add_knowledge("Lucius", Relation("Lucius", EntityType.INSTANCE, "person", EntityType.TYPE, "is" , RelType.INHERITS))
    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "working", EntityType.TYPE, "is", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Lucius", EntityType.INSTANCE, "bad declarator", EntityType.TYPE, "is", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "beans", EntityType.TYPE, "like", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "shotos", EntityType.TYPE, "like", RelType.OTHER))
    kb.add_knowledge("Martinho", Relation("person", EntityType.TYPE, "mammal", EntityType.TYPE, "is", RelType.INHERITS))
    kb.add_knowledge("Lucius", Relation("mammal", EntityType.TYPE, "animal", EntityType.TYPE, "is", RelType.INHERITS))
    kb.add_knowledge("Martinho", Relation("Diogo", EntityType.INSTANCE, "cringe", EntityType.TYPE, "is", RelType.OTHER, not_=True))
    
    kb.add_knowledge("Diogo", Relation("person", EntityType.TYPE, "food", EntityType.TYPE, "eat", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("person", EntityType.TYPE, "beans", EntityType.TYPE, "eat", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Diogo", EntityType.INSTANCE, "chips", EntityType.TYPE, "eat", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("mammal", EntityType.TYPE, "banana", EntityType.TYPE, "eat", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("animal", EntityType.TYPE, "water", EntityType.TYPE, "drinks", RelType.OTHER))
    
    yield kb

    kb.delete_all()

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
        Triples(ent1=Entity("favorite dish", False), rel="be", ent2=Entity("pasta", False)), 
        Triples(ent1=Entity("Diogo", False), rel="has", ent2=Entity("favorite dish", False)),
        Triples(ent1=Entity("Diogo favorite dish", False), ent2=Entity("favorite dish", False), rel="Instance")
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
        Triples(ent1=Entity("Lucius", False), rel="like", ent2=Entity("Dinis green house", False)),
        Triples(ent1=Entity("Dinis", False), rel="has", ent2=Entity("Dinis green house", False)),
        Triples(ent1=Entity("Dinis green house", False), rel="Instance", ent2=Entity("green house", False))
    ] 
    
    kb = initialize_knowledge_base

    result = add_knowledge(user, doc, kb)
    
    assert len(result) == len(output)
    for element in result:
        assert element in output 

############## QUESTIONS ###############

def test_question1(user, nlp, data1):
    """ TEST: What does Diogo like? """
    text = "What does Diogo like?"
    doc = nlp(text)
    output = ("Diogo", "like", {'Diogo': (['shotos', 'beans'], 0)})
    
    kb = data1
    
    ent1, relation, query = query_knowledge(user, doc, kb)
    
    assert output == (str(ent1), str(relation), query)


def test_question2(user, nlp, data1):
    """ TEST: Does Diogo like beans? """
    
    text = "Does Diogo like rice?"
    doc = nlp(text)
    output = False
    
    kb = data1
        
    assert output == query_knowledge(user, doc, kb)

# def test_question3(user, nlp, data1):
#     """ TEST: What does Diogo's dog like? """
    
#     text = "What does Diogo's dog like?"
#     doc = nlp(text)
#     output = False
    
#     kb = data1
        
#     assert output == query_knowledge(user, doc, kb)

# def test_question4(user, nlp, data1):
#     """ TEST: Does Diogo's dog like beans? """
    
#     text = "Does Diogo's dog like beans?"
#     doc = nlp(text)
#     output = False
    
#     kb = data1
        
#     assert output == query_knowledge(user, doc, kb)
