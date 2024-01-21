import umap
import numpy as np
from tqdm import tqdm
from LLM.embedding import *
import pandas as pd
import matplotlib.pyplot as plt

def project_embeddings(embeddings, umap_transform):
    umap_embeddings = np.empty((len(embeddings),2))
    for i, embedding in enumerate(tqdm(embeddings)): 
        umap_embeddings[i] = umap_transform.transform([embedding])
    return umap_embeddings

def show_collection_embeddings(collection_name):
    embedding_function = get_embedding_function()
    collection = get_collection(collection_name=collection_name, client_db_path="storage/vectors", embedding_function=embedding_function)
    embeddings = collection.get(include=['embeddings'])['embeddings']
    umap_transform = umap.UMAP(random_state=0, transform_seed=0).fit(embeddings)
    projected_dataset_embeddings = project_embeddings(embeddings, umap_transform)
    plt.figure()
    plt.scatter(projected_dataset_embeddings[:, 0], projected_dataset_embeddings[:, 1], s=10)
    plt.gca().set_aspect('equal', 'datalim')
    plt.title('Projected Embeddings')
    plt.axis('off')



