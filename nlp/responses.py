import random

def bool_response(value, confidence):
    if confidence > 0.85:
        if value:
            choices = [
                "Most certainly correct!",
                "Exactly right.",
                "According to most users and some trusted sources, that's correct.",
                "Decidedly so."
            ]
        else:
            choices = [
                "Incorrect.",
                "Not true.",
                "According to most users and some trusted sources, that's not correct.",
                "Factually wrong."
            ]
    elif confidence > 0.6:
        if value:
            choices = [
                "The data seems to indicate so.",
                "Apparently so.",
                "According to some users, that's correct."
            ]
        else:
            choices = [
                "The data seems to indicate not.",
                "Apparently that's not right.",
                "According to some users, that's incorrect."
            ]
    else:
        if value:
            choices = [
                "With some degree of uncertainty, yes.",
                "As far as my knowledge goes, that's correct, but I need more data to be sure.",
                "Some users have previously confirmed that, but more input is needed."
            ]
        else:
            choices = [
                "Hard to be sure, but that doesn't seem to be correct.",
                "As far as my knowledge goes, that's incorrect, but I need more data to be sure.",
                "Some users have previously denied that, but more input is needed."
            ]
    return random.choice(choices)
    
def complex_response(content, confidence):
    entity = content[0]
    relationship = content[1]
    if not content[2]:
        choices = [
            f"I have no information on whether/what {entity} {relationship}, maybe you can tell us something about it?",
            "Not much info on that, maybe ask me later!",
            "I don't know much about that, I'll be sure to ask others what they think!",
        ]
    else:
        # TODO: not considering inheritance
        target_entities = list(content[2][str(entity)][0])
        target_entities_string = str(target_entities[0][0]) if len(target_entities) == 1 else ''.join([str(target_entities[i][0]) + ", " for i in range(len(target_entities)-1)]) + "and " + str(target_entities[-1][0])
        if confidence > 0.85:
            choices = [
                f"I am quite sure {entity} does {relationship} {target_entities_string}.",
                f"Overwhelmingly, our sources indicate {entity} does {relationship} {target_entities_string}.",
                f"Most users affirm {entity} does {relationship} {target_entities_string}."
            ]
        elif confidence > 0.6:
            choices = [
                f"My knowledge seem to indicate {entity} does {relationship} {target_entities_string}.",
                f"Apparently {entity} does {relationship} {target_entities_string}.",
                f"Some users have affirmed {entity} does {relationship} {target_entities_string}."
            ]
        else:
            choices = [
                f"Unsure, but {entity} does seem to {relationship} {target_entities_string}.",
                f"A few of our sources indicate {entity} does {relationship} {target_entities_string}, but it's difficult to be sure.",
                f"A few users have previously said {entity} does {relationship} {target_entities_string}, but more data is needed."
            ]
    return random.choice(choices)

def new_knowledge_response():
    choices = [
        "Thanks for the input!",
        "I will take that into account in the future.",
        "This will surely enrich the knowledge pool.",
        "Interesting! I will pass on this information.",
        "Understood.",
        "Is that so? Uh!",
        "I will remember that in the future!"
    ]
    return random.choice(choices)