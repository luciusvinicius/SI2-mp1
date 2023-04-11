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
    kb = KnowledgeBase("bolt://localhost:7686", "neo4j", "Sussy_baka123321")
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
def query_knowledge(user:str, doc, kb: KnowledgeBase):
    
    for token in doc:
        print(token, token.pos_, list(token.children), token.dep_)
    
    root = [token for token in doc if token.head == token][0]
    
    nsubject = [token for token in root.children if token.dep_ == "nsubj"][0] # What Diogo likes VS What does Diogo likes
    nobj = list(root.rights)[0]

    # Verify possessives
    possessives = [child for child in nsubject.children if child.dep_ == "poss"]

    # base entities and rel
    entity1 = possessives[0] if possessives else nsubject
    rel = nsubject if possessives else root.lemma_
    
    # entity2 = build_entity(nobj) entity 2 only for boolean questions maybe?
    
    
    
    print(f"Triplet cringe: {entity1}, {rel}")
    
    kb_type = RelType.INSTANCE if str(rel) == "is" else RelType.OTHER
    
    query = kb.query_inheritance_relation(str(entity1), str(rel))
    print(f"{query=}")
    
    return entity1, rel, query
    

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
    entity2 = Entity(nobj)
    print("NSUBJ")
    for child in reversed(list(nsubject.children)):
        print(f"{child} {child.pos_} {child.dep_}")
        if child.dep_ == "poss":
            ent1 = copy(entity1).prefix(child)
            rel = "Instance"
            ent2 = copy(entity1)
            triplet = Triples(ent1=ent1, ent2=ent2, rel=rel)
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
            ent1 = copy(entity2).prefix(child)
            rel = "Instance"
            ent2 = copy(entity2)
            triplet = Triples(ent1=ent1, ent2=ent2, rel=rel)
            knowledge.append(triplet)

            ent1 = Entity(child)
            ent2 = entity2.prefix(child)
            rel = "has"
            triplet = Triples(ent1=ent1, ent2=ent2, rel=rel)
            knowledge.append(triplet)
        elif child.dep_ == "amod":
            entity2.prefix(child)
        elif nobj.dep_ == "xcomp" and child.dep_ == "dobj":
            entity2.sufix(child)

    base_triplet = Triples(entity1, entity2, relation)
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
    
    new_relation = Relation(str(entity1), ent1_type, str(entity2).strip(), ent2_type, str(relation), kb_type)

    kb.add_knowledge(user, new_relation)

    return knowledge


if __name__ == '__main__':
    main()
    