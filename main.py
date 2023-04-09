import spacy
from spacy import displacy
from typing import Dict, List
from sn.kb import KnowledgeBase, RelType, Relation
from sn.confidence import ConfidenceTable
from copy import copy

# namedtuple?
class Triples:
    def __init__(self, ent1, ent2, rel) -> None:
        self.ent1 = ent1
        self.ent2 = ent2
        self.rel = rel

    def __hash__(self) -> int:
        return hash(self.ent1) + hash(self.ent2) + hash(self.rel)

    
class Entity:
    def __init__(self, name) -> None:
        self.name = str(name)

    def prefix(self, val):
        self.name = f"{val} {self.name}"

    def sufix(self, val):
        self.name = f"{self.name} {val}"

    def __repr__(self) -> str:
        return self.name


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



def main():
    user = input("Please insert your username: ")
    kb = KnowledgeBase("bolt://localhost:7687", "neo4j", "Sussy_baka123321")
    kb.delete_all()
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
            confidence_table.get_relation_confidence(Relation())
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
    
    nsubject = [token for token in root.lefts if token.dep_ == "nsubj"][0] # What Diogo likes VS What does Diogo likes
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
    ###### RULES OF (not) WACKY STUFF ######

    # identify ent1 by nsubj dependency, or poss if nsubj has poss childfor child in nobj.children:

    # identify rel by root verb, or nsubj if nsubj has poss child

    # identify ent2 by dobj or pobj dependency, or attr

    # add xcomp and amod dependencies to ent2
    # add prt dependencies to rel
    # add conj dependencies to associated tokens 
    
    #######################################

    knowledge = []

    root = [token for token in doc if token.head == token][0]

    nsubject = list(root.lefts)[0] # Está na documentação -- Lucius. Mentirosos >:(
    nobj = list(root.rights)[0] if list(root.rights) else root.lemma_

    # Verify possessives
    possessives = [child for child in nsubject.children if child.dep_ == "poss"]

    # base entities and rel
    entity1 = Entity(possessives[0]) if possessives else Entity(nsubject)
    relation = nsubject if possessives else root.lemma_
    entity2 = Entity(nobj)

    for child in nobj.children:
        print(f"{child} {child.pos_} {child.dep_}")
        if child.dep_ == "poss":
            ent1 = copy(entity2)
            ent1.prefix(child)
            rel = "instance"
            ent2 = copy(entity2)
            triplet = Triples(ent1=ent1, ent2=ent2, rel=rel)
            knowledge.append(triplet)

            ent1 = child
            ent2 = entity2.prefix(child)
            rel = "has"
            triplet = Triples(ent1=ent1, ent2=ent2, rel=rel)
            knowledge.append(triplet)
        elif child.dep_ == "amod":
            entity2.prefix(child)
        elif child.dep_ == "xcomp":
            entity2.sufix(child)

    base_triplet = Triples(entity1, entity2, relation)
    knowledge.append(base_triplet)

    # for k in knowledge:
    #     print(k)

    # add other tokens
    
    # if nobj.dep_ == "xcomp":
    #     entity2 += f" {str(nobj.children[0])}"
    # elif nobj.dep_ in ["dobj", "pobj"]:
    #     entity2 = f"{str(nobj.children[0])} {entity2}"

    # hotashi's    gameplay
    # POSS   CASE  DOBJ 


    # ------ DEBUG PRINT -----
    for token in doc:
        print(token, token.pos_, list(token.children), token.dep_)

    kb_type = RelType.INSTANCE if str(relation) == "be" else RelType.OTHER
    
    new_relation = Relation(str(entity1), str(entity2).strip(), str(relation), kb_type)
    # print(f"{new_relation=}")

    kb.add_knowledge(user, new_relation)


if __name__ == '__main__':
    main()
    