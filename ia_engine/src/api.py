
# src/api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field, validator
from typing import List
import time
import asyncio
from contextlib import asynccontextmanager

from ai import get_patent_generator, PatentGenerator

# Gestionnaire de cycle de vie pour pré-charger le modèle
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: pré-chargement du modèle
    logger.info("Pré-chargement du modèle IA...")
    _ = get_patent_generator()  # Force l'initialisation
    yield
    # Shutdown: nettoyage si nécessaire
    logger.info("Arrêt de l'application")

app = FastAPI(
    title="IA pour Brevets - API Optimisée",
    description="Transforme une idée en brevet structuré avec IA avancée",
    version="2.0.0",
    lifespan=lifespan
)

# Middlewares
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models Pydantic améliorés
class IdeaRequest(BaseModel):
    raw_idea: str = Field(..., min_length=10, max_length=1000, description="Idée à transformer en brevet")
    
    @validator('raw_idea')
    def validate_idea(cls, v):
        if not v.strip():
            raise ValueError("L'idée ne peut pas être vide")
        return v.strip()

class PatentResponse(BaseModel):
    title: str = Field(..., description="Titre technique du brevet")
    problem: str = Field(..., description="Problème technique résolu")
    solution: str = Field(..., description="Description de la solution")
    claims: List[str] = Field(..., description="Liste des revendications")
    cpc_code: str = Field(..., description="Code de classification CPC")
    novelty_score: int = Field(..., ge=0, le=100, description="Score de nouveauté (0-100)")
    generation_time: float = Field(..., description="Temps de génération en secondes")

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str

# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Vérification de l'état de l'API."""
    try:
        generator = get_patent_generator()
        return HealthResponse(
            status="healthy",
            model_loaded=generator._generator is not None,
            device=str(generator._device)
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            device="unknown"
        )

@app.post("/ai/structure", response_model=PatentResponse)
async def structure_idea(request: IdeaRequest):
    """
    Transforme une idée en brevet structuré.
    
    - **raw_idea**: L'idée initiale (10-1000 caractères)
    
    Retourne un brevet structuré avec titre, problème, solution, revendications et score de nouveauté.
    """
    start_time = time.time()
    
    try:
        # Validation supplémentaire
        if len(request.raw_idea.split()) < 3:
            raise HTTPException(
                status_code=400, 
                detail="L'idée doit contenir au moins 3 mots"
            )
        
        # Génération asynchrone pour éviter le blocage
        loop = asyncio.get_event_loop()
        generator = get_patent_generator()
        
        result = await loop.run_in_executor(
            None, 
            generator.generate_patent_structured, 
            request.raw_idea
        )
        
        generation_time = time.time() - start_time
        result['generation_time'] = round(generation_time, 2)
        
        logger.info(f"Brevet généré en {generation_time:.2f}s pour: {request.raw_idea[:50]}...")
        
        return PatentResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors de la génération: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Erreur interne lors de la génération du brevet"
        )

@app.get("/ai/models")
async def list_available_models():
    """Liste les modèles disponibles."""
    return {
        "current_model": get_patent_generator().model_name,
        "available_models": [
            "google/flan-t5-small",
            "google/flan-t5-base", 
            "google/flan-t5-large",
            "google/flan-t5-xl"
        ],
        "recommendation": "flan-t5-large pour le meilleur équilibre performance/qualité"
    }

@app.post("/ai/batch")
async def batch_structure_ideas(ideas: List[str]):
    """Traite plusieurs idées en lot (max 5)."""
    if len(ideas) > 5:
        raise HTTPException(
            status_code=400, 
            detail="Maximum 5 idées par lot"
        )
    
    generator = get_patent_generator()
    results = []
    
    for i, idea in enumerate(ideas):
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                generator.generate_patent_structured, 
                idea
            )
            result['batch_index'] = i
            results.append(result)
        except Exception as e:
            logger.error(f"Erreur pour l'idée {i}: {e}")
            results.append({
                "batch_index": i,
                "error": str(e),
                "original_idea": idea
            })
    
    return {"results": results, "total_processed": len(ideas)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )

