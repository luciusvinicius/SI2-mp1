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
def example_data(initialize_knowledge_base):

    kb: KnowledgeBase = initialize_knowledge_base

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

def test_diogo_eats(example_data):
    
    kb: KnowledgeBase = example_data
    
    output = {
        "Diogo": ({"chips"}, 0),
        "person": ({"food", "beans"}, 1),
        "mammal": ({"banana"}, 2),
    }

    kb_output = kb.query_inheritance_relation("Diogo", "eats")

    assert kb_output == output


def test_diogo_eats_with_declarator(example_data):
    
    kb: KnowledgeBase = example_data
    
    output = {
        "mammal": ({"banana"}, 2),
    }

    kb_output = kb.query_inheritance_relation("Diogo", "eats", declarator="Lucius")

    assert kb_output == output


def test_query_local(example_data):

    kb: KnowledgeBase = example_data

    output = {(("is", "Other"), frozenset({"cringe", "working"})), (("is", "Inherits"), frozenset({"person"})), (("eats", "Other"), frozenset({"chips"}))}

    kb_output = kb.query_local("Diogo")

    assert kb_output == output


def test_query_local_relation(example_data):

    kb: KnowledgeBase = example_data

    output = {"working", "cringe"}

    kb_output = kb.query_local_relation("Diogo", "is", RelType.OTHER)

    assert kb_output == output


def test_query_descendants_relation(example_data):

    kb: KnowledgeBase = example_data

    output = {"beans", "food", "chips"}

    kb_output = kb.query_descendants_relation("mammal", "eats", RelType.OTHER)

    assert kb_output == output


def test_no_conflicting_declarations(initialize_knowledge_base):

    kb: KnowledgeBase = initialize_knowledge_base

    kb.add_knowledge('Lucius', Relation('Lucius', EntityType.INSTANCE, 'Dinis\'s green house', EntityType.INSTANCE, 'like', RelType.OTHER, not_=True))
    kb.add_knowledge('Lucius', Relation('Lucius', EntityType.INSTANCE, 'Dinis\'s green house', EntityType.INSTANCE, 'like', RelType.OTHER, not_=False))

    assert len(kb.query_declarations('Lucius')) == 1