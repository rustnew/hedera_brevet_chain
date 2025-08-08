# src/antecedent_search.py

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Charger le modèle
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Charger la base de données vectorielle
index = faiss.read_index("models/uspto_embeddings.faiss")

EXISTING_PATENTS = [
    "chaise pliante en aluminium",
    "tasse isotherme à double paroi",
    "sac à dos avec panneau solaire",
]

def check_novelty(idea: str) -> int:
    idea_embedding = model.encode([idea])
    distances, indices = index.search(idea_embedding, k=5)
    
    if distances[0][0] < 0.3:
        return random.randint(20, 40)  # Similaire
    return random.randint(70, 95)     # Nouveau