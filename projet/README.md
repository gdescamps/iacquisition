# Chanel - IAcquisition - [Démonstrateur]

## Description

Le code source du démonstrateur.

### Installation

**Code testé sur Ubuntu, python==3.10.12**

1) Installer les requirements.

```shell
pip install -r requirements.txt
```

2) En cas d'erreur avec ChromaDB.

```shell
pip install pysqlite3-binary
```

Ajouter ces 3 lignes dans virtualenv/lib/python3.10/site-packages/chromadb/init.py au début:
```shell
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
```
