# STRATOS : Système Multi-Agent de Veille Stratégique

STRATOS (Système de Traitement et d'Analyse Stratégique Orienté Synthèse) est un système multi-agent intelligent dédié à la veille stratégique sur le Maroc. Il collecte automatiquement les actualités nationales et internationales, enrichit le contexte via recherche vectorielle (RAG), intègre les tendances Google, et génère des analyses d'impact structurées.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.1.3-lightgrey)
![LangChain](https://img.shields.io/badge/LangChain-1.2.17-orange)
![LangGraph](https://img.shields.io/badge/LangGraph-1.1.10-yellow)
![Groq](https://img.shields.io/badge/Groq-0.37.1-purple)
![Transformers](https://img.shields.io/badge/Transformers-5.7.0-red)
![Torch](https://img.shields.io/badge/Torch-2.11.0-darkred)
![Scikit‑Learn](https://img.shields.io/badge/Scikit--Learn-1.8.0-green)
![Pandas](https://img.shields.io/badge/Pandas-3.0.2-blue)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-1.41.1-cyan)
![Uvicorn](https://img.shields.io/badge/Uvicorn-0.46.0-black)
![License](https://img.shields.io/badge/License-CC_BY_NC-blue)

## 🚀 Fonctionnalités  
Fonctionnalité	Description  
🤖 5 Agents spécialisés	Collecteur RSS, RAG Vectoriel, Google Trends, Analyste IA  
🔄 Orchestration séquentielle	Workflow clair avec points de contrôle  
👤 Human-in-the-Loop	3 points de validation humaine (collecte, tendances, analyse)  
📚 RAG Agentique	Base vectorielle ChromaDB + embeddings sémantiques  
📈 Google Trends	Intégration des tendances de recherche Maroc  
🎯 Analyse d'impact	Synthèse structurée des impacts sur le Maroc  
🌐 Interface Web	Dashboard temps réel (Flask + HTML/CSS/JS)  

## 📋 Prérequis  
Python : 3.12 ou supérieur  
RAM : 8 Go minimum (16 Go recommandé)  
Stockage : 2 Go disponibles  
Connexion Internet : Requise pour les API (Groq, flux RSS)  
Clé API : Groq (gratuite)  

## ⚙️ Installation  
1. Cloner le projet
2.
```bash
  git clone https://github.com/zoubeiraouchar13-creator/STRATOS
```

```bash
cd STRATOS
```
 
4. Créer un environnement virtuel
```bash  
  python -m venv .venv
```

```bash
.venv\Scripts\activate
```

6. Installer les dépendances
```bash
  pip install -r requirements.txt
```

8. Configurer la clé API Groq  
  Créez un fichier .env à la racine : GROQ_API_KEY=votre_clé_api_groq_ici  
9. Lancer l'application
```bash 
  python app.py
```
  L'application est accessible sur : http://localhost:5002  

## 🎮 Utilisation  
Via l'interface web  
Ouvrez http://localhost:5002  
Sélectionnez :  
Source : International + National / International seul / National seul  
Type d'analyse : Impact international / Synthèse nationale  
Mode : Automatique / Avec validation humaine  
Cliquez sur LANCER LE WORKFLOW  
Consultez les actualités collectées, les tendances et l'analyse générée  
