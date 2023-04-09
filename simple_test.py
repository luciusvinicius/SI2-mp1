
from typing import Dict, List
from sn.kb import EntityType, KnowledgeBase, RelType, Relation
from sn.confidence import ConfidenceTable
from copy import copy

kb = KnowledgeBase("bolt://localhost:7687", "neo4j", "Sussy_baka123321")

def add_data1():
    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "cringe", EntityType.TYPE, "is", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "person", EntityType.TYPE, "is" , RelType.INHERITS))
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


add_data1()


def test_diogo_eats():
    output = {
        "Diogo": (["chips"], 0),
        "person": (["food", "beans"], 1), # TODO: Food order is random. Maybe order in the query?
        "mammal": (["banana"], 2),
        
    }
    assert kb.query_inheritance_relation("Diogo", "eats") == output

def test_test():
    output = {
        "Diogo": (["chips"], 0),
        "person": (["food", "beans"], 1),
        "mammal": (["banana"], 2),
        
    }
    assert kb.query_inheritance_relation("Diogo", "eats") == output