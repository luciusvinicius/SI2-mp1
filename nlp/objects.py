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
        #self.pos_ = name.pos_

    def prefix(self, val):
        self.name = f"{val} {self.name}"

    def sufix(self, val):
        self.name = f"{self.name} {val}"

    def __repr__(self) -> str:
        return self.name