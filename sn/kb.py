from dataclasses import dataclass
from neo4j import GraphDatabase, ManagedTransaction
from enum import Enum
from typing import Tuple, Dict, Union, Set


class EntityType(Enum):
    TYPE = "Type"
    INSTANCE = "Instance"

class RelType(Enum):
    INHERITS = "Inherits"
    OTHER = "Other"

# Decorator for read operations
def sn_read(read_method):
    def wrapper(self: 'KnowledgeBase', *args, **kwargs):
        with self.driver.session() as session:
            def include_tx_wrapper(tx, *args, **kwargs):
                return read_method(*args, **kwargs, tx=tx)
            return session.execute_read(include_tx_wrapper, *args, **kwargs)
    return wrapper

# Decorator for write operations
def sn_write(write_method):
    def wrapper(self: 'KnowledgeBase', *args, **kwargs):
        with self.driver.session() as session:
            def include_tx_wrapper(tx, *args, **kwargs):
                return write_method(*args, **kwargs, tx=tx)
            return session.execute_write(include_tx_wrapper, *args, **kwargs)
    return wrapper

@dataclass(frozen=True)
class Relation:
    """Knowledge base relation between two entities.
    
    Parameters
    ----------
    ent1 : str
        The first entity of the relation
    ent1_type : EntityType | None
        The type of the first entity, optional
    ent2 : str
        The second entity of the relation
    ent2_type : EntityType | None
        The type of the second entity, optional
    name : str
        The name of the relation
    type_ : RelType | None
        The type of the relation, optional
    not_ : bool
        Whether the relation is negated
    """

    ent1:       str
    ent1_type:  Union[EntityType, None]
    ent2:       str
    ent2_type:  Union[EntityType, None]
    name:       str
    type_:      Union[RelType, None]
    not_:       bool                    = False

    def __post_init__(self):
        object.__setattr__(self, 'ent1', f"n_{self.ent1}" if self.ent1.isdigit() else self.ent1)
        object.__setattr__(self, 'ent2', f"n_{self.ent2}" if self.ent2.isdigit() else self.ent2)

    def inverse(self) -> 'Relation':
        """Return the inverse of this relation, where the `not_` truth value is swapped."""
        return Relation(self.ent1, self.ent1_type, self.ent2, self.ent2_type, self.name, self.type_, not self.not_)
    
    def __str__(self) -> str:
        return f"({self.ent1})-[{self.name}]->({self.ent2})"

class KnowledgeBase:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()
    
    # ------------------------ Query Methods --------------------------
    # Methods for interacting with the knowledge base. Any value passed to the `tx` argument is ignored.
    # E.gs.: 
    # greeter.delete_all()
    # greeter.add_knowledge("Lucius", "Diogo", "Cringe", RelType.OTHER, "is")

    @sn_write
    @staticmethod
    def add_knowledge(declarator: str, relation: Relation, tx: ManagedTransaction=None):
        """`declarator` states that `relation.ent1` has a `relation.name` with `relation.ent2`.
        `relation.type_` is one of 2 types:
            - INHERITS: (Diogo is a Person).
            - OTHER: Literally any other relation.
            
        Use `RelType` enum to specify which one.
        
        `relation.name` is the name given to the relation, and is only relevant with the OTHER relation type.

        `relation` should not have `None` values for the type fields.

        If the declaration of the inverse relation already exists, then it is replaced by the new declaration.
        """
        
        if relation.type_ == RelType.INHERITS and relation.ent2_type != EntityType.TYPE:
            raise ValueError("Can only inherit from types entities.")

        if relation.ent1_type is None or relation.ent2_type is None or relation.type_ is None:
            raise ValueError("Relation and entity types shold not be None.")

        # If the inverse relation already exists, then remove it first to avoid conflicting declarations
        inverse_relation = relation.inverse()
        if KnowledgeBase._tx_assert_relation_exists(inverse_relation, tx):
            tx.run(f"MATCH (:{inverse_relation.ent1_type.value} {{name: $ent1}})-[r:{inverse_relation.type_.value} {{declarator: $declarator, name: $relation, not: $not_}}]->(:{inverse_relation.ent2_type.value} {{name: $ent2}})" 
                   "DELETE r", ent1=inverse_relation.ent1, declarator=declarator, relation=inverse_relation.name, not_=inverse_relation.not_, ent2=inverse_relation.ent2)

        result = tx.run(f"MERGE (e1:{relation.ent1_type.value} {{name: $ent1}}) "
                        f"MERGE (e2:{relation.ent2_type.value} {{name: $ent2}}) "
                        f"MERGE (e1)-[r:{relation.type_.value} {{declarator: $declarator, name: $relation, not: $not_}}]->(e2) "
                        "RETURN e1.name", declarator=declarator, ent1=relation.ent1, ent2=relation.ent2, relation=relation.name, not_=relation.not_)
        
        return result.single()[0]
    
    @sn_read
    @staticmethod
    def query_declarations(declarator:str, tx: ManagedTransaction=None) -> Set[Relation]:
        """Query a declarator to obtain all declarations made by it.
        Output: `[relation1, relation2, (...)]`
        """
        results = tx.run("MATCH (e1)-[r {declarator: $declarator}]->(e2) "
                        "RETURN e1.name AS ent1, labels(e1)[0] AS ent1_type, type(r) AS relation_type, r.name AS relation, e2.name AS ent2, labels(e2)[0] AS ent2_type, r.not AS not", declarator=declarator)
        
        return {Relation(
            ent1=result.value("ent1"),
            ent1_type=EntityType(result.value("ent1_type")),
            ent2=result.value("ent2"),
            ent2_type=EntityType(result.value("ent2_type")),
            name=result.value("relation"),
            type_=result.value("relation_type"),
            not_=result.value("not")
        ) for result in results}

    @sn_read
    @staticmethod
    def query_declarators(relation: Relation, tx: ManagedTransaction=None) -> Set[str]:
        """Obtain all declarators that declared the given relation."""

        e1_label, e2_label, rel_type = KnowledgeBase._return_optional_labels(relation)

        results = tx.run(f"MATCH (e1{e1_label} {{name: $ent1}})-[r{rel_type} {{name: $relation, not: $not_}}]->(e2{e2_label} {{name: $ent2}}) "
                        "RETURN r.declarator AS declarator", ent1=relation.ent1, relation=relation.name, ent2=relation.ent2, not_=relation.not_)
        
        return {result.value("declarator") for result in results}

    @sn_read
    @staticmethod
    def query_local(ent:str, tx: ManagedTransaction=None) -> Set[Tuple[Tuple[str, str], Set[str]]]:
        """Query an entity to obtain the relations and its entities.
        Output: `[((relation_name, relation_type), [entity2, entity3]), (...)]`
        """
        
        results = tx.run("MATCH (eIn {name: $entIn})-[r]->(eOut)"
                        "RETURN r.name AS relation, type(r) AS relation_type, eOut.name AS other_entity", entIn=ent)

        result_dict = {}
        for result in results:
            relation = result.value("relation")
            relation_type = result.value("relation_type")
            other_entity = result.value("other_entity")

            result_dict.setdefault((relation, relation_type), set())
            result_dict[relation, relation_type].add(other_entity)

        result_dict = {k:frozenset(v) for k, v in result_dict.items()}

        return set(result_dict.items())

    @sn_read
    @staticmethod
    def query_local_relation(ent:str, relation:str, relation_type:RelType, tx: ManagedTransaction=None) -> Set[str]:
        """Query an entity to obtain the entities of a specific relation."""
        
        results = tx.run(f"MATCH (e {{name: $ent}})-[r:{relation_type.value} {{name: $relation}}]->(e2) "
                        "RETURN e2.name AS entity", ent=ent, relation=relation)
        
        return {result.value("entity") for result in results}
        
    # TODO: determine what the return format is
    @sn_read
    @staticmethod
    def query_inheritance(ent:str, tx: ManagedTransaction=None) -> Dict[str, Tuple[Set[str], int]]:
        """Query all local attributes of an entity as well as attributes inherited from INHERITS relations"""
        
        # logicks: query_local for ent + query_inheritance for ascendants
        
        # first: query_local on ent

        # second: get ascendants (INSTANCE/SUBTYPE rels)

        # third: query_inheritance on each ascendant and append result
        
        results = tx.run(
            f"MATCH (ent1 {{name:$ent}}) "
            "MATCH (ent1)-[r]->(ent2) "
            "RETURN ent1.name AS subject, collect(ent2.name) AS characteristics, 0 AS distance "
            "UNION "
            f"MATCH p = (ent1 {{name:$ent}})-[:{RelType.INHERITS.value} *1..]->(ascn) "
            "MATCH (ascn)-[r]->(ent2) "
            "RETURN ascn.name AS subject, collect(ent2.name) AS characteristics, length(p) AS distance", ent=ent
        )
        
        return {result.value('subject'):(frozenset(result.value('characteristics')), result.value('distance')) for result in results}

    @sn_read
    @staticmethod
    def query_inheritance_relation(ent:str, relation:str, declarator:str=None, tx: ManagedTransaction=None) ->  Dict[str, Tuple[Set[Tuple[str, bool]], int]]:
        """Query the specified attribute of an entity as well as attributes inherited from INSTANCE and SUBTYPE relations.
        The output is each Entity in the key, the characteristics, truth values and distance as the tuple elements"""
        
        # TODO: cypher injection
        declarator_filter = f", declarator: '{declarator}'" if declarator is not None else ""

        results = tx.run(
            f"MATCH (ent1 {{name:$ent}}) "
            f"MATCH (ent1)-[r {{name:$relation {declarator_filter}}}]->(ent2) "
            "RETURN ent1.name AS subject, collect(ent2.name) AS characteristics, collect(r.not) AS nots, 0 AS distance "
            "UNION "
            f"MATCH p = (ent1 {{name:$ent}})-[:{RelType.INHERITS.value} *1..]->(ascn) "
            f"MATCH (ascn)-[r {{name:$relation {declarator_filter}}}]->(ent2) "
            "RETURN ascn.name AS subject, collect(ent2.name) AS characteristics, collect(r.not) AS nots, length(p) AS distance", ent=ent, relation=relation
        )
        
        return {result.value('subject'):(frozenset(zip(result.value('characteristics'), [not n for n in result.value('nots')])), result.value('distance')) for result in results}

    @sn_read
    @staticmethod
    def query_descendants_relation(ent:str, relation:str, relation_type:RelType=None, not_:bool=False, tx: ManagedTransaction=None) -> Set[str]:
        """Query the specified *local* attribute of entity descendants"""
        
        rel_label = f':{relation_type.value}' if relation_type is not None else ''

        results = tx.run(f"MATCH (eOut)<-[{rel_label} {{name: $relation, not: $not_}}]-(desc)-[r:{RelType.INHERITS.value} *1..]->(eIn {{name: $entIn}}) "
                        "RETURN eOut.name AS other_entity", relation=relation, entIn=ent, not_=not_)

        return {result.value("other_entity") for result in results}

    @sn_read
    @staticmethod
    def assert_relation(relation: Relation, tx: ManagedTransaction=None) -> bool:
        """Assert whether or not `relation` exists in the knowledge base"""
        return KnowledgeBase._tx_assert_relation_exists(relation, tx)

    @sn_read
    @staticmethod
    def assert_relation_inheritance(relation: Relation, declarator: str=None, tx: ManagedTransaction=None) -> bool:
        """Assert whether or not `relation` exists in the knowledge base, with inheritance"""

        e1_label, e2_label, rel_label = KnowledgeBase._return_optional_labels(relation)
        declarator_filter = f", declarator: '{declarator}'" if declarator is not None else ""

        results = tx.run(
            f"RETURN exists(({e1_label} {{name: $ent1}})-[{rel_label} {{name: $relation, not: $not_ {declarator_filter}}}]->({e2_label} {{name: $ent2}})) AS relation_exists "
            "UNION ALL "
            f"MATCH (e1{e1_label} {{name: $ent1}})-[:{RelType.INHERITS.value} *1..]->(ascn) "
            f"RETURN exists((ascn)-[{rel_label} {{name: $relation, not: $not_}}]->({e2_label} {{name: $ent2}})) AS relation_exists", ent1=relation.ent1, ent2=relation.ent2, relation=relation.name, not_=relation.not_
        )

        return any(result.value("relation_exists") for result in results)

    @sn_read
    @staticmethod
    def get_all_declarators(tx: ManagedTransaction=None) -> Set[str]:
        """Get all unique declarators of knowledge."""

        results = tx.run(f"MATCH ()-[r]->() RETURN DISTINCT r.declarator AS declarator")

        return {result.value("declarator") for result in results}

    @sn_write
    @staticmethod
    def delete_all(tx: ManagedTransaction=None):
        result = tx.run("MATCH (a) -[r]-> () DELETE a, r")
        result = tx.run("MATCH (a) DELETE a")
        return result.single()
    
    @staticmethod
    def _tx_assert_relation_exists(relation: Relation, tx: ManagedTransaction) -> bool:
        e1_label, e2_label, rel_label = KnowledgeBase._return_optional_labels(relation)
        results = tx.run(f"RETURN exists(({e1_label} {{name: $ent1}})-[{rel_label} {{name: $relation, not: $not_}}]->({e2_label} {{name: $ent2}})) AS relation_exists", ent1=relation.ent1, relation=relation.name, not_=relation.not_, ent2=relation.ent2)
        return results.single().value("relation_exists")

    @staticmethod
    def _return_optional_labels(relation: Relation) -> Tuple[str, str, str]:
        e1_label = f':{relation.ent1_type.value}' if relation.ent1_type is not None else ''
        e2_label = f':{relation.ent2_type.value}' if relation.ent2_type is not None else ''
        rel_label = f':{relation.type_.value}' if relation.type_ is not None else ''
        return e1_label, e2_label, rel_label

    # # # # nice >:]




if __name__ == "__main__":
    kb = KnowledgeBase("bolt://localhost:7687", "neo4j", "Sussy_baka123321") # Security just sent a hug :)
    kb.delete_all() # Clear all data, to have a clean testing sandbox
    
    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "cringe", EntityType.TYPE, "is", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "person", EntityType.TYPE, "is" , RelType.INHERITS))
    kb.add_knowledge("Lucius", Relation("Lucius", EntityType.INSTANCE, "person", EntityType.TYPE, "is" , RelType.INHERITS))
    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "working", EntityType.TYPE, "is", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Lucius", EntityType.INSTANCE, "bad declarator", EntityType.TYPE, "is", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Lucius", EntityType.INSTANCE, "mushrooms", EntityType.TYPE, "likes", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Lucius", EntityType.INSTANCE, "shotos", EntityType.TYPE, "likes", RelType.OTHER))
    kb.add_knowledge("Martinho", Relation("person", EntityType.TYPE, "mammal", EntityType.TYPE, "is", RelType.INHERITS))
    kb.add_knowledge("Lucius", Relation("mammal", EntityType.TYPE, "animal", EntityType.TYPE, "is", RelType.INHERITS))
    kb.add_knowledge("Martinho", Relation("Diogo", EntityType.INSTANCE, "cringe", EntityType.TYPE, "is", RelType.OTHER, not_=True))
    
    kb.add_knowledge("Diogo", Relation("person", EntityType.TYPE, "food", EntityType.TYPE, "eats", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("person", EntityType.TYPE, "beans", EntityType.TYPE, "eats", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Diogo", EntityType.INSTANCE, "chips", EntityType.TYPE, "eats", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("mammal", EntityType.TYPE, "banana", EntityType.TYPE, "eats", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("animal", EntityType.TYPE, "water", EntityType.TYPE, "drinks", RelType.OTHER))

    kb.close()
