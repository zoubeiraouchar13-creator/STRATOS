"""
Agent Orchestrateur utilisant LangGraph
Gère le workflow séquentiel avec Human-in-the-Loop
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
import os
from dotenv import load_dotenv

from .tools import collect_rss, index_articles, search_rag, get_google_trends
from langsmith import traceable
import time

load_dotenv()

# ==================== DÉFINITION DE L'ÉTAT ====================

class StratosState(TypedDict):
    """État partagé entre tous les agents du workflow"""
    # Paramètres d'entrée
    source_type: str
    analysis_type: str
    human_in_loop: bool
    
    # Données collectées
    articles: List[Dict[str, Any]]
    trends: List[str]
    rag_context: str
    
    # Analyse
    analysis: str
    
    # État du workflow
    current_step: str
    human_feedback: Optional[str]
    errors: Annotated[List[str], operator.add]
    
    # Métadonnées
    workflow_id: str
    start_time: float
    end_time: Optional[float]

# ==================== AGENT ORCHESTRATEUR ====================

class OrchestratorAgent:
    """
    Orchestrateur utilisant LangGraph pour un workflow séquentiel
    avec support Human-in-the-Loop natif
    """
    
    def __init__(self, human_in_loop: bool = False):
        self.human_in_loop = human_in_loop
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.7,
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Construction du graphe
        self.graph = self._build_graph()
        
        # Sauvegarde d'état persistante
        self.memory = InMemorySaver()
    
    def _build_graph(self) -> StateGraph:
        """Construit le graphe LangGraph du workflow"""
        
        builder = StateGraph(StratosState)
        
        # Ajout des nœuds (chaque nœud = une étape du workflow)
        builder.add_node("collect", self._collect_node)
        builder.add_node("index_rag", self._index_rag_node)
        builder.add_node("search_rag", self._search_rag_node)
        builder.add_node("trends", self._trends_node)
        builder.add_node("analyze", self._analyze_node)
        builder.add_node("format_result", self._format_node)
        
        # Ajout des nœuds de checkpoint humain si HITL activé
        if self.human_in_loop:
            builder.add_node("human_checkpoint_1", self._human_checkpoint_node)
            builder.add_node("human_checkpoint_2", self._human_checkpoint_node)
            builder.add_node("human_checkpoint_3", self._human_checkpoint_node)
        
        # Définition des arêtes (workflow séquentiel)
        builder.set_entry_point("collect")
        
        if self.human_in_loop:
            builder.add_edge("collect", "human_checkpoint_1")
            builder.add_conditional_edges(
                "human_checkpoint_1",
                self._check_continue,
                {"continue": "index_rag", "stop": END}
            )
            builder.add_edge("index_rag", "search_rag")
            builder.add_edge("search_rag", "trends")
            builder.add_edge("trends", "human_checkpoint_2")
            builder.add_conditional_edges(
                "human_checkpoint_2",
                self._check_continue,
                {"continue": "analyze", "stop": END}
            )
            builder.add_edge("analyze", "human_checkpoint_3")
            builder.add_conditional_edges(
                "human_checkpoint_3",
                self._check_continue,
                {"continue": "format_result", "stop": END}
            )
        else:
            builder.add_edge("collect", "index_rag")
            builder.add_edge("index_rag", "search_rag")
            builder.add_edge("search_rag", "trends")
            builder.add_edge("trends", "analyze")
        
        builder.add_edge("format_result", END)
        
        return builder.compile()
    
    # ==================== NOEUDS D'EXÉCUTION ====================
    
    def _collect_node(self, state: StratosState) -> StratosState:
        """Nœud 1 : Collecte des actualités"""
        print("📡 [Orchestrateur] Agent 1/5: Collecte RSS...")
        
        articles = collect_rss.invoke({"source_type": state["source_type"]})
        
        return {
            **state,
            "articles": articles,
            "current_step": "collect_completed"
        }
    
    def _index_rag_node(self, state: StratosState) -> StratosState:
        """Nœud 2 : Indexation des articles dans le RAG multi-corpus"""
        print("🗂️ [Orchestrateur] Agent 2/5: Indexation RAG multi-corpus...")
        
        result = index_articles.invoke({"articles": state["articles"]})
        print(f"   {result}")
        
        return {
            **state,
            "current_step": "index_completed"
        }
    
    def _search_rag_node(self, state: StratosState) -> StratosState:
        """Nœud 3 : Recherche RAG pour enrichir le contexte"""
        print("🔍 [Orchestrateur] Agent 3/5: Recherche RAG multi-corpus...")
        
        # Recherche dans tous les corpus
        rag_context = search_rag.invoke({
            "query": "actualités Maroc impact économique et géopolitique",
            "corpora_list": None  # Tous les corpus
        })
        
        return {
            **state,
            "rag_context": rag_context,
            "current_step": "search_completed"
        }
    
    def _trends_node(self, state: StratosState) -> StratosState:
        """Nœud 4 : Récupération des tendances Google"""
        print("📈 [Orchestrateur] Agent 4/5: Google Trends...")
        
        trends = get_google_trends.invoke({})
        
        return {
            **state,
            "trends": trends,
            "current_step": "trends_completed"
        }
    
    def _analyze_node(self, state: StratosState) -> StratosState:
        """Nœud 5 : Génération de l'analyse par l'agent Analyste"""
        print("🤖 [Orchestrateur] Agent 5/5: Génération de l'analyse...")
        
        # Construction du prompt
        prompt = self._build_analysis_prompt(state)
        
        # Appel LLM
        response = self.llm.invoke(prompt)
        
        return {
            **state,
            "analysis": response.content,
            "current_step": "analysis_completed",
            "end_time": datetime.now().timestamp()
        }
    
    def _format_node(self, state: StratosState) -> StratosState:
        """Nœud final : Formatage des résultats"""
        print("📝 [Orchestrateur] Formatage des résultats...")
        
        return {
            **state,
            "current_step": "completed"
        }
    
    # ==================== HUMAN-IN-THE-LOOP ====================
    
    def _human_checkpoint_node(self, state: StratosState) -> StratosState:
        """Point de contrôle pour validation humaine"""
        step = state["current_step"]
        
        print("\n" + "="*60)
        print(f"🛑 CHECKPOINT HUMAIN - Étape: {step}")
        print("="*60)
        
        if step == "collect_completed":
            print(f"📊 {len(state['articles'])} articles collectés")
            print("\nAperçu des 3 premiers articles:")
            for i, article in enumerate(state["articles"][:3], 1):
                print(f"   {i}. {article['title'][:80]}...")
        
        elif step == "trends_completed":
            print(f"📈 Tendances Google: {', '.join(state['trends'][:5])}")
        
        elif step == "analysis_completed":
            print(f"📝 Analyse générée ({len(state['analysis'])} caractères)")
            print("\nAperçu:")
            print(state["analysis"][:400] + "...")
        
        print("\n" + "-"*40)
        feedback = input("Action (valider/modifier/annuler): ").lower()
        
        return {
            **state,
            "human_feedback": feedback
        }
    
    def _check_continue(self, state: StratosState) -> str:
        """Vérifie si le workflow doit continuer après HITL"""
        feedback = state.get("human_feedback", "valider")
        
        if feedback == "annuler":
            print("⏸️ Workflow interrompu par l'utilisateur")
            return "stop"
        elif feedback == "modifier":
            # Ici on pourrait implémenter une logique de modification
            print("✏️ Mode modification (à implémenter)")
            return "continue"
        else:
            return "continue"
    
    # ==================== CONSTRUCTION DU PROMPT ====================
    
    def _build_analysis_prompt(self, state: StratosState) -> str:
        """Construit le prompt pour l'agent analyste"""
        titles = [a['title'] for a in state["articles"][:15]]
        
        trends_text = "\n".join([f"   {i+1}. {t}" for i, t in enumerate(state["trends"][:10])])
        
        if state["analysis_type"] == "impact":
            return f"""Tu es un expert en géopolitique spécialiste du Maroc.

**ACTUALITÉS INTERNATIONALES RÉCENTES :**
{chr(10).join(f'• {t}' for t in titles)}

**TENDANCES GOOGLE MAROC :**
{trends_text}

**CONTEXTE RAG :**
{state['rag_context']}

**OBJECTIF :** Analyser l'impact de ces actualités sur le Maroc.

Structure ta réponse en 4 sections :
1. **🌍 FAITS MARQUANTS** - Synthèse des événements majeurs
2. **🎯 IMPACTS SUR LE MAROC** - Opportunités et risques
3. **📊 LIENS AVEC LES TENDANCES GOOGLE** - Corrélations observées
4. **📝 RECOMMANDATIONS** - Actions pour les décideurs

 Utilise toujours "Sahara marocain" (jamais "occidental").
Réponds en français. Environ 500 mots."""
        
        else:
            return f"""Tu es un analyste spécialiste du Maroc.

**ACTUALITÉS NATIONALES :**
{chr(10).join(f'• {t}' for t in titles)}

**TENDANCES GOOGLE MAROC :**
{trends_text}

**OBJECTIF :** Produire une synthèse de l'actualité marocaine.

Structure :
1. **📊 VUE D'ENSEMBLE**
2. **💰 ÉCONOMIE & FINANCES**
3. **🌾 AGRICULTURE & EAU**
4. **🏛️ POLITIQUE & GOUVERNANCE**
5. **👥 SOCIAL & TERRITOIRES**

Réponds en français. Environ 500 mots."""
    
    # ==================== EXÉCUTION PUBLIQUE ====================
    @traceable(run_type="chain", name="orchestrator_workflow")
    def run(self, source_type: str = "both", analysis_type: str = "impact") -> Dict:
        """
        Exécute le workflow complet
        
        Args:
            source_type: 'both', 'international', 'national'
            analysis_type: 'impact', 'national'
        
        Returns:
            Résultat du workflow
        """
        workflow_start = time.time()
        
        initial_state: StratosState = {
            "source_type": source_type,
            "analysis_type": analysis_type,
            "human_in_loop": self.human_in_loop,
            "articles": [],
            "trends": [],
            "rag_context": "",
            "analysis": "",
            "current_step": "start",
            "human_feedback": None,
            "errors": [],
            "workflow_id": f"wf_{datetime.now().timestamp()}",
            "start_time": datetime.now().timestamp(),
            "end_time": None
        }
        
        print("\n" + "="*60)
        print("🚀 STRATOS - Orchestration LangGraph")
        print("="*60)
        print(f"🎯 Source: {source_type} | Analyse: {analysis_type}")
        print(f"👤 HITL: {'Activé' if self.human_in_loop else 'Désactivé'}")
        print("="*60 + "\n")
        
        # Exécution du graphe
        config = {"configurable": {"thread_id": initial_state["workflow_id"]}}
        final_state = self.graph.invoke(initial_state, config=config)
        
        duration = final_state["end_time"] - final_state["start_time"] if final_state["end_time"] else 0
        
        print("\n" + "="*60)
        print(f"✅ WORKFLOW TERMINÉ en {duration:.2f} secondes")
        print("="*60)
        
        return {
            "status": "completed",
            "articles": final_state["articles"],
            "trends": final_state["trends"],
            "analysis": final_state["analysis"],
            "workflow_duration": duration,
            "current_step": final_state["current_step"]
        }