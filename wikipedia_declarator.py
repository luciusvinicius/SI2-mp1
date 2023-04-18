import re


def separate_sentences(s: str) -> str:
    return re.sub(r'\.[ ]?', '\n', s)

def no_references(s: str) -> str:
    return re.sub(r'\[\d+\][ ]?', '', s)

def no_blanklines(s: str) -> str:
    return re.sub(r'\n[\n]+', '\n', s)

def no_tabs_or_whitespace(s: str) -> str:
    return re.sub(r'\t| ([ ]+)', '', s)


if __name__ == '__main__':
    dog = """The dog (Canis familiaris[4][5] or Canis lupus familiaris[5]) is a domesticated descendant of the wolf. Also called the domestic dog, it is derived from the extinct Pleistocene wolf,[6][7] and the modern wolf is the dog's nearest living relative.[8] Dogs were the first species to be domesticated[9][8] by hunter-gatherers over 15,000 years ago[7] before the development of agriculture.[1] Due to their long association with humans, dogs have expanded to a large number of domestic individuals[10] and gained the ability to thrive on a starch-rich diet that would be inadequate for other canids.[11]
The dog has been selectively bred over millennia for various behaviors, sensory capabilities, and physical attributes.[12] Dog breeds vary widely in shape, size, and color. They perform many roles for humans, such as hunting, herding, pulling loads, protection, assisting police and the military, companionship, therapy, and aiding disabled people. Over the millennia, dogs became uniquely adapted to human behavior, and the human–canine bond has been a topic of frequent study.[13] This influence on human society has given them the sobriquet of "man's best friend".[14] """
    
    print('Wikipedia')
    print(
        no_blanklines(
        no_references(
        separate_sentences(
        dog))))
    print('q!')
