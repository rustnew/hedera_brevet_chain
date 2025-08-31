# src/ai.py
import asyncio
import logging
import re
from functools import lru_cache
from typing import Dict, List, Optional
from transformers import pipeline, Pipeline
import torch

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatentGenerator:
    """Générateur de brevets structurés utilisant l'IA."""
    
    def __init__(self, model_name: str = "google/flan-t5-large"):
        self.model_name = model_name
        self._generator: Optional[Pipeline] = None
        self._device = self._get_optimal_device()
    
    def _get_optimal_device(self) -> int:
        """Détermine le meilleur device disponible."""
        if torch.cuda.is_available():
            logger.info("GPU CUDA détecté")
            return 0
        elif torch.backends.mps.is_available():
            logger.info("GPU MPS (Apple Silicon) détecté")
            return "mps"
        else:
            logger.info("Utilisation du CPU")
            return -1
    
    @property
    def generator(self) -> Pipeline:
        """Lazy loading du modèle pour optimiser l'initialisation."""
        if self._generator is None:
            logger.info(f"Chargement du modèle {self.model_name}")
            try:
                self._generator = pipeline(
                    "text2text-generation",
                    model=self.model_name,
                    device=self._device,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    model_kwargs={"cache_dir": "./model_cache"}
                )
                logger.info("Modèle chargé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors du chargement du modèle: {e}")
                raise
        return self._generator
    
    def generate_patent_structured(self, raw_idea: str) -> Dict:
        """
        Transforme une idée brute en brevet structuré.
        
        Args:
            raw_idea: L'idée initiale à transformer
            
        Returns:
            Dict contenant le brevet structuré
        """
        if not raw_idea or not raw_idea.strip():
            raise ValueError("L'idée ne peut pas être vide")
        
        # Nettoyage de l'entrée
        cleaned_idea = self._clean_input(raw_idea)
        
        # Génération du prompt optimisé
        prompt = self._create_optimized_prompt(cleaned_idea)
        
        try:
            # Génération avec paramètres optimisés
            result = self.generator(
                prompt,
                max_length=1200,
                min_length=400,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                repetition_penalty=1.2,
                length_penalty=1.0
            )
            
            output = result[0]['generated_text']
            logger.info("Génération réussie")
            
            # Parser et valider le résultat
            parsed_result = self._parse_patent_output(output)
            return self._validate_and_enhance(parsed_result, cleaned_idea)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération: {e}")
            return self._create_fallback_patent(cleaned_idea)
    
    def _clean_input(self, raw_idea: str) -> str:
        """Nettoie et normalise l'entrée utilisateur."""
        # Supprime les caractères spéciaux problématiques
        cleaned = re.sub(r'[^\w\s\-.,;:!?()\[\]{}]', '', raw_idea)
        # Limite la taille pour éviter les prompts trop longs
        return cleaned[:500].strip()
    
    def _create_optimized_prompt(self, idea: str) -> str:
        """Crée un prompt optimisé pour FLAN-T5."""
        return f"""Transforme cette idée en brevet technique structuré:

Idée: "{idea}"

Format requis:
Titre: [Titre technique précis]
Problème: [Problème technique résolu]
Solution: [Description détaillée de l'invention]
Revendications:
1. [Revendication principale]
2. [Revendication dépendante]
3. [Revendication technique]
Code CPC: [Classification internationale]

Génère uniquement le brevet structuré."""
    
    def _parse_patent_output(self, text: str) -> Dict:
        """Extrait les champs du texte généré avec robustesse améliorée."""
        patterns = {
            'title': [
                r"Titre\s*:\s*(.+?)(?=\n|Problème|$)",
                r"Titre\s*[:\-]\s*(.+?)(?=\n|$)"
            ],
            'problem': [
                r"Problème(?:\s+technique)?\s*:\s*(.+?)(?=\n|Solution|$)",
                r"Problème\s*[:\-]\s*(.+?)(?=\n|$)"
            ],
            'solution': [
                r"Solution\s*:\s*(.+?)(?=\n|Revendications|$)",
                r"Solution\s*[:\-]\s*(.+?)(?=\n|$)"
            ],
            'cpc_code': [
                r"Code CPC\s*:\s*([A-Z]\d{2}[A-Z]\s*\d+/[\d\w]+)",
                r"CPC\s*:\s*([A-Z]\d{2}[A-Z]\s*\d+/[\d\w]+)"
            ]
        }
        
        result = {}
        
        # Extraction avec patterns multiples
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    result[field] = match.group(1).strip()
                    break
            else:
                result[field] = None
        
        # Extraction des revendications
        claims_matches = re.findall(r"(\d+)\.\s*(.+?)(?=\n\d+\.|$)", text, re.DOTALL)
        result['claims'] = [match[1].strip() for match in claims_matches] if claims_matches else []
        
        return result
    
    def _validate_and_enhance(self, parsed: Dict, original_idea: str) -> Dict:
        """Valide et améliore le résultat parsé."""
        # Valeurs par défaut améliorées
        defaults = {
            'title': f"Système innovant basé sur: {original_idea[:50]}...",
            'problem': "Résolution de limitations techniques existantes",
            'solution': f"Innovation technique répondant aux besoins identifiés: {original_idea[:100]}",
            'claims': [
                f"1. Dispositif caractérisé par l'implémentation de: {original_idea[:80]}",
                "2. Dispositif selon la revendication 1, comprenant des moyens de contrôle",
                "3. Procédé de mise en œuvre du dispositif selon les revendications précédentes"
            ],
            'cpc_code': self._estimate_cpc_code(original_idea),
        }
        
        # Application des defaults si nécessaire
        result = {}
        for key, default_value in defaults.items():
            value = parsed.get(key)
            if not value or (isinstance(value, list) and not value):
                result[key] = default_value
            else:
                result[key] = value
        
        # Calcul du score de nouveauté amélioré
        result['novelty_score'] = self._calculate_novelty_score(result, original_idea)
        
        return result
    
    @lru_cache(maxsize=100)
    def _estimate_cpc_code(self, idea: str) -> str:
        """Estime le code CPC basé sur des mots-clés."""
        idea_lower = idea.lower()
        
        cpc_mapping = {
            'médical': 'A61B 5/00',
            'électronique': 'H04L 29/08',
            'mécanique': 'F16H 25/00',
            'logiciel': 'G06F 9/46',
            'énergie': 'H02J 3/00',
            'transport': 'B60L 15/00',
            'communication': 'H04W 4/00',
            'robotique': 'B25J 9/16',
            'intelligence artificielle': 'G06N 3/08',
            'blockchain': 'G06Q 20/38'
        }
        
        for keyword, cpc in cpc_mapping.items():
            if keyword in idea_lower:
                return cpc
        
        return 'G06F 17/30'  # Code générique pour systèmes d'information
    
    def _calculate_novelty_score(self, patent_data: Dict, original_idea: str) -> int:
        """Calcule un score de nouveauté plus sophistiqué."""
        base_score = 60
        
        # Bonus pour la complexité technique
        complexity_bonus = min(len(patent_data['claims']) * 8, 25)
        
        # Bonus pour la longueur de la solution
        solution_bonus = min(len(patent_data['solution']) // 20, 15)
        
        # Bonus pour mots-clés innovants
        innovation_keywords = ['ia', 'intelligence artificielle', 'blockchain', 
                             'quantum', 'nanotechnologie', 'iot', 'machine learning']
        keyword_bonus = sum(5 for keyword in innovation_keywords 
                          if keyword in original_idea.lower())
        
        total_score = base_score + complexity_bonus + solution_bonus + keyword_bonus
        return min(total_score, 95)
    
    def _create_fallback_patent(self, idea: str) -> Dict:
        """Crée un brevet de base en cas d'échec de génération."""
        logger.warning("Utilisation du fallback patent")
        return {
            "title": f"Innovation technique: {idea[:50]}",
            "problem": "Amélioration des technologies existantes",
            "solution": f"Système innovant répondant aux besoins: {idea}",
            "claims": [
                f"1. Dispositif caractérisé par: {idea[:100]}",
                "2. Dispositif selon la revendication 1, avec moyens de contrôle optimisés",
                "3. Procédé d'utilisation du dispositif des revendications précédentes"
            ],
            "cpc_code": self._estimate_cpc_code(idea),
            "novelty_score": 65
        }

# Instance globale réutilisable
_patent_generator = None

def get_patent_generator() -> PatentGenerator:
    """Singleton pattern pour réutiliser l'instance."""
    global _patent_generator
    if _patent_generator is None:
        _patent_generator = PatentGenerator()
    return _patent_generator

# Fonction publique pour compatibilité
def generate_patent_structured(raw_idea: str) -> Dict:
    """Interface publique pour la génération de brevets."""
    generator = get_patent_generator()
    return generator.generate_patent_structured(raw_idea)
