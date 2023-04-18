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
The dog has been selectively bred over millennia for various behaviors, sensory capabilities, and physical attributes.[12] Dog breeds vary widely in shape, size, and color. They perform many roles for humans, such as hunting, herding, pulling loads, protection, assisting police and the military, companionship, therapy, and aiding disabled people. Over the millennia, dogs became uniquely adapted to human behavior, and the human-canine bond has been a topic of frequent study.[13] This influence on human society has given them the sobriquet of "man's best friend".[14]
In 1758, the Swedish botanist and zoologist Carl Linnaeus published in his Systema Naturae, the two-word naming of species (binomial nomenclature). Canis is the Latin word meaning "dog",[15] and under this genus, he listed the domestic dog, the wolf, and the golden jackal. He classified the domestic dog as Canis familiaris and, on the next page, classified the grey wolf as Canis lupus.[2] Linnaeus considered the dog to be a separate species from the wolf because of its upturning tail (cauda recurvata), which is not found in any other canid.[16]
In 1999, a study of mitochondrial DNA (mtDNA) indicated that the domestic dog may have originated from the grey wolf, with the dingo and New Guinea singing dog breeds having developed at a time when human communities were more isolated from each other.[17] In the third edition of Mammal Species of the World published in 2005, the mammalogist W. Christopher Wozencraft listed under the wolf Canis lupus its wild subspecies and proposed two additional subspecies, which formed the domestic dog clade: familiaris, as named by Linnaeus in 1758 and, dingo named by Meyer in 1793. Wozencraft included hallstromi (the New Guinea singing dog) as another name (junior synonym) for the dingo. Wozencraft referred to the mtDNA study as one of the guides informing his decision.[3] Mammalogists have noted the inclusion of familiaris and dingo together under the "domestic dog" clade[18] with some debating it.[19]
In 2019, a workshop hosted by the IUCN/Species Survival Commission's Canid Specialist Group considered the dingo and the New Guinea singing dog to be feral Canis familiaris and therefore did not assess them for the IUCN Red List of Threatened Species.[4]
The Cretaceous-Paleogene extinction event occurred 66 million years ago and brought an end to the non-avian dinosaurs and the appearance of the first carnivorans.[20] The name carnivoran is given to a member of the order Carnivora. Carnivorans possess a common arrangement of teeth called carnassials, in which the first lower molar and the last upper premolar possess blade-like enamel crowns that act similar to a pair of shears for cutting meat. This dental arrangement has been modified by adaptation over the past 60 million years for diets composed of meat, for crushing vegetation, or for the loss of the carnassial function altogether as in seals, sea lions, and walruses. Today, not all carnivorans are carnivores, such as the insect-eating aardwolf.[5]
The carnivoran ancestors of the dog-like caniforms and the cat-like feliforms began their separate evolutionary paths just after the end of the dinosaurs. The first members of the dog family Canidae appeared 40 million years ago,[21] of which only its subfamily the Caninae survives today in the form of the wolf-like and fox-like canines. Within the Caninae, the first members of genus Canis appeared six million years ago,[15] the ancestors of modern domestic dogs, wolves, coyotes, and golden jackals.
The earliest remains generally accepted to be those of a domesticated dog were discovered in Bonn-Oberkassel, Germany. Contextual, isotopic, genetic, and morphological evidence shows that this dog was not a local wolf.[22] The dog was dated to 14,223 years ago and was found buried along with a man and a woman, all three having been sprayed with red hematite powder and buried under large, thick basalt blocks. The dog had died of canine distemper.[23] Earlier remains dating back to 30,000 years ago have been described as Paleolithic dogs, but their status as dogs or wolves remains debated[24] because considerable morphological diversity existed among wolves during the Late Pleistocene.[1]
This timing indicates that the dog was the first species to be domesticated[9][8] in the time of hunter–gatherers,[7] which predates agriculture.[1] DNA sequences show that all ancient and modern dogs share a common ancestry and descended from an ancient, extinct wolf population which was distinct from the modern wolf lineage.[6][7] Most dogs form a sister group to the remains of a Late Pleistocene wolf found in the Kessleroch cave near Thayngen in the canton of Schaffhausen, Switzerland, which dates to 14,500 years ago. The most recent common ancestor of both is estimated to be from 32,100 years ago.[25] This indicates that an extinct Late Pleistocene wolf may have been the ancestor of the dog,[8][1][26] with the modern wolf being the dog's nearest living relative.[8]
The dog is a classic example of a domestic animal that likely travelled a commensal pathway into domestication.[24][27] The questions of when and where dogs were first domesticated have taxed geneticists and archaeologists for decades.[9] Genetic studies suggest a domestication process commencing over 25,000 years ago, in one or several wolf populations in either Europe, the high Arctic, or eastern Asia.[10] In 2021, a literature review of the current evidence infers that the dog was domesticated in Siberia 23,000 years ago by ancient North Siberians, then later dispersed eastward into the Americas and westward across Eurasia.[22] 
"""
    
    print('Wikipedia')
    print(
        no_blanklines(
        no_references(
        separate_sentences(
        dog))))
    print('q!')
