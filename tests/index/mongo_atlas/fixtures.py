import os

import numpy as np
import pytest
from pydantic import Field

from docarray import BaseDoc
from docarray.index import MongoAtlasDocumentIndex
from docarray.typing import NdArray

N_DIM = 10


def mongo_env_var(var: str):
    try:
        env_var = os.environ[var]
    except KeyError as e:
        msg = f"""Please add `export {var}=\"your_{var.lower()}\"` in the terminal"""
        raise KeyError(msg) from e
    return env_var


@pytest.fixture
def mongo_fixture_env():
    uri = mongo_env_var("MONGODB_URI")
    database = mongo_env_var("DATABASE_NAME")
    collection_name = mongo_env_var("COLLECTION_NAME")
    return uri, database, collection_name


@pytest.fixture
def simple_schema():
    class SimpleSchema(BaseDoc):
        text: str
        number: int
        embedding: NdArray[10] = Field(dim=10, index_name="vector_index")

    return SimpleSchema


@pytest.fixture
def simple_index(mongo_fixture_env, simple_schema):
    uri, database, collection_name = mongo_fixture_env
    index = MongoAtlasDocumentIndex[simple_schema](
        mongo_connection_uri=uri,
        database_name=database,
        collection_name=collection_name,
    )
    return index


@pytest.fixture
def db_collection(simple_index):
    return simple_index._doc_collection


@pytest.fixture
def clean_database(db_collection):
    db_collection.delete_many({})
    yield
    db_collection.delete_many({})


@pytest.fixture
def random_simple_documents(simple_schema):
    docs_text = [
        "Text processing with Python is a valuable skill for data analysis.",
        "Gardening tips for a beautiful backyard oasis.",
        "Explore the wonders of deep-sea diving in tropical locations.",
        "The history and art of classical music compositions.",
        "An introduction to the world of gourmet cooking.",
    ]
    docs_text += [e[::-1] for e in docs_text]
    return [
        simple_schema(embedding=np.random.rand(N_DIM), number=i, text=docs_text[i])
        for i in range(10)
    ]


@pytest.fixture
def simple_index_with_docs(simple_index, random_simple_documents):
    simple_index.index(random_simple_documents)
    yield simple_index, random_simple_documents
    simple_index._doc_collection.delete_many({})