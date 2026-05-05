'''
Le script app.py est le point d'entrée de l'application STRATOS. 
Il utilise Flask pour créer une interface web simple qui permet à 
l'utilisateur de déclencher l'exécution du workflow LangGraph.
Contrairement à STREAMLIT, Flask offre une plus grande flexibilité pour 
la personnalisation de l'interface et la gestion des requêtes API, ainsi que 
le choix du PORT utilisé, ce qui est idéal pour une application plus complexe 
comme STRATOS.
'''

from flask import Flask, render_template, jsonify, request
from agents.orchestrator_agent import OrchestratorAgent
import os
from dotenv import load_dotenv
import time
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

load_dotenv()

# Configuration LangSmith
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "STRATOS")

app = Flask(__name__)

# Initialisation de l'orchestrateur LangGraph
orchestrator = OrchestratorAgent(human_in_loop=False)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/run_workflow", methods=["POST"])
def run_workflow():
    """Exécute le workflow LangGraph"""
    data = request.get_json() or {}
    source_type = data.get("source_type", "both")
    analysis_type = data.get("analysis_type", "impact")
    hitl_mode = data.get("hitl_mode", "auto")
    
    # Activer HITL si demandé
    if hitl_mode == "manual":
        orchestrator.human_in_loop = True
    else:
        orchestrator.human_in_loop = False
    
    metadata = {
        "source_type": source_type,
        "analysis_type": analysis_type,
        "hitl_mode": hitl_mode,
        "timestamp": time.time()
    }
    # Exécution du workflow
    result = orchestrator.run(source_type, analysis_type)
    
    return jsonify({
        "status": result.get("status"),
        "articles": result.get("articles", [])[:30],
        "trends": result.get("trends", []),
        "analysis": result.get("analysis", ""),
        "workflow_duration": result.get("workflow_duration", 0),
        "current_step": result.get("current_step")
    })

@app.route("/api/health")
def health():
    """Endpoint de santé pour vérifier que le système fonctionne"""
    return jsonify({
        "status": "healthy",
        "orchestrator": "LangGraph",
        "rag_multi_corpus": True,
        "corpora": ["international", "national", "officiel", "historique"]
    })

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🇲🇦 STRATOS v2.0 - Architecture LangChain/LangGraph")
    print("="*60)
    print("🎯 Orchestration: LangGraph (séquentiel)")
    print("📚 RAG: Multi-corpus (4 collections)")
    print("🔧 Agents: @tool decorators")
    print("👤 HITL: Intégré nativement")
    print("")
    print(f"🌐 Interface: http://localhost:5002")
    print("="*60 + "\n")
    
    app.run(debug=True, host="0.0.0.0", port=5002)
    '''Ici nous avons choisi le port 5002 pour éviter les conflits avec d'autres applications, 
    mais cela peut être configuré selon les besoins.'''
