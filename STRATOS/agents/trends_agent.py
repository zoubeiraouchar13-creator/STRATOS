from .base_agent import BaseAgent
from typing import Dict, Any
import csv
import os
import time
from datetime import datetime

class TrendsAgent(BaseAgent):
    """Agent responsable des Google Trends"""
    
    def __init__(self, csv_path: str = "data/trends_maroc.csv"):
        super().__init__(
            name="TrendsAgent",
            role="Analyse des tendances Google Maroc"
        )
        self.csv_path = csv_path
        self.cache = {"data": None, "timestamp": 0}
        self.cache_ttl = 3600  # 1 heure
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Récupère les tendances"""
        start_time = time.time()
        
        # Vérifier le cache
        now = time.time()
        if self.cache["data"] and (now - self.cache["timestamp"]) < self.cache_ttl:
            result = {
                "trends": self.cache["data"],
                "from_cache": True,
                "timestamp": datetime.now().isoformat()
            }
            self.log_execution(context, result, time.time() - start_time)
            return result
        
        # Lire depuis CSV
        trends = self._load_trends_from_csv()
        
        # Mettre en cache
        self.cache["data"] = trends
        self.cache["timestamp"] = now
        
        result = {
            "trends": trends,
            "from_cache": False,
            "count": len(trends),
            "timestamp": datetime.now().isoformat()
        }
        
        self.log_execution(context, result, time.time() - start_time)
        return result
    
    def _load_trends_from_csv(self):
        """Charge les tendances depuis le CSV"""
        fallback = [
            "Météo Maroc", "YouTube", "Actualités Maroc",
            "ChatGPT", "Économie Maroc", "Agriculture"
        ]
        
        if not os.path.exists(self.csv_path):
            self.logger.warning(f"Fichier {self.csv_path} non trouvé")
            return fallback
        
        try:
            trends = []
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i == 0:  # Skip header
                        continue
                    if row and len(row) >= 2:
                        trend = row[1].strip().strip('"')
                        if trend and len(trend) > 2 and not trend.isdigit():
                            trends.append(trend)
                    if len(trends) >= 10:
                        break
            
            return trends if trends else fallback
            
        except Exception as e:
            self.logger.error(f"Erreur chargement CSV: {e}")
            return fallback