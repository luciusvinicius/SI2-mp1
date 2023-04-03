import spacy

def init():
    nlp = spacy.load("en_core_web_sm")
    return nlp


def main():
    nlp = init()
    print("(!) Hello, how can I help you? (q! - quit)")
    while True:
        text = input("# ")
        if text.lower() == "q!":
            break
        # Do stuff with text
        print(text)
        doc = nlp(text)
        for token in doc:
            print(token, token.pos_)

if __name__ == '__main__':
    main()
    