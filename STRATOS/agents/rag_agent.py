from .base_agent import BaseAgent
from typing import Dict, Any, List
import time
from datetime import datetime
import hashlib

class RAGAgent(BaseAgent):
    """
    Agent RAG Multi-Corpus
    - Corpus 1 : International
    - Corpus 2 : National
    - Corpus 3 : Officiel (MAP)
    - Corpus 4 : Historique (anciens articles)
    """
    
    def __init__(self):
        super().__init__(
            name="RAGAgent",
            role="Recherche vectorielle multi-corpus pour enrichir le contexte"
        )
        
        # 4 corpus distincts
        self.corpora = {
            "international": [],   # BBC, CNN, Al Jazeera, etc.
            "national": [],        # Médias24, TelQuel, Le360, etc.
            "officiel": [],        # MAP uniquement
            "historique": []       # Articles archivés (pour mémoire longue)
        }
        
        # Métadonnées par corpus
        self.corpora_stats = {
            "international": {"count": 0, "last_index": None},
            "national": {"count": 0, "last_index": None},
            "officiel": {"count": 0, "last_index": None},
            "historique": {"count": 0, "last_index": None}
        }
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute la recherche RAG multi-corpus"""
        start_time = time.time()
        
        query = context.get("query", "")
        articles = context.get("articles", [])
        corpora_filter = context.get("corpora", ["international", "national", "officiel"])
        
        # Indexer les nouveaux articles (répartition automatique par corpus)
        if articles:
            self._index_articles_multi(articles)
        
        # Recherche dans les corpus spécifiés
        all_relevant_docs = []
        
        for corpus_name in corpora_filter:
            if corpus_name in self.corpora:
                docs = self._search_in_corpus(query, corpus_name, k=3)
                all_relevant_docs.extend(docs)
        
        # Enrichir le contexte avec pondération par corpus
        enriched_context = self._enrich_context_multi(
            query, articles, all_relevant_docs, corpora_filter
        )
        
        # Statistiques
        total_docs = sum(len(c) for c in self.corpora.values())
        
        result = {
            "relevant_documents": all_relevant_docs[:5],
            "enriched_context": enriched_context,
            "documents_count": total_docs,
            "corpora_stats": self.corpora_stats,
            "corpora_used": corpora_filter,
            "search_query": query,
            "timestamp": datetime.now().isoformat()
        }
        
        self.log_execution(context, result, time.time() - start_time)
        return result
    
    def _index_articles_multi(self, articles: List[Dict]):
        """Indexe les articles dans le corpus approprié selon leur source"""
        
        for article in articles:
            doc_id = hashlib.md5(article['title'].encode()).hexdigest()
            source = article.get('source', '').lower()
            article_type = article.get('type', 'international')
            
            # Déterminer le corpus cible
            corpus_name = self._get_corpus_for_article(article)
            
            # Vérifier si déjà indexé
            existing_ids = [a.get('id') for a in self.corpora[corpus_name]]
            
            if doc_id not in existing_ids:
                self.corpora[corpus_name].append({
                    'id': doc_id,
                    'title': article['title'],
                    'summary': article['summary'],
                    'source': article.get('source', ''),
                    'type': article_type,
                    'indexed_at': datetime.now().isoformat()
                })
                
                # Mettre à jour les stats
                self.corpora_stats[corpus_name]["count"] += 1
                self.corpora_stats[corpus_name]["last_index"] = datetime.now().isoformat()
                
                self.logger.info(f"📚 Indexé dans [{corpus_name}]: {article['title'][:50]}...")
    
    def _get_corpus_for_article(self, article: Dict) -> str:
        """
        Détermine le corpus cible en fonction de la source
        """
        source = article.get('source', '').lower()
        article_type = article.get('type', 'international')
        
        # Règle 1 : Sources officielles (MAP)
        if 'map' in source or 'officiel' in source:
            return "officiel"
        
        # Règle 2 : Sources nationales
        if article_type == 'national':
            return "national"
        
        # Règle 3 : Sources internationales
        if article_type == 'international':
            return "international"
        
        # Par défaut
        return "national"
    
    def _search_in_corpus(self, query: str, corpus_name: str, k: int = 3) -> List[Dict]:
        """
        Recherche dans un corpus spécifique
        """
        results = []
        
        for article in self.corpora[corpus_name][-50:]:  # Limiter aux 50 plus récents
            # Recherche simple (titre + résumé)
            text = (article['title'] + ' ' + article['summary']).lower()
            if query.lower() in text:
                results.append({
                    **article,
                    "corpus": corpus_name,
                    "score": self._calculate_relevance(query, article)
                })
        
        # Trier par score et prendre les k meilleurs
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:k]
    
    def _calculate_relevance(self, query: str, article: Dict) -> float:
        """
        Calcule un score de pertinence simple
        """
        text = (article['title'] + ' ' + article['summary']).lower()
        query_words = query.lower().split()
        
        # Nombre de mots de la requête trouvés
        hits = sum(1 for word in query_words if word in text)
        
        # Score normalisé
        return hits / max(len(query_words), 1)
    
    def _enrich_context_multi(self, query: str, current_articles: List[Dict], 
                               relevant_docs: List[Dict], corpora_used: List[str]) -> str:
        """
        Enrichit le contexte avec distinction des corpus
        """
        context_parts = []
        
        # 1. Actualités actuelles
        if current_articles:
            context_parts.append("=== 📰 ACTUALITÉS RÉCENTES ===")
            for a in current_articles[:10]:
                source_type = "🌍" if a.get('type') == 'international' else "🇲🇦"
                context_parts.append(f"{source_type} {a['title']}")
        
        # 2. Contexte multi-corpus (avec labels)
        if relevant_docs:
            context_parts.append("\n=== 📚 CONTEXTE RAG MULTI-CORPUS ===")
            
            corpus_labels = {
                "international": "🌍 Sources internationales",
                "national": "🇲🇦 Sources nationales", 
                "officiel": "🏛️ Sources officielles (MAP)",
                "historique": "📜 Contexte historique"
            }
            
            # Grouper par corpus
            docs_by_corpus = {}
            for doc in relevant_docs:
                corpus = doc.get("corpus", "national")
                if corpus not in docs_by_corpus:
                    docs_by_corpus[corpus] = []
                docs_by_corpus[corpus].append(doc)
            
            for corpus, docs in docs_by_corpus.items():
                context_parts.append(f"\n{corpus_labels.get(corpus, corpus)}:")
                for doc in docs[:2]:
                    context_parts.append(f"   • {doc['title']}")
        else:
            context_parts.append("\n=== 📚 CONTEXTE RAG ===")
            context_parts.append("Aucun document pertinent trouvé dans les corpus.")
        
        return "\n".join(context_parts)
    
    def search_in_corpus_only(self, corpus_name: str, query: str, k: int = 5) -> List[Dict]:
        """
        Méthode utilitaire : recherche uniquement dans un corpus spécifique
        Utile pour filtrer par type de source
        """
        return self._search_in_corpus(query, corpus_name, k)
    
    def get_corpora_stats(self) -> Dict:
        """Retourne les statistiques des 4 corpus"""
        return self.corpora_stats
