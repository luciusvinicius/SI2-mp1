# SI2-mp1

Python 3.10 or newer is required to run this project.

## Structure

- `nlp`: module responsible for the Natural Language Processing, i.e. the chatbot.
- `sn`: module specifying the semantic network, its queries and the confidence system.

## Requirements instalation

```
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m textblob.download_corpora
```

## Run neo4j container with docker

Neo4j is required to run with specific credentials and the default Bolt port.

```
docker run --env=NEO4J_AUTH=neo4j/Sussy_baka123321 -p 7474:7474 -p 7687:7687 neo4j
```

## Run the chatbot

In order to run the chatbot, execute the respective Python module at the root of the project.

```
python3 -m nlp.main
```

## Populate semantic network with Wikipedia knowledge

To populate the semantic network with example knowledge, pipe the output of executing `wikipedia_declarator.py` into the chatbot, as shown below.
Do note that the example below assumes Linux/Unix is being used.

```
python3 wikipedia_declarator.py | python3 -m nlp.main
```