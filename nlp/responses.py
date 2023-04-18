import random

def bool_response(confidence):
    if confidence is None:
        choices = [
            "I have no information regarding that.",
            "I don't know anything about that.",
            "I have no idea."
        ]

    elif confidence > 0.85:
        choices = [
            "Most certainly correct!",
            "Exactly right.",
            "According to most users and trusted sources, that's correct.",
            "Decidedly so."
        ]
    
    elif confidence > 0.7:
        choices = [
            "The data seems to indicate so.",
            "Apparently so.",
            "According to some users, that's correct."
        ]
    
    elif confidence > 0.6:
        choices = [
            "With some degree of uncertainty, yes.",
            "As far as my knowledge goes, that's correct, but I need more data to be sure.",
            "Some users have previously confirmed that, but more input is needed."
        ]

    elif confidence > 0.4:
        choices = [
            "I'm not sure at all.",
            "I can't be certain about that.",
            "Maybe, maybe not."
        ]

    elif confidence > 0.3:
        choices = [
            "Hard to be sure, but that doesn't seem to be correct.",
            "As far as my knowledge goes, that's incorrect, but I need more data to be sure.",
            "Some users have previously denied that, but more input is needed."
        ]

    elif confidence > 0.15:
        choices = [
            "The data seems to indicate not.",
            "Apparently that's not right.",
            "According to some users, that's incorrect."
        ]

    else:
        choices = [
            "Incorrect.",
            "Not true.",
            "According to most users and trusted sources, that's not correct.",
            "Factually wrong."
        ]

    return random.choice(choices)
    
def complex_response(content, confidence):
    if confidence is None:
        choices = [
            "I have no information regarding that.",
            "I don't know anything about that."
            "I have no idea."
        ]

    entity = content[3]
    relationship = content[1]
    if not content[2]:
        choices = [
            f"I have no information on what/where {entity} {relationship}, maybe you can tell us something about it?",
            "Not much info on that, maybe ask me later!",
            "I don't know much about that, I'll be sure to ask others what they think!",
        ]
    else:
        target_entities = [object for entity in content[2].keys() for object in content[2][entity][0]]
        target_entities_string = str(target_entities[0][0]) if len(target_entities) == 1 else ''.join([("" if target_entities[i][1] else "not ") + str(target_entities[i][0]) + ", " for i in range(len(target_entities)-1)]) + "and " + str(target_entities[-1][0])
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