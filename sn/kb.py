from dataclasses import dataclass
from neo4j import GraphDatabase, ManagedTransaction
from enum import Enum
from typing import List, Tuple, Dict, Union

from sn.confidence import ConfidenceTable


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
    not_:       bool                = False

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

    # TODO: verify if inverse of relation is already in the KnowledgeBase?    
    @sn_write
    @staticmethod
    def add_knowledge(declarator:str, relation: Relation, tx: ManagedTransaction=None):
        """`declarator` states that `relation.ent1` has a `relation.name` with `relation.ent2`.
        `relation.type_` is one of 2 types:
            - INHERITS: (Diogo is a Person).
            - OTHER: Literally any other relation.
            
        Use `RelType` enum to specify which one.
        
        `relation.name` is the name given to the relation, and is only relevant with the OTHER relation type.

        `relation` should not have `None` values for the type fields.
        """
        
        if relation.type_.INHERITS and relation.ent2_type != EntityType.TYPE:
            raise ValueError("Can only inherit from types entities.")

        if relation.ent1_type is None or relation.ent2_type is None or relation.type_ is None:
            raise ValueError("Relation and entity types shold not be None.")

        new_ent1 = f"n_{relation.ent1}" if relation.ent1.isdigit() else relation.ent1 
        new_ent2 = f"n_{relation.ent2}" if relation.ent2.isdigit() else relation.ent2

        result = tx.run(f"MERGE (e1:{relation.ent1_type.value} {{name: $ent1}}) "
                        f"MERGE (e2:{relation.ent2_type.value} {{name: $ent2}}) "
                        f"MERGE (e1)-[r:{relation.type_.value} {{declarator: $declarator, name: $relation, not: $not_}}]->(e2) "
                        "RETURN e1.name", declarator=declarator, ent1=new_ent1, ent2=new_ent2, relation=relation.name, not_=relation.not_)
        
        return result.single()[0]
    
    @sn_read
    @staticmethod
    def query_declarations(declarator:str, tx: ManagedTransaction=None) -> List[Relation]:
        """Query a declarator to obtain all declarations made by it.
        Output: `[relation1, relation2, (...)]`
        """
        results = tx.run("MATCH (e1)-[r {declarator: $declarator}]->(e2) "
                        "RETURN e1.name AS ent1, labels(e1)[0] AS ent1_type, type(r) AS relation_type, r.name AS relation, e2.name AS ent2, labels(e2)[0] AS ent2_type, r.not AS not", declarator=declarator)
        
        return [Relation(
            ent1=result.value("ent1"),
            ent1_type=EntityType(result.value("ent1_type")),
            ent2=result.value("ent2"),
            ent2_type=EntityType(result.value("ent2_type")),
            name=result.value("relation"),
            type_=result.value("relation_type"),
            not_=result.value("not")
        ) for result in results]

    @sn_read
    @staticmethod
    def query_declarators(relation: Relation, tx: ManagedTransaction=None) -> List[str]:
        """Obtain all declarators that declared the given relation."""
        results = tx.run(f"MATCH (e1:{relation.ent1_type} {{name: $ent1}})-[r:{relation.type_.value} {{name: $relation, not: $not_}}]->(e2{relation.ent2_type} {{name: $ent2}}) "
                        "RETURN r.declarator AS declarator", ent1=relation.ent1, relation=relation.name, ent2=relation.ent2, not_=relation.not_)
        
        return [result.value("declarator") for result in results]

    @sn_read
    @staticmethod
    def query_local(ent:str, tx: ManagedTransaction=None) -> List[Tuple[Tuple[str, str], List[str]]]:
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

            result_dict.setdefault((relation, relation_type), [])
            result_dict[relation, relation_type].append(other_entity)

        return list(result_dict.items())

    @sn_read
    @staticmethod
    def query_local_relation(ent:str, relation:str, relation_type:RelType, tx: ManagedTransaction=None) -> List[str]:
        """Query an entity to obtain the entities of a specific relation."""
        
        results = tx.run(f"MATCH (e {{name: $ent}})-[r:{relation_type.value} {{name: $relation}}]->(e2) "
                        "RETURN e2.name AS entity", ent=ent, relation=relation)
        
        return [result.value("entity") for result in results]
        
    @sn_read
    @staticmethod
    def query_inheritance(ent:str, tx: ManagedTransaction=None) -> Dict[str, Tuple[List[str], int]]:
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
        
        return {result.value('subject'):(result.value('characteristics'), result.value('distance')) for result in results}

    @sn_read
    @staticmethod
    def query_inheritance_relation(ent:str, relation:str, tx: ManagedTransaction=None) ->  Dict[str, Tuple[List[str], int]]:
        """Query the specified attribute of an entity as well as attributes inherited from INSTANCE and SUBTYPE relations.
        The output is each Entity in the key, the characteristics and distance as the tuple elements"""
        
        results = tx.run(
            f"MATCH (ent1 {{name:$ent}}) "
            "MATCH (ent1)-[r {name:$relation}]->(ent2) "
            "RETURN ent1.name AS subject, collect(ent2.name) AS characteristics, 0 AS distance "
            "UNION "
            f"MATCH p = (ent1 {{name:$ent}})-[:{RelType.INHERITS.value} *1..]->(ascn) "
            "MATCH (ascn)-[r {name:$relation}]->(ent2) "
            "RETURN ascn.name AS subject, collect(ent2.name) AS characteristics, length(p) AS distance", ent=ent, relation=relation
        )
        
        return {result.value('subject'):(result.value('characteristics'), result.value('distance')) for result in results}
        
    @sn_read
    @staticmethod
    def query_descendants(ent:str, tx: ManagedTransaction=None) -> List[Tuple[str, str, List[str]]]:
        """Query all attributes of entity descendants"""
        # this sounds like a bad idea maybe
        raise NotImplementedError()

    @sn_read
    @staticmethod
    def query_descendants_relation(ent:str, relation:str, relation_type:RelType, tx: ManagedTransaction=None) -> List[str]:
        """Query the specified *local* attribute of entity descendants"""
        
        results = tx.run(f"MATCH (eOut)<-[:{relation_type.value} {{name: $relation}}]-(desc)-[r:{RelType.INHERITS.value} *1..]->(eIn {{name: $entIn}}) "
                        "RETURN eOut.name AS other_entity", relation=relation, entIn=ent)

        return [result.value("other_entity") for result in results]

    @sn_read
    @staticmethod
    def assert_relation(relation: Relation, tx: ManagedTransaction=None) -> bool:
        """Assert whether or not `relation` exists in the knowledge base"""

        results = tx.run(f"RETURN exists((e1:{relation.ent1_type.value} {{name: $ent1}})-[r:{relation.type_.value} {{name: $relation, not: $not_}}]->(e2:{relation.ent2_type.value} {{name: $ent2}})) AS relation_exists")

        return results.single().value("relation_exists")

    @sn_read
    @staticmethod
    def assert_relation_inheritance(relation: Relation, tx: ManagedTransaction=None) -> bool:
        """Assert whether or not `relation` exists in the knowledge base, with inheritance"""

        results = tx.run(
            f"MATCH p = (e1 {{name: $ent1}})-[r {{name: $relation, not: $not_}}]->(e2 {{name: $ent2}}) "
            "RETURN exists(p) AS relation_exists "
            "UNION "
            f"MATCH p = (e1 {{name: $ent1}})-[:{RelType.INHERITS.value} *1..]->(ascn) "
            f"MATCH (ascn)-[r {{name:$relation}}]->(e2 {{name: $ent2}}) "
            "RETURN exists(p) AS relation_exists", ent1=relation.ent1, ent2=relation.ent2, relation=relation.name
        )

        return any(result.value("relation_exists") for result in results)

    @sn_read
    @staticmethod
    def get_all_declarators(tx: ManagedTransaction=None) -> List[str]:
        """Get all unique declarators of knowledge."""

        results = tx.run(f"MATCH ()-[r]->() RETURN DISTINCT r.declarator AS declarator")

        return [result.value("declarator") for result in results]

    @sn_write
    @staticmethod
    def delete_all(tx: ManagedTransaction=None):
        result = tx.run("match (a) -[r] -> () delete a, r")
        result = tx.run("match (a) delete a")
        return result.single()
    

    # # # nice >:]




if __name__ == "__main__":
    kb = KnowledgeBase("bolt://localhost:7687", "neo4j", "Sussy_baka123321") # Security just sent a hug :)
    kb.delete_all() # Don't have memory between run tests
    
    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "cringe", EntityType.TYPE, "is", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "person", EntityType.TYPE, "is" , RelType.INHERITS))
    kb.add_knowledge("Lucius", Relation("Diogo", EntityType.INSTANCE, "working", EntityType.TYPE, "is", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Lucius", EntityType.INSTANCE, "bad declarator", EntityType.TYPE, "is", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Lucius", EntityType.INSTANCE, "mushrooms", EntityType.TYPE, "likes", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Lucius", EntityType.INSTANCE, "shotos", EntityType.TYPE, "likes", RelType.OTHER))
    kb.add_knowledge("Martinho", Relation("Person", EntityType.TYPE, "mammal", EntityType.TYPE, "is", RelType.INHERITS))
    kb.add_knowledge("Lucius", Relation("Mammal", EntityType.TYPE, "animal", EntityType.TYPE, "is", RelType.INHERITS))
    kb.add_knowledge("Martinho", Relation("Diogo", EntityType.INSTANCE, "cringe", EntityType.TYPE, "is", RelType.OTHER, not_=True))
    

    kb.add_knowledge("Diogo", Relation("Person", EntityType.TYPE, "food", EntityType.TYPE, "eats", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Person", EntityType.TYPE, "beans", EntityType.TYPE, "eats", RelType.OTHER))
    kb.add_knowledge("Diogo", Relation("Diogo", EntityType.INSTANCE, "chips", EntityType.TYPE, "eats", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("Mammal", EntityType.TYPE, "banana", EntityType.TYPE, "eats", RelType.OTHER))
    kb.add_knowledge("Lucius", Relation("Animal", EntityType.TYPE, "water", EntityType.TYPE, "drinks", RelType.OTHER))

    
    
    # ------------- DEBUG ZONE ------------
    print(kb.query_declarations("Lucius"))
    print(kb.query_local("Diogo"))   # [(('is', 'Other'), ['Cringe', 'Working']), (('is', 'Instance'), ['Person']), (('eats', 'Other'), ['Chips'])]
    print(kb.query_local_relation("Diogo", "is", RelType.OTHER))   # ['Working', 'Cringe']
    print(kb.query_inheritance("Diogo"))
    print(kb.query_descendants_relation("Mammal", "eats", RelType.OTHER))   # ['Beans', 'Food', 'Chips']
    
    confidence_table = ConfidenceTable(kb)
    confidence_table.register_declarator("Lucius")
    confidence_table.register_declarator("Diogo")
    confidence_table.register_declarator("Martinho")
    confidence_table.update_confidences()
    print('Confidence of (Diogo)-[is]->(Cringe):', confidence_table.get_relation_confidence(Relation("Diogo", "Cringe", "is", RelType.OTHER)))   # 0.4947916666666667
    print('Confidence table:', confidence_table._confidences)

    kb.close()
    
    # [<Record e1.name + ' ' + r.name + ' ' + e2.name='Diogo is Cringe'>, <Record e1.name + ' ' + r.name + ' ' + e2.name='Diogo is Person'>, <Record e1.name + ' ' + r.name + ' ' + e2.name='Diogo is Working'>]
    # [(('is', 'Other'), ['Cringe', 'Working']), (('is', 'Instance'), ['Person'])]
    # ['Working', 'Cringe']
    
    

    # neo4j.exceptions.CypherSyntaxError: {code: Neo.ClientError.Statement.SyntaxError} {message: All sub queries in an UNION must have the same return column names (line 1, column 105 (offset: 104))
    # "MATCH (ent1 {name:$ent})-[:Instance|Subtype *1..]->(ascn) MATCH (ent1)-[r]->(ent2) RETURN ent1, r, ent2 UNION MATCH (ascn)-[r]->(ent2) RETURN ascn, r, ent2" 
    
    # [<Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:4' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:2' labels=frozenset({'Cringe'}) properties={'name': 'Cringe'}>) type='Other' properties={'name': 'is', 'declarator': 'Lucius'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:2' labels=frozenset({'Cringe'}) properties={'name': 'Cringe'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:5' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:3' labels=frozenset({'Person'}) properties={'name': 'Person'}>) type='Instance' properties={'name': 'is', 'declarator': 'Lucius'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:3' labels=frozenset({'Person'}) properties={'name': 'Person'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:6' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:9' labels=frozenset({'Working'}) properties={'name': 'Working'}>) type='Other' properties={'name': 'is', 'declarator': 'Lucius'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:9' labels=frozenset({'Working'}) properties={'name': 'Working'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:15' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:19' labels=frozenset({'Chips'}) properties={'name': 'Chips'}>) type='Other' properties={'name': 'eats', 'declarator': 'Diogo'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:19' labels=frozenset({'Chips'}) properties={'name': 'Chips'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:10' labels=frozenset({'Lucius'}) properties={'name': 'Lucius'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:7' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:10' labels=frozenset({'Lucius'}) properties={'name': 'Lucius'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:11' labels=frozenset({'BadDeclarator'}) properties={'name': 'Bad Declarator'}>) type='Other' properties={'name': 'is', 'declarator': 'Diogo'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:11' labels=frozenset({'BadDeclarator'}) properties={'name': 'Bad Declarator'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:10' labels=frozenset({'Lucius'}) properties={'name': 'Lucius'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:11' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:10' labels=frozenset({'Lucius'}) properties={'name': 'Lucius'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:15' labels=frozenset({'Mushrooms'}) properties={'name': 'Mushrooms'}>) type='Other' properties={'name': 'likes', 'declarator': 'Diogo'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:15' labels=frozenset({'Mushrooms'}) properties={'name': 'Mushrooms'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:10' labels=frozenset({'Lucius'}) properties={'name': 'Lucius'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:12' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:10' labels=frozenset({'Lucius'}) properties={'name': 'Lucius'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:16' labels=frozenset({'Shotos'}) properties={'name': 'Shotos'}>) type='Other' properties={'name': 'likes', 'declarator': 'Diogo'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:16' labels=frozenset({'Shotos'}) properties={'name': 'Shotos'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:3' labels=frozenset({'Person'}) properties={'name': 'Person'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:13' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:3' labels=frozenset({'Person'}) properties={'name': 'Person'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:17' labels=frozenset({'Mammal'}) properties={'name': 'Mammal'}>) type='Subtype' properties={'name': 'is', 'declarator': 'Martinho'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:17' labels=frozenset({'Mammal'}) properties={'name': 'Mammal'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:3' labels=frozenset({'Person'}) properties={'name': 'Person'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:14' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:3' labels=frozenset({'Person'}) properties={'name': 'Person'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:18' labels=frozenset({'Food'}) properties={'name': 'Food'}>) type='Other' properties={'name': 'eats', 'declarator': 'Diogo'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:18' labels=frozenset({'Food'}) properties={'name': 'Food'}>>]
    
    