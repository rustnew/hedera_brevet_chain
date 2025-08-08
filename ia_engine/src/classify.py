# src/classify.py

CPC_DATABASE = {
    "chaise": "A47C 4/02",
    "tasse": "A47G 19/22",
    "sac": "A45F 3/00",
    "panneau solaire": "H02S 40/00",
    "batterie": "H01M 10/00",
}

def classify_cpc(idea: str) -> str:
    idea_lower = idea.lower()
    for keyword, code in CPC_DATABASE.items():
        if keyword in idea_lower:
            return code
    return "A01B 1/00"  # Code par défaut