from .base_agent import BaseAgent
from typing import Dict, Any, List
from groq import Groq
import os
import time
from datetime import datetime

class AnalystAgent(BaseAgent):
    """Agent responsable de l'analyse et de la synthèse"""
    
    def __init__(self):
        # Correction ici : passer name et role correctement
        super().__init__(
            name="AnalystAgent",
            role="Génération de synthèses et analyses d'impact"
        )
        
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            self.groq_client = Groq(api_key=api_key)
            self.available = True
        else:
            self.available = False
            self.logger.warning("Groq API non disponible")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Génère une analyse"""
        start_time = time.time()
        
        if not self.available:
            return {"error": "Groq API non disponible"}
        
        articles = context.get("articles", [])
        enriched_context = context.get("enriched_context", "")
        trends = context.get("trends", [])  # Récupérer les tendances
        analysis_type = context.get("analysis_type", "impact")
        
        # Construire le prompt avec les tendances
        prompt = self._build_prompt(articles, trends, enriched_context, analysis_type)
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000,
            )
            
            analysis = response.choices[0].message.content
            
            result = {
                "analysis": analysis,
                "type": analysis_type,
                "articles_analyzed": len(articles),
                "trends_used": len(trends),
                "timestamp": datetime.now().isoformat()
            }
            
            self.log_execution(context, result, time.time() - start_time)
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur d'analyse: {e}")
            return {"error": str(e)}
    
    def _build_prompt(self, articles, trends, enriched_context, analysis_type):
        """Construit le prompt pour l'IA"""
        titles = [a['title'] for a in articles[:15]]
        
        # Formatage des tendances
        trends_text = ""
        if trends:
            trends_text = "\n\n📊 **TENDANCES GOOGLE MAROC :**\n"
            for i, trend in enumerate(trends[:10], 1):
                trends_text += f"{i}. {trend}\n"
        
        if analysis_type == "impact":
            return f"""Tu es un expert en géopolitique spécialiste du Maroc.

**ACTUALITÉS INTERNATIONALES :**
{chr(10).join(f'• {t}' for t in titles)}

{trends_text}

{enriched_context}

**OBJECTIF :** Analyser l'impact de ces actualités sur le Maroc.

Structure ta réponse :
1. **🌍 FAITS MARQUANTS**
2. **🇲🇦 IMPACTS SUR LE MAROC**
3. **📊 LIENS AVEC LES TENDANCES GOOGLE**
4. **🎯 RECOMMANDATIONS**

Utilise "Sahara marocain". Réponds en français. Environ 400 mots."""
        
        else:
            return f"""Tu es un analyste spécialiste du Maroc.

**ACTUALITÉS NATIONALES :**
{chr(10).join(f'• {t}' for t in titles)}

{trends_text}

**OBJECTIF :** Produire une synthèse de l'actualité marocaine.

Structure :
1. **📊 VUE D'ENSEMBLE**
2. **💰 ÉCONOMIE & FINANCES**
3. **🌾 AGRICULTURE & EAU**
4. **🏛️ POLITIQUE & GOUVERNANCE**
5. **👥 SOCIAL & TERRITOIRES**

Réponds en français. Environ 400 mots."""