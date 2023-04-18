# SI2-mp1

Python 3.10 is required to run this project.

## Requirements instalation

```
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m textblob.download_corpora
```

## Run neo4j container with docker

```
docker run --env=NEO4J_AUTH=neo4j/Sussy_baka123321 -p 7474:7474 -p 7687:7687 neo4j
```

## Populate semantic network with Wikipedia knowledge

```
python3 wikipedia_declarator.py | python3 -m nlp.main
```