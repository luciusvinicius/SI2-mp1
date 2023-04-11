import pytest
from sn.kb import EntityType, KnowledgeBase, RelType, Relation

@pytest.fixture(scope="module", autouse=True)
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
    kb.add_knowledge("Diogo", Relation("Lucius", EntityType.INSTANCE, "mushrooms", EntityType.TYPE, "likes", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Lucius", EntityType.INSTANCE, "shotos", EntityType.TYPE, "likes", RelType.OTHER))
    kb.add_knowledge("Martinho", Relation("person", EntityType.TYPE, "mammal", EntityType.TYPE, "is", RelType.INHERITS))
    kb.add_knowledge("Lucius", Relation("mammal", EntityType.TYPE, "animal", EntityType.TYPE, "is", RelType.INHERITS))
    kb.add_knowledge("Martinho", Relation("Diogo", EntityType.INSTANCE, "cringe", EntityType.TYPE, "is", RelType.OTHER, not_=True))
    
    kb.add_knowledge("Diogo", Relation("person", EntityType.TYPE, "food", EntityType.TYPE, "eats", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("person", EntityType.TYPE, "beans", EntityType.TYPE, "eats", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Diogo", EntityType.INSTANCE, "chips", EntityType.TYPE, "eats", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("mammal", EntityType.TYPE, "banana", EntityType.TYPE, "eats", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("animal", EntityType.TYPE, "water", EntityType.TYPE, "drinks", RelType.OTHER))
    
    yield kb

    kb.delete_all()

@pytest.fixture()
def data2(initialize_knowledge_base):

    kb = initialize_knowledge_base

    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "cringe", EntityType.TYPE, "is", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "person", EntityType.TYPE, "is" , RelType.INHERITS))
    kb.add_knowledge("Lucius", Relation("Lucius", EntityType.INSTANCE, "person", EntityType.TYPE, "is" , RelType.INHERITS))
    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "working", EntityType.TYPE, "is", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Lucius", EntityType.INSTANCE, "bad declarator", EntityType.TYPE, "is", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Lucius", EntityType.INSTANCE, "mushrooms", EntityType.TYPE, "likes", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Lucius", EntityType.INSTANCE, "shotos", EntityType.TYPE, "likes", RelType.OTHER))
    kb.add_knowledge("Martinho", Relation("person", EntityType.TYPE, "mammal", EntityType.TYPE, "is", RelType.INHERITS))
    kb.add_knowledge("Lucius", Relation("mammal", EntityType.TYPE, "animal", EntityType.TYPE, "is", RelType.INHERITS))
    kb.add_knowledge("Martinho", Relation("Diogo", EntityType.INSTANCE, "cringe", EntityType.TYPE, "is", RelType.OTHER, not_=True))
    
    kb.add_knowledge("Diogo", Relation("Diogo", EntityType.INSTANCE, "chips", EntityType.TYPE, "eats", RelType.OTHER))
    
    yield kb

    kb.delete_all()
    

def test_diogo_eats(data1):
    
    kb = data1
    
    output = {
        "Diogo": (["chips"], 0),
        "person": (["food", "beans"], 1), # TODO: Food order is random. Maybe order in the query?
        "mammal": (["banana"], 2),
        
    }

    assert kb.query_inheritance_relation("Diogo", "eats") == output
    

def test_diogo_eats_chips(data2):
    
    kb = data2

    output = {
        "Diogo": (["chips"], 0),
        
    }

    assert kb.query_inheritance_relation("Diogo", "eats") == output
