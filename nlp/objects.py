class Triples:
    def __init__(self, ent1, ent2, rel) -> None:
        self.ent1 = ent1
        self.ent2 = ent2
        self.rel = rel

    def __hash__(self) -> int:
        return hash(self.ent1) + hash(self.ent2) + hash(self.rel)
    
    def __eq__(self, __o: object) -> bool:
        return self.rel == __o.rel and (
            (self.ent1 == __o.ent1 and self.ent2 == __o.ent2) or
            (self.ent1 == __o.ent2 and self.ent2 == __o.ent1)
        )
    
    def __repr__(self) -> str:
        return f"{self.ent1} -- {self.rel} -> {self.ent2}"

    
class Entity:
    def __init__(self, name, pos=True) -> None:
        self.name = str(name)
        self.pos_ = name.pos_ if pos else None

    def prefix(self, val):
        self.name = f"{val} {self.name}"
        return self

    def sufix(self, val):
        self.name = f"{self.name} {val}"
        return self

    def __repr__(self) -> str:
        return self.name
    
    def __eq__(self, __o: object) -> bool:
        return self.name == __o.name