from LLM.embedding import *
import pandas as pd
from enum import Enum


class Collection(str, Enum):
    Responsibilities: str = "Responsibilities"
    Diplomas: str = "Diplomas"
    Skills: str = "Skills"


def query_collection(queries, collection_name, n_results=50):
    embedding_function = get_embedding_function()
    collection = get_collection(
        collection_name=collection_name,
        client_db_path="storage/vectors",
        embedding_function=embedding_function,
    )

    if queries:
        results = collection.query(
            query_texts=queries,
            n_results=n_results,
        )
        final_df = pd.DataFrame()
        for i in range(len(results["distances"])):
            frame = {
                "Distances": pd.Series(results["distances"][i]),
                "Requêtes": pd.Series([queries[i]] * n_results),
                "Documents": pd.Series(results["documents"][i]),
                "Metadatas": pd.Series(
                    [_["Filename"] for _ in results["metadatas"][i]]
                ),
            }
            result = pd.DataFrame(frame)

            if final_df.shape[0] == 0:
                final_df = result
            else:
                final_df = pd.concat([final_df, result], axis=0)
        return final_df
    else:
        return None


def process_dataframe_get_top(final_df, n_top):
    return final_df["Metadatas"].value_counts().nlargest(n_top).to_dict()


def explicability(final_df, top_dict):
    res = {}
    for _ in top_dict.keys():
        zoom = final_df[final_df["Metadatas"] == _][["Requêtes", "Documents"]]
        data = zoom.to_dict(orient="records")
        res[_] = data
    return res
