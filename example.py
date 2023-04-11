import spacy

def init() -> spacy.Language:
    nlp = spacy.load("en_core_web_sm")
    #lemmatizer = nlp.get_pipe("lemmatizer")
    return nlp
