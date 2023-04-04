from neo4j import GraphDatabase
from enum import Enum

class RelType(Enum):
    INSTANCE = "Instance"
    SUBTYPE = "Subtype"
    OTHER = "Other"

class HelloWorldExample:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def print_greeting(self, message):
        with self.driver.session() as session:
            greeting = session.execute_write(self._create_and_return_greeting, message)
            print(greeting)
    
    def delete_all(self):
        with self.driver.session() as session:
            session.execute_write(self._delete_everything)
            
    def add_knowledge(self, declarator, ent1, ent2, relation_type, relation):
        with self.driver.session() as session:
            greeting = session.execute_write(self._add_knowledge, declarator, ent1, ent2, relation_type.value, relation)
            print(greeting)
        
    
    @staticmethod
    def _add_knowledge(tx, declarator:str, ent1:str, ent2:str, relation_type:RelType, relation:str):
        
        
        
        result = tx.run(f"MERGE (e1:{ent1} {{name: $ent1}})" +
                        f"MERGE (e2:{ent2} {{name: $ent2}})" +
                        f"MERGE (e1)-[r:{relation_type} {{declarator: $declarator, name: $relation}}]->(e2)" +
                        "RETURN e1.name", declarator=declarator, ent1=ent1, ent2=ent2, relation_type=relation_type, relation=relation)
        
        # result = tx.run("MERGE (e1:"+ ent1 +" {name: $ent1})-[r:" + relation_type + " {declarator: $declarator, name: $relation}]->(e2:"+ ent2 + " {name: $ent2}) "
        #                 "RETURN e1.name", declarator=declarator, ent1=ent1, ent2=ent2, relation_type=relation_type, relation=relation)
        return result.single()[0]
    
    @staticmethod
    def _create_and_return_greeting(tx, message):
        result = tx.run("CREATE (a:Greeting) "
                        "SET a.message = $message "
                        "RETURN a.message + ', from node ' + id(a)", message=message)
        return result.single()[0]
    
    @staticmethod
    def _delete_everything(tx):
        result = tx.run("match (a) -[r] -> () delete a, r")
        result = tx.run("match (a) delete a")
        return result.single()


if __name__ == "__main__":
    greeter = HelloWorldExample("bolt://localhost:7687", "neo4j", "Sussy_baka123321")
    greeter.delete_all()
    greeter.print_greeting("hello, world")
    greeter.add_knowledge("Lucius", "Diogo", "Cringe", RelType.OTHER, "is")
    greeter.add_knowledge("Lucius", "Diogo", "Person", RelType.INSTANCE, "is")
    
    greeter.close()