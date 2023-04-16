import pytest
from typing import List
from test_knowledge_base import initialize_knowledge_base
from sn.kb import EntityType, KnowledgeBase, RelType, Relation
from sn.confidence import ConfidenceTable

@pytest.fixture()
def confidence_table(initialize_knowledge_base):

    kb: KnowledgeBase = initialize_knowledge_base    

    return ConfidenceTable(kb)

@pytest.fixture()
def data_disagreements(initialize_knowledge_base):
    
    kb: KnowledgeBase = initialize_knowledge_base

    relation_person_is_mammal = Relation("person", EntityType.TYPE, "mammal", EntityType.TYPE, "is", RelType.INHERITS)
    relation_mammal_is_animal = Relation("mammal", EntityType.TYPE, "animal", EntityType.TYPE, "is", RelType.INHERITS)
    relation_lucius_bad_declarator = Relation("Lucius", EntityType.INSTANCE, "bad declarator", EntityType.TYPE, "is", RelType.OTHER)
    relation_mammal_eats_banana = Relation("mammal", EntityType.TYPE, "banana", EntityType.TYPE, "eats", RelType.OTHER)

    kb.add_knowledge("Diogo", relation_lucius_bad_declarator)
    kb.add_knowledge("Lucius", relation_person_is_mammal)
    kb.add_knowledge("Martinho", relation_person_is_mammal)
    kb.add_knowledge("Martinho", relation_mammal_is_animal)
    kb.add_knowledge("Diogo", relation_mammal_is_animal)
    kb.add_knowledge("Lucius", relation_mammal_eats_banana)

    relations_with_inverses = [
        Relation("Diogo", EntityType.INSTANCE, "cringe", EntityType.TYPE, "is", RelType.OTHER),
        Relation("Diogo", EntityType.INSTANCE, "working", EntityType.TYPE, "is", RelType.OTHER),
        Relation("Lucius", EntityType.INSTANCE, "mushrooms", EntityType.TYPE, "likes", RelType.OTHER),
        Relation("animal", EntityType.TYPE, "water", EntityType.TYPE, "drinks", RelType.OTHER),
    ]

    kb.add_knowledge("Lucius", relations_with_inverses[0])
    kb.add_knowledge("Diogo", relations_with_inverses[0])
    kb.add_knowledge("Martinho", relations_with_inverses[0].inverse())
    kb.add_knowledge("Lucius", relations_with_inverses[1].inverse())
    kb.add_knowledge("Martinho", relations_with_inverses[1].inverse())
    kb.add_knowledge("Diogo", relations_with_inverses[2].inverse())
    kb.add_knowledge("Lucius", relations_with_inverses[2].inverse())
    kb.add_knowledge("Martinho", relations_with_inverses[2])
    kb.add_knowledge("Lucius", relations_with_inverses[3])
    kb.add_knowledge("Diogo", relations_with_inverses[3])
    
    yield kb, relations_with_inverses

    kb.delete_all()

def test_confidence_of_relation_inverses_depends_on_number_of_declarators(data_disagreements, confidence_table):
    """Confidence of relation X `cX` is equal to 1 - `~cX`, the confidence of relation ~X"""

    kb, relations_with_inverses = data_disagreements
    kb: KnowledgeBase
    relations_with_inverses: List[Relation]

    ct: ConfidenceTable = confidence_table

    for declarator in kb.get_all_declarators():
        ct.register_declarator(declarator)
    ct.update_confidences()

    for relation in relations_with_inverses:
        relation_confidence = ct.get_relation_confidence(relation)
        relation_inverse_confidence = ct.get_relation_confidence(relation.inverse())

        n_declarators = len(kb.query_declarators(relation))
        n_declarators_inverse = len(kb.query_declarators(relation.inverse()))

        if n_declarators < n_declarators_inverse:
            assert relation_confidence < relation_inverse_confidence
        else:
            assert relation_confidence > relation_inverse_confidence

        if n_declarators > 0 and n_declarators_inverse > 0:
            assert relation_confidence == 1 - relation_inverse_confidence

def test_confidence_of_bare_non_static_disagreement_at_half(initialize_knowledge_base, confidence_table):
    """Confidence of disagreement between two relations should be at half, if no other relations are present in the knowledge base"""

    kb: KnowledgeBase = initialize_knowledge_base
    ct: ConfidenceTable = confidence_table

    relation_not = Relation("Diogo", EntityType.INSTANCE, "person", EntityType.TYPE, "is" , RelType.INHERITS, not_=True)
    relation = Relation("Diogo", EntityType.INSTANCE, "person", EntityType.TYPE, "is", RelType.INHERITS)
    kb.add_knowledge("Lucius", relation_not)
    kb.add_knowledge("Diogo", relation)

    for declarator in kb.get_all_declarators():
        ct.register_declarator(declarator)
    ct.update_confidences()

    assert ct.get_relation_confidence(relation_not) == 0.5
    assert ct.get_relation_confidence(relation) == 0.5
