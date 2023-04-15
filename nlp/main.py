import spacy
import sys
from spacy import displacy
from typing import Dict, List


# # setting path
# sys.path.append('../parentdirectory')
# # importing
# from parentdirectory.geeks import geek_method

# Como corre
from sn.kb import EntityType, KnowledgeBase, RelType, Relation
from sn.confidence import ConfidenceTable
from copy import copy
from nlp.objects import Entity, Triples

def init() -> spacy.Language:
    nlp = spacy.load("en_core_web_sm")
    #lemmatizer = nlp.get_pipe("lemmatizer")
    return nlp

def build_entity(token) -> str:
    output = ""

    for child in token.children:
        output += build_entity(child)

    if token.dep_ in ["xcomp", "amod", "case", "acomp", "nummod"]:
        output = f"{token} {output}"
    elif token.dep_ in ["dobj", "pobj", "attr"]:
        output = f"{output} {token}"
    elif token.dep_ in ["poss"]:
        output = f"{token}{output}"
        
    return output

def get_entity_type(token) -> EntityType:
    return EntityType.INSTANCE if token.pos_ == "PROPN" else EntityType.TYPE


def main():
    user = input("Please insert your username: ")
    kb = KnowledgeBase("bolt://localhost:7687", "neo4j", "Sussy_baka123321")
    # kb.delete_all()
    confidence_table = ConfidenceTable(kb)
    nlp = init()
    print("(!) Hello, how can I help you? (q! - quit)")
    while True:
        text = input("# ")
        if text.lower() == "q!":
            break

        # Do stuff with text
        doc = nlp(text)

        # --------- DEBUG: SHOW TREE ---------
        # displacy.serve(doc, auto_select_port=True, style="dep")

        # Check if phrase is a question or not
        
        # If is a question
        
        word = text.split(" ")[0]
        
        if word[0].lower() in ["what", "where", "who"] or text[-1].lower() in ["?"]:
            query_knowledge(user, doc, kb)
            # confidence_table.get_relation_confidence(Relation())
        else:
            add_knowledge(user, doc, kb)
            confidence_table.register_declarator(user)
            confidence_table.update_confidences()


        # Output text based on stuff that was done
        
# What Diogo like?
# What does Diogo like?
# What Diogo's dog eat?

# What does <entity> <rel>?
# Does <entity1> <rel> <entity2>? Example: does Joana eat bananas?
def query_knowledge(user:str, doc, kb: KnowledgeBase):
    
    for token in doc:
        print(token, token.pos_, list(token.children), token.dep_)
    
    root = [token for token in doc if token.head == token][0]
    
    possible_subjects = [token for token in root.children if token.dep_ == "nsubj"] # What Diogo likes VS What does Diogo likes
    
    # Boolean question specific use cases (that for some reason treats "like" as preposition)
    # e.g.: "Does Diogo like rice?"
    if len(possible_subjects) == 0:
        nsubject = root
        rel = [token for token in root.children if token.dep_ == "prep"][0]
        entity2 = [token for token in rel.children if token.dep_ == "pobj"][0]
        
        print(f"Question triplet: {nsubject}, {rel}, {entity2}")
        return query_boolean(nsubject, rel, entity2, kb)
    
    
    nsubject = possible_subjects[0]

    # Verify possessives
    possessives = [child for child in nsubject.children if child.dep_ == "poss"]

    # base entities and rel
    entity1 = possessives[0] if possessives else nsubject # TODO change to get object ("Diogo's dog" is returning only "dog")
    rel = nsubject if possessives else root.lemma_
    entity2 = [child for child in root.children if child.dep_ == "dobj" and child.pos_.lower() != "pron"]
    
    # Not a boolean question
    if len(entity2) == 0:
    
        # entity2 = build_entity(nobj) entity 2 only for boolean questions maybe?
        
        
        # kb_type = RelType.INHERITS if str(rel) == "is" else RelType.OTHER
        
        print(f"Question dupla: {nsubject}, {rel}")
        
        
        query = kb.query_inheritance_relation(str(entity1), str(rel))
        
        return entity1, rel, query
    else:
        print(f"Question tripla bool: {nsubject}, {rel}, {entity2}")
        
        return query_boolean(entity1, rel, entity2[0], kb)
            

def query_boolean(ent1, rel, ent2, kb:KnowledgeBase):
    relation = Relation(str(ent1), None, str(ent2), None, str(rel), None)
    print(f"{relation=}")
    return kb.assert_relation_inheritance(relation)

def add_knowledge(user:str, doc, kb: KnowledgeBase):
    print("TEST")
    ###### RULES OF (not) WACKY STUFF ######

    # identify ent1 by nsubj dependency, or poss if nsubj has poss childfor child in nobj.children:

    # identify rel by root verb, or nsubj if nsubj has poss child

    # identify ent2 by dobj or pobj dependency, or attr

    # add xcomp and amod dependencies to ent2
    # add prt dependencies to rel
    # add conj dependencies to associated tokens 
    
    #######################################

    # ------ DEBUG PRINT -----
    for token in doc:
        print(token, token.pos_, list(token.children), token.dep_)

    knowledge = []

    root = [token for token in doc if token.head == token][0]

    nsubject = list(root.lefts)[0] # Está na documentação -- Lucius. Mentirosos >:(
    nobj = list(root.rights)[0] if list(root.rights) else root.lemma_

    # Verify possessives
    possessives = [child for child in nsubject.children if child.dep_ == "poss"]

    # base entities and rel
    entity1 = Entity(nsubject)
    relation = root.lemma_
    relation_negated = 'neg' in [child.dep_ for child in root.children]
    entity2 = Entity(nobj)
    print("NSUBJ")
    for child in reversed(list(nsubject.children)):
        print(f"{child} {child.pos_} {child.dep_}")
        if child.dep_ == "poss":
            ent2 = copy(entity1)
            entity1 = entity1.prefix(Entity(child).append([c for c in child.children if c.dep_ == "case"][0]))
            rel = "Instance"
            triplet = Triples(ent1=entity1, ent2=ent2, rel=rel)
            knowledge.append(triplet)

            ent1 = Entity(child)
            ent2 = entity1#.prefix(child)
            rel = "has"
            triplet = Triples(ent1=ent1, ent2=ent2, rel=rel)
            knowledge.append(triplet)
        elif child.dep_ == "amod":
            entity1.prefix(child)
        elif nsubject.dep_ == "xcomp" and child.dep_ == "dobj":
            entity1.sufix(child)
    print("NOBJ")
    for child in reversed(list(nobj.children)):
        print(f"{child} {child.pos_} {child.dep_}")
        if child.dep_ == "poss":
            ent2 = copy(entity2)
            entity2 = entity2.prefix(Entity(child).append([c for c in child.children if c.dep_ == "case"][0]))
            rel = "Instance"
            triplet = Triples(ent1=entity2, ent2=ent2, rel=rel)
            knowledge.append(triplet)

            ent1 = Entity(child)
            ent2 = entity2#.prefix(child)
            rel = "has"
            triplet = Triples(ent1=ent1, ent2=ent2, rel=rel)
            knowledge.append(triplet)
        elif child.dep_ == "amod":
            entity2.prefix(child)
        elif nobj.dep_ == "xcomp" and child.dep_ == "dobj":
            entity2.sufix(child)

    base_triplet = Triples(entity1, entity2, relation)
    base_triplet.not_ = relation_negated
    knowledge.append(base_triplet)

    # add other tokens
    
    # if nobj.dep_ == "xcomp":
    #     entity2 += f" {str(nobj.children[0])}"
    # elif nobj.dep_ in ["dobj", "pobj"]:
    #     entity2 = f"{str(nobj.children[0])} {entity2}"

    # hotashi's    gameplay
    # POSS   CASE  DOBJ 
    
    for k in knowledge:
        print(k)
    
    # Whats this?
    kb_type = RelType.INHERITS if str(relation) == "be" else RelType.OTHER
    ent1_type = get_entity_type(entity1)
    ent2_type = get_entity_type(entity2)
    
    new_relation = Relation(str(entity1), ent1_type, str(entity2).strip(), ent2_type, str(relation), kb_type, not_=relation_negated)

    kb.add_knowledge(user, new_relation)

    return knowledge


if __name__ == '__main__':
    main()
    