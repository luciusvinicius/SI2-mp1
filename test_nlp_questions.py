import pytest

from sn.kb import KnowledgeBase, Relation, EntityType, RelType
from nlp.objects import Triples, Entity
from nlp.main import add_knowledge, init, query_knowledge

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