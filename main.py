import spacy
from spacy import displacy
from typing import Dict, List
#from sn.kb import KnowledgeBase

# namedtuple?
class Triples:
    def __init__(self, ent1, ent2, rel) -> None:
        self.ent1 = ent1
        self.ent2 = ent2
        self.rel = rel

    def __hash__(self) -> int:
        return hash(self.ent1) + hash(self.ent2) + hash(self.rel)


def init() -> spacy.Language:
    nlp = spacy.load("en_core_web_sm")
    #lemmatizer = nlp.get_pipe("lemmatizer")
    return nlp

def build_entity(token) -> str:
    output = ""

    for child in token.children:
        output += build_entity(child)

    if token.dep_ in ["xcomp", "amod"]:
        output = f"{token} {output}"
    elif token.dep_ in ["dobj", "pobj", "poss", "attr"]:
        output = f"{output} {token}"
    
    return output
        

def main():
    # kb = KnowledgeBase("bolt://localhost:7687", "neo4j", "Sussy_baka123321")
    nlp = init()
    print("(!) Hello, how can I help you? (q! - quit)")
    while True:
        text = input("# ")
        if text.lower() == "q!":
            break

        # Do stuff with text
        doc = nlp(text)

        # --------- DEBUG: SHOW TREE ---------
        #displacy.serve(doc, auto_select_port=True, style="dep")


        ###### RULES OF (not) WACKY STUFF ######

        # identify ent1 by nsubj dependency, or poss if nsubj has poss child

        # identify rel by root verb, or nsubj if nsubj has poss child

        # identify ent2 by dobj or pobj dependency, or attr

        # add xcomp and amod dependencies to ent2
        # add prt dependencies to rel
        # add conj dependencies to associated tokens 
        
        #######################################

        root = [token for token in doc if token.head == token][0]
        nsubject = list(root.lefts)[0] # Está na documentação -- Lucius. Mentirosos >:(
        nobj = list(root.rights)[0]

        # Verify possessives
        possessives = [child for child in nsubject.children if child.dep_ == "poss"]

        # base entities and rel
        entity1 = possessives[0] if possessives else nsubject
        rel = nsubject if possessives else root
        entity2 = build_entity(nobj)

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
        

        print(f"Triplet cringe: {entity1}, {rel}, {entity2}")
        print("Triplet cringier:", entity1, rel, entity2, sep=", ")


        # Output text based on stuff that was done



if __name__ == '__main__':
    main()
    