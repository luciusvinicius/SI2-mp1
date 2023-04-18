import spacy
import sys
from spacy import displacy
#from textblob import TextBlob, Sentence
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
from nlp.responses import *

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
    confidence_table = ConfidenceTable(kb, saf_weight=0.5, nsaf_weight=0.5, base_confidence=0.8)
    confidence_table.register_declarator('Wikipedia', static_confidence=1.0)
    for declarator in kb.get_all_declarators():
        confidence_table.register_declarator(declarator)
    nlp = init()
    print("(!) Hello, how can I help you? (q! - quit)")
    while True:
        text = input("# ")
        if text.lower() == "q!":
            print("(!) Bye bye!")
            break
        if len(text.strip()) == 0:
            continue

        # don't ask why
        if text.lower().startswith("does"):
            text = text[0].upper() + text[1:]

        # Do stuff with text
        doc = nlp(text)

        # --------- DEBUG: SHOW TREE ---------
        displacy.serve(doc, auto_select_port=True, style="dep")

        # Check if phrase is a question or not
        
        # If is a question
        
        word = text.split(" ")[0]

        respond_to_query = True
        
        try:
            if word[0].lower() in ["what", "where", "who"] or text[-1].lower() in ["?"]:
                content, bool_query = query_knowledge(user, doc, kb)
                #print(content)
            else:
                respond_to_query = False
                knowledge = add_knowledge(user, doc, kb)
                #print(knowledge)
                confidence_table.register_declarator(user)
                confidence_table.update_confidences()
        except:
            print("Sorry, I didn't understand that. Maybe try rephrasing your sentence?")
        else:
            # Output text based on stuff that was done
            if respond_to_query:
                if bool_query:
                    confidence = 0
                    confidence_n = 0
                    entity1, rel, entity2, negated, query = content
                    
                    # We can perform these boolean queries in two ways:
                    # - Unknown -> then it's False: if no declarations are present, then include inverse relations
                    # - Unknown -> conclude nothing: if no declarations are present, then don't bother with inverse relations
                    # For instance, if we say "person doesn't like beans" and ask "does person like beans?" we will get "No" and "Don't know" respectively.
                    # The code below, which includes the results from the inverse query, implements the first case.
                    inverse_query = kb.assert_relation_inheritance(Relation(
                        ent1=str(entity1),
                        ent1_type=None,
                        ent2=str(entity2),
                        ent2_type=None,
                        name=str(rel),
                        type_=None,
                        not_=not negated
                    ))

                    for (entity1_parent, length) in (query | inverse_query):
                        relation = Relation(
                            ent1=str(entity1_parent),
                            ent1_type=None,
                            ent2=str(entity2),
                            ent2_type=None,
                            name=str(rel),
                            type_=None,
                            not_=negated
                        )
                    
                        # We completely trust the user if they are asking about something that they declared
                        if kb.assert_relation(relation, declarator=user):
                            # If it was a local assertion, then we have complete confidence
                            if length == 0:
                                confidence = 1.0
                                confidence_n = 1
                                break
                            else:
                                confidence += 1.0
                        else:
                            confidence += confidence_table.get_relation_confidence(relation)
                        confidence_n += 1

                    response = bool_response(confidence / confidence_n if confidence_n > 0 else None)

                else:
                    confidence = 0
                    confidence_n = 0
                    rel = content[1]
                    for entity1, (entity2s, length) in content[2].items():
                        for entity2, positive in entity2s:
                            relation = Relation(
                                    ent1=entity1,
                                    ent1_type=None,
                                    ent2=entity2,
                                    ent2_type=None,
                                    name=rel,
                                    type_=None,
                                    not_=not positive
                                )
                            
                            # We completely trust the user if they are asking about something that they declared
                            if kb.assert_relation(relation, declarator=user):
                                confidence += 1.0
                            else:
                                confidence += confidence_table.get_relation_confidence(relation)
                            confidence_n += 1

                    response = complex_response(content, confidence / confidence_n if confidence_n > 0 else None)
            else:
                response = new_knowledge_response()
            print(response)
        
# What Diogo like?
# What does Diogo like?
# What Diogo's dog eat?

# What does <entity> <rel>?
# Does <entity1> <rel> <entity2>? Example: does Joana eat bananas?
def query_knowledge(user:str, doc, kb: KnowledgeBase):
    bool_query = False
    
    for token in doc:
        print(token, token.pos_, list(token.children), token.dep_)
    
    root = [token for token in doc if token.head == token][0]
    
    possible_subjects = [token for token in root.children if token.dep_ == "nsubj"] # What Diogo likes VS What does Diogo likes
    
    relation_negated = 'neg' in [child.dep_ for child in root.children]

    # Boolean question specific use cases (that for some reason treats "like" as preposition)
    # e.g.: "Does Diogo like rice?"
    if len(possible_subjects) == 0:
        bool_query = True
        if root.lemma_ == "be":
            nsubject = [token for token in root.children if token.dep_ == "attr"][0]
            rel = root.lemma_
            entity2 = [token for token in nsubject.children if token.dep_ == "amod"][0]
        else:
            nsubject = root
            rel = [token for token in doc if token.dep_ == "prep"][0]
            entity2 = [token for token in rel.children if token.dep_ == "pobj"][0]
        
        # print(f"Question triplet: {nsubject}, {rel}, {entity2}")

        ent1 = extract_entity(Entity(root), nsubject, [])
        ent2 = extract_entity(Entity(entity2), entity2, [])

        query = query_boolean(ent1, rel, ent2, kb)

        print(f"Question triplet particular: {ent1}, {rel}, {ent2}")
        return (ent1, rel, ent2, relation_negated, query), bool_query
    
    nsubject = possible_subjects[0]

    # Verify possessives
    possessives = [child for child in nsubject.children if child.dep_ == "poss"]

    #print(nsubject)
    #print(possessives)
    #print("Full entity:", extract_entity(Entity(nsubject), nsubject, []))


    # base entities and rel
    #entity1 = possessives[0] if possessives else nsubject # TODO change to get object ("Diogo's dog" is returning only "dog")
    entity1 = nsubject
    rel = nsubject if possessives else root.lemma_
    entity2 = [child for child in root.children if child.dep_ == "dobj" and child.pos_.lower() != "pron"]

    relation_negated = 'neg' in [child.dep_ for child in root.children]

    print("ENT2", entity2, len(entity2))

    # Not a boolean question
    if len(entity2) == 0:
        
        ent = str(extract_entity(Entity(entity1), nsubject, []))
        print(ent, nsubject, nsubject.pos_, nsubject.text)
        if nsubject.pos_ == "PROPN" and ent.lower() == nsubject.text.lower():
            ent = ent.capitalize()
        rel = root.lemma_

        print(f"Question dupla: {ent}, {rel}")
        
        query = kb.query_inheritance_relation(ent, str(rel))
        print(query)
        
        return (entity1, rel, query), bool_query
    else:
        ent1 = str(extract_entity(Entity(entity1), nsubject, []))
        ent2 = str(extract_entity(Entity(entity2[0]), nsubject, []))
        print("B4")
        if nsubject.pos_ == "PROPN" and ent1.lower() == nsubject.text.lower():
            ent1 = ent1.capitalize()
        print("A")
        if nsubject.pos_ == "PROPN" and ent2.lower() == nsubject.text.lower():
            ent2 = ent2.capitalize()
        print("B")
        print(f"Question tripla bool: {ent1}, {rel}, {ent2}")
        
        query = query_boolean(ent1, rel, ent2, kb, relation_negated)

        # TODO: shouldn't bool_query be True here?
        return (ent1, rel, ent2, relation_negated, query), True
            

def query_boolean(ent1, rel, ent2, kb:KnowledgeBase, not_:bool=False):
    relation = Relation(str(ent1), None, str(ent2), None, str(rel), None, not_)
    #print(f"{relation=}")
    return kb.assert_relation_inheritance(relation)

def add_knowledge(user:str, doc, kb: KnowledgeBase):
    # print("TEST")
    ###### RULES OF (not) WACKY STUFF ######

    # identify ent1 by nsubj dependency, or poss if nsubj has poss childfor child in nobj.children:

    # identify rel by root verb, or nsubj if nsubj has poss child

    # identify ent2 by dobj or pobj dependency, or attr

    # add xcomp and amod dependencies to ent2
    # add prt dependencies to rel
    # add conj dependencies to associated tokens 
    
    #######################################

    # ------ DEBUG PRINT -----
    # for token in doc:
    #     print(token, token.pos_, list(token.children), token.dep_)

    knowledge = []

    root = [token for token in doc if token.head == token][0]

    nsubject = list(root.lefts)[0] # Está na documentação -- Lucius. Mentirosos >:(

    # Verify possessives
    # TODO: possessives not used
    possessives = [child for child in nsubject.children if child.dep_ == "poss"]
    adp = [child for child in root.children if child.pos_ == "ADP"]
    # base entities and rel
    entity1 = Entity(nsubject)
    relation = f"{root.lemma_} {adp[0].lemma_}" if adp else root.lemma_
    relation_negated = 'neg' in [child.dep_ for child in root.children]

    if adp and list(adp[0].rights):
        nobj = list(adp[0].rights)[0]
    elif list(root.rights):
        nobj = list(root.rights)[0]
    else:
        nobj = root

    entity2 = Entity(nobj)

    # print(entity1)
    # print(entity2)
    # print(root)

    # print("NSUBJ")
    children = list(reversed(list(nsubject.children)))
    for child in children:
        # print(f"{child} {child.pos_} {child.dep_}")
        if child.dep_ == "poss":
            ent2 = copy(entity1)
            entity1 = entity1.prefix(Entity(child).append([c for c in child.children if c.dep_ == "case"][0]))
            rel = "Instance"
            triplet = Triples(ent1=entity1, ent2=ent2, rel=rel)
            triplet.not_ = False
            knowledge.append(triplet)

            ent1 = Entity(child)
            ent2 = entity1#.prefix(child)
            rel = "have"
            triplet = Triples(ent1=ent1, ent2=ent2, rel=rel)
            triplet.not_ = False
            knowledge.append(triplet)
        elif child.dep_ in ["amod", "npadvmod", "nummod"]:
            entity1.prefix(child)
            new_children = child.children
            children.extend(new_children)
        elif nsubject.dep_ == "xcomp" and child.dep_ == "dobj":
            entity1.sufix(child)
    # print("NOBJ")
    children = list(reversed(list(nobj.children)))
    for child in children:
        # print(f"{child} {child.pos_} {child.dep_}")
        if child.dep_ == "poss":
            ent2 = copy(entity2)
            entity2 = entity2.prefix(Entity(child).append([c for c in child.children if c.dep_ == "case"][0]))
            rel = "Instance"
            triplet = Triples(ent1=entity2, ent2=ent2, rel=rel)
            triplet.not_ = False
            knowledge.append(triplet)

            ent1 = Entity(child)
            ent2 = entity2#.prefix(child)
            rel = "have"
            triplet = Triples(ent1=ent1, ent2=ent2, rel=rel)
            triplet.not_ = False
            knowledge.append(triplet)
        elif child.dep_ in ["amod", "npadvmod", "nummod"]:
            entity2.prefix(child)
            new_children = child.children
            children.extend(new_children)
        elif nobj.dep_ == "xcomp" and child.dep_ == "dobj":
            entity2.sufix(child)
    # print('Negated?', 'Yes' if relation_negated else 'No')

    base_triplet = Triples(entity1, entity2, relation)
    base_triplet.not_ = relation_negated
    knowledge.append(base_triplet)

    
    for k in knowledge:
        # print(k)
        kb_type = RelType.INHERITS if str(k.rel) in ["be", "Instance"] else RelType.OTHER
        ent1_type = get_entity_type(k.ent1)
        ent2_type = get_entity_type(k.ent2)
        
        # TODO: lowercase entity names if they are TYPEs? ('Beans' and 'beans' will be different)
        new_relation = Relation(str(k.ent1), ent1_type, str(k.ent2).strip(), ent2_type, str(k.rel), kb_type, not_=k.not_)
        kb.add_knowledge(user, new_relation)

    return knowledge


def extract_entity(entity, subject, knowledge):
    children = list(reversed(list(subject.children)))
    for child in children:
        # print(f"{child} {child.pos_} {child.dep_}")
        if child.dep_ == "poss":
            ent2 = copy(entity)
            entity = entity.prefix(Entity(child).append([c for c in child.children if c.dep_ == "case"][0]))
            rel = "Instance"
            triplet = Triples(ent1=entity, ent2=ent2, rel=rel)
            triplet.not_ = False
            knowledge.append(triplet)

            ent1 = Entity(child)
            ent2 = entity#.prefix(child)
            rel = "have"
            triplet = Triples(ent1=ent1, ent2=ent2, rel=rel)
            triplet.not_ = False
            knowledge.append(triplet)
        elif child.dep_ in ["amod", "npadvmod", "nummod"]:
            entity.prefix(child)
            new_children = child.children
            children.extend(new_children)
        elif subject.dep_ == "xcomp" and child.dep_ == "dobj":
            entity.sufix(child)
    
    return entity



if __name__ == '__main__':
    main()
    