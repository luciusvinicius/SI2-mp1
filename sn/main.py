from neo4j import GraphDatabase, ManagedTransaction
from enum import Enum
from typing import Type, Any, List, Tuple, TypeVar, Callable

T = TypeVar('T')

class RelType(Enum):
    INSTANCE = "Instance"
    SUBTYPE = "Subtype"
    OTHER = "Other"

class Driver:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()
    
    def query_read(self, func:Callable[[Any], T], *args, **kwargs) -> T:
        """Call with a static query function and its arguments following it, performing a read operation.
        
        Examples
        --------
        ```
        >>> query_read(query_declarations, "Lucius")
        [("Diogo", "is", "Cringe")]
        >>> query_read(query_local_relation, "Diogo", RelType.OTHER, "is")
        ["Cringe"]
        ```"""
        
        new_args = self.get_enums(args)
        with self.driver.session() as session:
            return session.execute_read(func, *new_args, **kwargs)
    
    def query_write(self, func:Callable[[Any], T], *args, **kwargs) -> T:
        """Call with a static query function and its arguments following it.
        
        Examples:
        - query_write(delete_all)
        - query_write(add_knowledge, "Lucius", "Diogo", "Cringe", RelType.OTHER, "is")
        - query_write(add_knowledge, "Diogo", "Lucius", "Bad Declarator", RelType.OTHER, "is")
        """
        
        new_args = self.get_enums(args)
        with self.driver.session() as session:
            return session.execute_write(func, *new_args, **kwargs)
    
    def get_enums(self, args: Tuple[str|RelType]) -> Tuple[str]:
        """Given a list of args, convert all `RelType` enums to their corresponding string value."""
        new_args = list(args)
        for i,a in enumerate(new_args):
            if isinstance(a, RelType):
                new_args[i] = a.value
        
        return tuple(new_args)

    # ------------------------ Query Methods --------------------------
    # Don't use these directly, pass the function name to the `query` and `query_write` methods
    # E.gs.: 
    # greeter.query_write(greeter.delete_all)
    # greeter.query_write(greeter.add_knowledge, "Lucius", "Diogo", "Cringe", RelType.OTHER.value, "is")
        
    @staticmethod
    def add_knowledge(tx, declarator:str, ent1:str, ent2:str, relation:str, relation_type:str):
        """`declarator` states that `ent1` has a `relation` with `ent2`.
        `relation_type` is one of 3 types:
            - INSTANCE: (Diogo is a Person).
            - SUBTYPE: (Person is a Mammal).
            - OTHER: Literally any other relation.
            
        Use `RelType` enum to specify which one.
        
        `relation` is the name given to the relation, and is only relevant with the OTHER relation type.
        """

        result = tx.run(f"MERGE (e1:{ent1.replace(' ', '')} {{name: $ent1}}) "
                        f"MERGE (e2:{ent2.replace(' ', '')} {{name: $ent2}}) "
                        f"MERGE (e1)-[r:{relation_type} {{declarator: $declarator, name: $relation}}]->(e2) "
                        "RETURN e1.name", declarator=declarator, ent1=ent1, ent2=ent2, relation_type=relation_type, relation=relation)
        
        return result.single()[0]
    

    @staticmethod
    def query_declarations(tx: ManagedTransaction, declarator:str) -> List[Tuple[str, str, str]]:
        """Query an declarator to obtain all declarations made by it.
        Output: `[(entity1, relation_name, entity2), (...)]`
        """
        result = tx.run("MATCH (e1)-[r {declarator: $declarator}]->(e2) "
                        "RETURN e1.name + ' ' + r.name + ' ' + e2.name", declarator=declarator)
        return list(result)

    @staticmethod
    def query_local(tx: ManagedTransaction, ent:str) -> List[Tuple[str, str, List[str]]]:
        """Query an entity to obtain the relations and its entities.
        Output: `[(relation_name, [entity1, entity2]), (...)]`
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

    @staticmethod
    def query_local_relation(tx: ManagedTransaction, ent:str, relation:str, relation_type:str) -> List[str]:
        """Query an entity to obtain the entities of a specific relation."""
        
        results = tx.run(f"MATCH (e {{name: $ent}})-[r:{relation_type} {{name: $relation}}]->(e2) "
                        "RETURN e2.name as entity", ent=ent, relation=relation)
        
        return [result.value("entity") for result in results]
        
    @staticmethod
    def query_inheritance(tx: ManagedTransaction, ent:str) -> List[Tuple[str, List[str]]]:
        """Query all local attributes of an entity as well as attributes inherited from INSTANCE and SUBTYPE relations"""
        
        # logicks: query_local for ent + query_inheritance for ascendants
        
        # first: query_local on ent

        # second: get ascendants (INSTANCE/SUBTYPE rels)

        # third: query_inheritance on each ascendant and append result
        
        results = tx.run(
            f"MATCH (ent1 {{name:$ent}}) "
            "MATCH (ent1)-[r]->(ent2) "
            "RETURN ent1 as ent, collect(r), collect(ent2)"
            "UNION "
            f"MATCH (ent1 {{name:$ent}})-[:{RelType.INSTANCE.value}|{RelType.SUBTYPE.value} *1..]->(ascn) "
            "MATCH (ascn)-[r]->(ent2) "
            "RETURN ascn as ent, collect(r), collect(ent2)", ent=ent
        )
        
        # TODO: process results into final return val


        return list(results)

    @staticmethod
    def query_inheritance_relation(tx: ManagedTransaction, ent:str, relation:str, relation_type:str) -> List[str]:
        """Query the specified attribute of an entity as well as attributes inherited from INSTANCE and SUBTYPE relations"""
        # Unary values would be used in a shortest path context. ig
        pass
    
    @staticmethod
    def query_descendants(tx: ManagedTransaction, ent:str) -> List[Tuple[str, str, List[str]]]:
        """Query all attributes of entity descendants"""
        # this sounds like a bad idea maybe
        raise NotImplementedError()

    @staticmethod
    def query_descendants_relation(tx: ManagedTransaction, ent:str, relation:str, relation_type:str) -> List[str]:
        """Query the specified *local* attribute of entity descendants"""
        
        results = tx.run(f"MATCH (eOut)<-[:{relation_type} {{name: $relation}}]-(desc)-[r:{RelType.INSTANCE.value}|{RelType.SUBTYPE.value} *1..]->(eIn {{name: $entIn}}) "
                        "RETURN eOut.name AS other_entity", relation=relation, entIn=ent)

        return [result.value("other_entity") for result in results]

    @staticmethod
    def _create_and_return_greeting(tx: ManagedTransaction, message):
        result = tx.run("CREATE (a:Greeting) "
                        "SET a.message = $message "
                        "RETURN a.message + ', from node ' + id(a)", message=message)
        return result.single()[0]
    
    @staticmethod
    def delete_all(tx: ManagedTransaction):
        result = tx.run("match (a) -[r] -> () delete a, r")
        result = tx.run("match (a) delete a")
        return result.single()
    

    # # nice >:]




if __name__ == "__main__":
    driver = Driver("bolt://localhost:7687", "neo4j", "Sussy_baka123321") # Security just sent a hug :)
    driver.query_write(driver.delete_all) # Don't have memory between run tests
    
    driver.query_write(driver.add_knowledge, "Lucius", "Diogo", "Cringe", "is", RelType.OTHER)
    driver.query_write(driver.add_knowledge, "Lucius", "Diogo", "Person", "is" , RelType.INSTANCE)
    driver.query_write(driver.add_knowledge, "Lucius", "Diogo", "Working", "is", RelType.OTHER)
    driver.query_write(driver.add_knowledge, "Diogo", "Lucius", "Bad Declarator", "is", RelType.OTHER)
    driver.query_write(driver.add_knowledge, "Diogo", "Lucius", "Mushrooms", "likes", RelType.OTHER)
    driver.query_write(driver.add_knowledge, "Diogo", "Lucius", "Shotos", "likes", RelType.OTHER)
    driver.query_write(driver.add_knowledge, "Martinho", "Person", "Mammal", "is", RelType.SUBTYPE)
    driver.query_write(driver.add_knowledge, "Lucius", "Mammal", "Animal", "is", RelType.SUBTYPE)
    

    driver.query_write(driver.add_knowledge, "Diogo", "Person", "Food", "eats", RelType.OTHER)
    driver.query_write(driver.add_knowledge, "Diogo", "Person", "Beans", "eats", RelType.OTHER)
    driver.query_write(driver.add_knowledge, "Diogo", "Diogo", "Chips", "eats", RelType.OTHER)
    driver.query_write(driver.add_knowledge, "Lucius", "Mammal", "Banana", "eats", RelType.OTHER)
    driver.query_write(driver.add_knowledge, "Lucius", "Animal", "Water", "drinks", RelType.OTHER)

    
    
    # ------------- DEBUG ZONE ------------
    # print(driver.query_read(driver.query_declarations, "Lucius"))
    # print(driver.query_read(driver.query_local, "Diogo"))
    # print(driver.query_read(driver.query_local_relation, "Diogo", "is", RelType.OTHER))
    print(driver.query_read(driver.query_inheritance, "Diogo"))
    # print(driver.query_read(driver.query_descendants_relation, "Mammal", "eats", RelType.OTHER))   # ['Food', 'Chips']
    
    driver.close()
    
    # [<Record e1.name + ' ' + r.name + ' ' + e2.name='Diogo is Cringe'>, <Record e1.name + ' ' + r.name + ' ' + e2.name='Diogo is Person'>, <Record e1.name + ' ' + r.name + ' ' + e2.name='Diogo is Working'>]
    # [(('is', 'Other'), ['Cringe', 'Working']), (('is', 'Instance'), ['Person'])]
    # ['Working', 'Cringe']
    
    

    # neo4j.exceptions.CypherSyntaxError: {code: Neo.ClientError.Statement.SyntaxError} {message: All sub queries in an UNION must have the same return column names (line 1, column 105 (offset: 104))
    # "MATCH (ent1 {name:$ent})-[:Instance|Subtype *1..]->(ascn) MATCH (ent1)-[r]->(ent2) RETURN ent1, r, ent2 UNION MATCH (ascn)-[r]->(ent2) RETURN ascn, r, ent2" 
    
    # [<Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:4' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:2' labels=frozenset({'Cringe'}) properties={'name': 'Cringe'}>) type='Other' properties={'name': 'is', 'declarator': 'Lucius'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:2' labels=frozenset({'Cringe'}) properties={'name': 'Cringe'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:5' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:3' labels=frozenset({'Person'}) properties={'name': 'Person'}>) type='Instance' properties={'name': 'is', 'declarator': 'Lucius'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:3' labels=frozenset({'Person'}) properties={'name': 'Person'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:6' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:9' labels=frozenset({'Working'}) properties={'name': 'Working'}>) type='Other' properties={'name': 'is', 'declarator': 'Lucius'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:9' labels=frozenset({'Working'}) properties={'name': 'Working'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:15' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:0' labels=frozenset({'Diogo'}) properties={'name': 'Diogo'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:19' labels=frozenset({'Chips'}) properties={'name': 'Chips'}>) type='Other' properties={'name': 'eats', 'declarator': 'Diogo'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:19' labels=frozenset({'Chips'}) properties={'name': 'Chips'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:10' labels=frozenset({'Lucius'}) properties={'name': 'Lucius'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:7' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:10' labels=frozenset({'Lucius'}) properties={'name': 'Lucius'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:11' labels=frozenset({'BadDeclarator'}) properties={'name': 'Bad Declarator'}>) type='Other' properties={'name': 'is', 'declarator': 'Diogo'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:11' labels=frozenset({'BadDeclarator'}) properties={'name': 'Bad Declarator'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:10' labels=frozenset({'Lucius'}) properties={'name': 'Lucius'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:11' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:10' labels=frozenset({'Lucius'}) properties={'name': 'Lucius'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:15' labels=frozenset({'Mushrooms'}) properties={'name': 'Mushrooms'}>) type='Other' properties={'name': 'likes', 'declarator': 'Diogo'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:15' labels=frozenset({'Mushrooms'}) properties={'name': 'Mushrooms'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:10' labels=frozenset({'Lucius'}) properties={'name': 'Lucius'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:12' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:10' labels=frozenset({'Lucius'}) properties={'name': 'Lucius'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:16' labels=frozenset({'Shotos'}) properties={'name': 'Shotos'}>) type='Other' properties={'name': 'likes', 'declarator': 'Diogo'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:16' labels=frozenset({'Shotos'}) properties={'name': 'Shotos'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:3' labels=frozenset({'Person'}) properties={'name': 'Person'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:13' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:3' labels=frozenset({'Person'}) properties={'name': 'Person'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:17' labels=frozenset({'Mammal'}) properties={'name': 'Mammal'}>) type='Subtype' properties={'name': 'is', 'declarator': 'Martinho'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:17' labels=frozenset({'Mammal'}) properties={'name': 'Mammal'}>>, <Record ent=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:3' labels=frozenset({'Person'}) properties={'name': 'Person'}> r=<Relationship element_id='5:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:14' nodes=(<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:3' labels=frozenset({'Person'}) properties={'name': 'Person'}>, <Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:18' labels=frozenset({'Food'}) properties={'name': 'Food'}>) type='Other' properties={'name': 'eats', 'declarator': 'Diogo'}> ent2=<Node element_id='4:fa1d321e-d5e1-47f7-a1b4-bd75aa5605e3:18' labels=frozenset({'Food'}) properties={'name': 'Food'}>>]
    
    