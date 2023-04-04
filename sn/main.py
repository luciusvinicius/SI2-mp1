from neo4j import GraphDatabase
from enum import Enum
from typing import Type, Any, List, Tuple, TypeVar, Callable

T = TypeVar('T')

class RelType(Enum):
    INSTANCE = "Instance"
    SUBTYPE = "Subtype"
    OTHER = "Other"

class HelloWorldExample:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()
    
    def query_read(self, func:Callable[[Any], T], *args, **kwargs) -> T:
        """Call with a static query function and its arguments following it, performing a read operation.
        
        Examples:
        ---------
        ```
        >>> query_read(query_declarations, "Lucius")
        [("Diogo", "is", "Cringe")]
        >>> query_read(query_inheritance_relation, "Diogo", RelType.OTHER, "is")
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
    def add_knowledge(tx, declarator:str, ent1:str, ent2:str, relation_type:str, relation:str):
        """`declarator` states that `ent1` has a `relation` with `ent2`.
        `relation_type` is one of 3 types:
            - INSTANCE: (Diogo is a Person).
            - SUBTYPE: (Person is a Mammal).
            - OTHER: Literally any other relation.
            
        Use `RelType` enum to specify which one.
        
        `relation` is the name given to the relation, and is only relevant with the OTHER relation type.
        """
        
        result = tx.run(f"MERGE (e1:{ent1} {{name: $ent1}})" +
                        f"MERGE (e2:{ent2} {{name: $ent2}})" +
                        f"MERGE (e1)-[r:{relation_type} {{declarator: $declarator, name: $relation}}]->(e2)" +
                        "RETURN e1.name", declarator=declarator, ent1=ent1, ent2=ent2, relation_type=relation_type, relation=relation)
        
        return result.single()[0]
    

    @staticmethod
    def query_declarations(tx, declarator:str) -> List[Tuple[str, str, str]]:
        """Query an declarator to obtain all declarations made by it.
        Output: `[(entity1, relation_name, entity2), (...)]`
        """
        pass

    @staticmethod
    def query_local(tx, ent:str) -> List[Tuple[str, List[str]]]:
        """Query an entity to obtain the relations and its entities.
        Output: `[(relation_name, [entity1, entity2]), (...)]`
        """
        pass

    @staticmethod
    def query_local_relation(tx, ent:str, relation_type:RelType, relation:str) -> List[str]:
        """Query an entity to obtain the entities of a specific relation."""
        pass
        # return self._query(, )

    @staticmethod
    def query_inheritance(tx, ent:str) -> List[Tuple[str, List[str]]]:
        """Query all local attributes of an entity as well as attributes inherited from INSTANCE and SUBTYPE relations"""
        pass

    @staticmethod
    def query_inheritance_relation(tx, ent:str, relation_type:RelType, relation:str) -> List[str]:
        """Query the specified attribute of an entity as well as attributes inherited from INSTANCE and SUBTYPE relations"""
        pass
    
    @staticmethod
    def query_descendants(tx, ent:str) -> List[str]:
        """Query all attributes of entity descendants"""
        # this sounds like a bad idea maybe
        pass

    @staticmethod
    def query_descendants_relation(tx, ent:str, relation_type:RelType, relation:str) -> List[Tuple[str, List[str]]]:
        """Query the specified attribute of entity descendants"""
        pass


    
    @staticmethod
    def _create_and_return_greeting(tx, message):
        result = tx.run("CREATE (a:Greeting) "
                        "SET a.message = $message "
                        "RETURN a.message + ', from node ' + id(a)", message=message)
        return result.single()[0]
    
    # Why are you still reading? We told you to not peek >:(
    
    @staticmethod
    def delete_all(tx):
        result = tx.run("match (a) -[r] -> () delete a, r")
        result = tx.run("match (a) delete a")
        return result.single()
    

    # # nice >:]




if __name__ == "__main__":
    greeter = HelloWorldExample("bolt://localhost:7687", "neo4j", "Sussy_baka123321") # Security just sent a hug :)
    greeter.query_write(greeter.delete_all) # Don't have memory between run tests
    
    greeter.query_write(greeter.add_knowledge, "Lucius", "Diogo", "Cringe", RelType.OTHER, "is")
    greeter.query_write(greeter.add_knowledge, "Lucius", "Diogo", "Person", RelType.INSTANCE, "is")
    
    greeter.query_read(greeter.query_declarations, "Lucius")
    
    greeter.close()