"""
Le présent script regroupe les Outils LangChain pour STRATOS.
Chaque outil commence par @tool pour être utilisable par l'agent
"""

from langchain.tools import tool
from typing import List, Dict, Any, Optional
import requests
import xml.etree.ElementTree as ET
import csv
import os
from datetime import datetime
import hashlib
import chromadb
from chromadb.utils import embedding_functions

# ==================== CONFIGURATION ====================
''' A cet étape, il faut vérifier que les sources RSS sont toujours actives'''
# Sources internationales
INTERNATIONAL_SOURCES = [
    {"url": "http://feeds.bbci.co.uk/news/world/rss.xml", "source": "BBC World"},
    {"url": "http://rss.cnn.com/rss/edition_world.rss", "source": "CNN International"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "source": "Al Jazeera"},
    {"url": "https://www.france24.com/fr/france/rss", "source": "France 24"},
    {"url": "https://www.lemonde.fr/international/rss_full.xml", "source": "Le Monde"},
    {"url": "https://www.economist.com/international/rss.xml", "source": "The Economist"},
]

# Sources nationales
NATIONAL_SOURCES = [
    {"url": "https://www.medias24.com/feed", "source": "Médias24", "category": "Économie"},
    {"url": "https://telquel.ma/feed", "source": "TelQuel", "category": "Général"},
    {"url": "https://www.le360.ma/feed", "source": "Le360", "category": "Général"},
    {"url": "https://lematin.ma/feed", "source": "Le Matin", "category": "Général"},
    {"url": "https://www.leconomiste.com/feed", "source": "L'Économiste", "category": "Économie"},
    {"url": "https://www.mapnews.ma/fr/feed", "source": "MAP", "category": "Officiel"},
]

''' Mots-clés de filtrage, l'ajout de mots-clés permet de limiter le bruit 
et d'augmenter la pertinence des articles collectés'''
KEYWORDS = ["maroc", "morocco", "maghreb", "sahara", "économie", 
            "investissement", "agriculture", "phosphates", "gazoduc", "tourisme"]

# Cache pour ChromaDB
CHROMA_PATH = "./memory/vector_store"

# ==================== INITIALISATION RAG MULTI-CORPUS ====================
_client = None
_corpora = None

def _get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _client

def _get_embedding_function():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

def _get_corpora():
    """Initialise les 4 corpus spécialisés pour le RAG multi-corpus
    Ainsi, nous aurons les corpus suivant : iternational, national, officiel et historique"""
    global _corpora
    if _corpora is None:
        client = _get_chroma_client()
        embedding_fn = _get_embedding_function()
        
        _corpora = {
            "international": client.get_or_create_collection(
                name="corpus_international",
                embedding_function=embedding_fn
            ),
            "national": client.get_or_create_collection(
                name="corpus_national",
                embedding_function=embedding_fn
            ),
            "officiel": client.get_or_create_collection(
                name="corpus_officiel",
                embedding_function=embedding_fn
            ),
            "historique": client.get_or_create_collection(
                name="corpus_historique",
                embedding_function=embedding_fn
            )
        }
    return _corpora

# ==================== OUTIL 1 : COLLECTE RSS ====================

@tool
def collect_rss(source_type: str = "both") -> List[Dict[str, Any]]:
    """
    Collecte les actualités RSS des sources internationales et nationales.
    
    Args:
        source_type: 'both', 'international', ou 'national'
    
    Returns:
        Liste des articles avec titre, source, résumé, date
    """
    articles = []
    
    if source_type in ["both", "international"]:
        for feed in INTERNATIONAL_SOURCES:
            try:
                r = requests.get(feed["url"], timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200:
                    root = ET.fromstring(r.text)
                    for item in root.findall('.//item')[:10]:
                        title = (item.findtext('title') or '').strip()
                        summary = (item.findtext('description') or '')[:300]
                        text = (title + " " + summary).lower()
                        
                        if any(kw in text for kw in KEYWORDS):
                            articles.append({
                                "title": title,
                                "summary": summary,
                                "source": feed["source"],
                                "type": "international",
                                "link": (item.findtext('link') or '#'),
                                "timestamp": datetime.now().isoformat()
                            })
            except Exception as e:
                print(f"Erreur {feed['source']}: {e}")
    
    if source_type in ["both", "national"]:
        for feed in NATIONAL_SOURCES:
            try:
                r = requests.get(feed["url"], timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200:
                    root = ET.fromstring(r.text)
                    for item in root.findall('.//item')[:15]:
                        articles.append({
                            "title": (item.findtext('title') or '').strip(),
                            "summary": (item.findtext('description') or '')[:300],
                            "source": feed["source"],
                            "category": feed.get("category", "Général"),
                            "type": "national",
                            "link": (item.findtext('link') or '#'),
                            "timestamp": datetime.now().isoformat()
                        })
            except Exception as e:
                print(f"Erreur {feed['source']}: {e}")
    
    return articles[:50]

# ==================== OUTIL 2 : RAG MULTI-CORPUS ====================

@tool
def index_articles(articles: List[Dict[str, Any]]) -> str:
    """
    Indexe les articles dans la base vectorielle multi-corpus.
    Les articles sont répartis selon leur type (international, national, officiel).
    
    Args:
        articles: Liste des articles à indexer
    
    Returns:
        Message indiquant le nombre d'articles indexés
    """
    corpora = _get_corpora()
    indexed_count = 0
    
    for article in articles:
        doc_id = hashlib.md5(article['title'].encode()).hexdigest()
        text = f"{article['title']}\n{article['summary']}"
        
        # Choix du corpus selon le type de source
        source = article.get('source', '').lower()
        article_type = article.get('type', 'international')
        
        if article_type == 'national':
            if 'map' in source or 'officiel' in source:
                corpus_name = "officiel"
            else:
                corpus_name = "national"
        else:
            corpus_name = "international"
        
        # Vérifier si déjà indexé
        existing = corpora[corpus_name].get(ids=[doc_id])
        if not existing['ids']:
            corpora[corpus_name].add(
                ids=[doc_id],
                documents=[text],
                metadatas=[{
                    "source": article.get('source', ''),
                    "type": article_type,
                    "timestamp": article.get('timestamp', '')
                }]
            )
            indexed_count += 1
    
    return f"{indexed_count} articles indexés dans le RAG multi-corpus"

@tool
def search_rag(query: str, corpora_list: Optional[List[str]] = None) -> str:
    """
    Recherche dans la base vectorielle multi-corpus.
    Permet de limiter la recherche à certains corpus spécifiques.
    
    Args:
        query: La requête de recherche
        corpora_list: Liste des corpus à interroger (default: tous)
                     Options: 'international', 'national', 'officiel', 'historique'
    
    Returns:
        Contexte enrichi avec les documents pertinents
    """
    corpora = _get_corpora()
    
    if corpora_list is None:
        corpora_list = ["international", "national", "officiel"]
    
    all_results = []
    
    for corpus_name in corpora_list:
        if corpus_name in corpora:
            results = corpora[corpus_name].query(
                query_texts=[query],
                n_results=3
            )
            
            if results['documents'] and results['documents'][0]:
                for doc, distance in zip(results['documents'][0], results['distances'][0]):
                    all_results.append({
                        "document": doc,
                        "score": 1 - distance,  # Convertir distance en similarité
                        "corpus": corpus_name
                    })
    
    # Trier par score et prendre les top 5
    all_results.sort(key=lambda x: x['score'], reverse=True)
    top_results = all_results[:5]
    
    if not top_results:
        return "Aucun contexte pertinent trouvé dans la base RAG."
    
    # Formater le contexte
    context_parts = ["=== CONTEXTE RAG MULTI-CORPUS ===\n"]
    
    for i, result in enumerate(top_results, 1):
        source_label = {
            "international": "🌍 Sources internationales",
            "national": "🇲🇦 Sources nationales",
            "officiel": "🏛️ Sources officielles",
            "historique": "📜 Contexte historique"
        }.get(result['corpus'], result['corpus'])
        
        context_parts.append(f"[{i}] {source_label}:")
        context_parts.append(f"{result['document'][:300]}...")
        context_parts.append(f"    (pertinence: {result['score']:.2f})\n")
    
    return "\n".join(context_parts)

# ==================== OUTIL 3 : GOOGLE TRENDS ====================

@tool
def get_google_trends() -> List[str]:
    """
    Récupère les tendances Google Maroc depuis le fichier CSV.
    
    Returns:
        Liste des 10 tendances actuelles
    """
    csv_path = "data/trends_maroc.csv"
    
    ''' Nous ajoutons un fallback pour garantir que l'outil retourne 
    toujours des tendances même si le fichier est manquant ou corrompu'''
    
    fallback = ["Météo Maroc", "YouTube", "Actualités Maroc", "ChatGPT", "Économie Maroc"]
    
    if not os.path.exists(csv_path):
        return fallback
    
    try:
        trends = []
        with open(csv_path, 'r', encoding='utf-8') as f:
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
        print(f"Erreur chargement trends: {e}")
        return fallback

# ==================== OUTIL 4 : ANALYSE (utilitaires) ====================

@tool
def format_analysis(analysis: str) -> str:
    """
    Formate l'analyse pour l'affichage (post-traitement).
    
    Args:
        analysis: Analyse brute générée par le LLM
    
    Returns:
        Analyse formatée avec HTML
    """
    formatted = analysis
    formatted = formatted.replace("**", "<strong>").replace("**", "</strong>")
    formatted = formatted.replace("## ", "<h3>").replace(" ##", "</h3>")
    formatted = formatted.replace("\n", "<br>")
    return formatted