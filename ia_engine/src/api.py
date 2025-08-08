# src/api.py

from fastapi import FastAPI
from pydantic import BaseModel
from ai import generate_patent_structured

app = FastAPI(title="IA pour Brevets", description="Transforme une idée en brevet structuré")

class IdeaRequest(BaseModel):
    raw_idea: str

class PatentResponse(BaseModel):
    title: str
    problem: str
    solution: str
    claims: list[str]
    cpc_code: str
    novelty_score: int

@app.post("/ai/structure", response_model=PatentResponse)
async def structure_idea(request: IdeaRequest):
    result = generate_patent_structured(request.raw_idea)
    return result