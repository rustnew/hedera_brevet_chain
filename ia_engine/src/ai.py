# src/ai.py

import random
from typing import Dict
from classify import classify_cpc
from antecedent_search import check_novelty
from translate import translate_to_english

# Base de données simplifiée pour démo
CPC_DATABASE = {
    "chaise": "A47C 4/02",
    "tasse": "A47G 19/22",
    "sac": "A45F 3/00",
    "panneau solaire": "H02S 40/00",
}

def generate_patent_structured(raw_idea: str) -> Dict:
    # Traduire en anglais (si nécessaire)
    idea_en = translate_to_english(raw_idea)

    # Extraire le mot-clé principal
    key_word = next((kw for kw in CPC_DATABASE if kw in raw_idea.lower()), "invention")

    # Générer le titre
    title = f"Amélioration de {key_word}".title()

    # Classer CPC
    cpc_code = classify_cpc(raw_idea)

    # Vérifier la nouveauté
    novelty_score = check_novelty(raw_idea)

    # Générer les revendications
    claims = [
        f"1. Un dispositif comprenant {key_word} avec une structure améliorée.",
        f"2. Selon la revendication 1, ledit dispositif est fabriqué en matériau recyclé.",
        f"3. Dispositif selon l'une des revendications précédentes, adapté pour un usage en extérieur."
    ]

    return {
        "title": title,
        "problem": f"Les dispositifs existants de type {key_word} ne résolvent pas efficacement le problème de durabilité.",
        "solution": f"La présente invention propose un système amélioré de {key_word} avec une structure renforcée.",
        "claims": claims,
        "cpc_code": cpc_code,
        "novelty_score": novelty_score
    }