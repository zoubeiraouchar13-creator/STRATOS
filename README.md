STRATOS : Système Multi-Agent de Veille Stratégique

STRATOS (Système de Traitement et d'Analyse Stratégique Orienté Synthèse) est un système multi-agent intelligent dédié à la veille stratégique sur le Maroc. Il collecte automatiquement les actualités nationales et internationales, enrichit le contexte via recherche vectorielle (RAG), intègre les tendances Google, et génère des analyses d'impact structurées.

🚀 Fonctionnalités
Fonctionnalité	Description
🤖 5 Agents spécialisés	Collecteur RSS, RAG Vectoriel, Google Trends, Analyste IA
🔄 Orchestration séquentielle	Workflow clair avec points de contrôle
👤 Human-in-the-Loop	3 points de validation humaine (collecte, tendances, analyse)
📚 RAG Agentique	Base vectorielle ChromaDB + embeddings sémantiques
📈 Google Trends	Intégration des tendances de recherche Maroc
🎯 Analyse d'impact	Synthèse structurée des impacts sur le Maroc
🌐 Interface Web	Dashboard temps réel (Flask + HTML/CSS/JS)

📋 Prérequis
Python : 3.12 ou supérieur
RAM : 8 Go minimum (16 Go recommandé)
Stockage : 2 Go disponibles
Connexion Internet : Requise pour les API (Groq, flux RSS)
Clé API : Groq (gratuite)

⚙️ Installation
1. Cloner le projet
  git clone https://github.com/votre-username/STRATOS.git
  cd STRATOS
2. Créer un environnement virtuel
  python -m venv .venv
  .venv\Scripts\activate
3. Installer les dépendances
  pip install -r requirements.txt
4. Configurer la clé API Groq
  Créez un fichier .env à la racine : GROQ_API_KEY=votre_clé_api_groq_ici
5. Lancer l'application
  python app.py
  L'application est accessible sur : http://localhost:5002

🎮 Utilisation
Via l'interface web
Ouvrez http://localhost:5002
Sélectionnez :
Source : International + National / International seul / National seul
Type d'analyse : Impact international / Synthèse nationale
Mode : Automatique / Avec validation humaine
Cliquez sur LANCER LE WORKFLOW
Consultez les actualités collectées, les tendances et l'analyse générée

📁 Structure du projet
STRATOS/
├── app.py                          # Application Flask
├── requirements.txt                # Dépendances Python
├── .env                            # Variables d'environnement
├── agents/
│   ├── __init__.py                 # Initialisation du package
│   ├── base_agent.py               # Classe abstraite BaseAgent
│   ├── collector_agent.py          # Agent 1 : Collecteur RSS
│   ├── rag_agent.py                # Agent 2 : RAG Vectoriel
│   ├── trends_agent.py             # Agent 3 : Google Trends
│   ├── analyst_agent.py            # Agent 4 : Analyste IA
│   └── orchestrator.py             # Orchestrateur séquentiel
├── templates/
│   └── index.html                  # Interface utilisateur
├── static/
│   └── css/
│       └── style.css               # Styles CSS
├── data/
│   └── trends_maroc.csv            # Données Google Trends
└── memory/
    └── human_validations.json      # Journal des interventions HITL
