from .base_agent import BaseAgent
from typing import Dict, Any, List
import time
from datetime import datetime
import hashlib

class RAGAgent(BaseAgent):
    """Agent responsable de la recherche augmentée (RAG)"""
    
    def __init__(self):
        super().__init__(
            name="RAGAgent",
            role="Recherche vectorielle pour enrichir le contexte des analyses"
        )
        self.indexed_articles = []
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute la recherche RAG"""
        start_time = time.time()
        
        query = context.get("query", "")
        articles = context.get("articles", [])
        
        # Indexer les nouveaux articles
        if articles:
            self._index_articles(articles)
        
        # Recherche simple sans ChromaDB (pour éviter les erreurs)
        relevant_docs = []
        if query:
            for art in self.indexed_articles[-10:]:
                if query.lower() in art['title'].lower() or query.lower() in art['summary'].lower():
                    relevant_docs.append(art)
        
        # Enrichir le contexte
        enriched_context = self._enrich_context(query, articles, relevant_docs)
        
        result = {
            "relevant_documents": relevant_docs,
            "enriched_context": enriched_context,
            "documents_count": len(self.indexed_articles),
            "search_query": query,
            "timestamp": datetime.now().isoformat()
        }
        
        self.log_execution(context, result, time.time() - start_time)
        return result
    
    def _index_articles(self, articles: List[Dict]):
        """Indexe les articles en mémoire"""
        for article in articles:
            doc_id = hashlib.md5(article['title'].encode()).hexdigest()
            # Vérifier si déjà indexé
            existing_ids = [a.get('id') for a in self.indexed_articles]
            if doc_id not in existing_ids:
                self.indexed_articles.append({
                    'id': doc_id,
                    'title': article['title'],
                    'summary': article['summary'],
                    'source': article.get('source', '')
                })
                self.logger.info(f"Indexé: {article['title'][:50]}...")
    
    def _enrich_context(self, query: str, current_articles: List[Dict], relevant_docs: List[Dict]) -> str:
        """Enrichit le contexte avec les documents similaires"""
        context_parts = []
        
        # Actualités actuelles
        if current_articles:
            context_parts.append("=== ACTUALITÉS RÉCENTES ===")
            for a in current_articles[:10]:
                context_parts.append(f"- {a['title']}")
        
        # Contexte historique pertinent
        if relevant_docs:
            context_parts.append("\n=== CONTEXTE HISTORIQUE PERTINENT ===")
            for doc in relevant_docs[:3]:
                context_parts.append(f"* {doc['title']}")
        
        return "\n".join(context_parts)