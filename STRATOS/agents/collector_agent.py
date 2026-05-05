from .base_agent import BaseAgent
from typing import Dict, Any
import requests
import xml.etree.ElementTree as ET
import re
import time
from datetime import datetime

class CollectorAgent(BaseAgent):
    """Agent responsable de la collecte des flux RSS"""
    
    def __init__(self):
        super().__init__(
            name="CollectorAgent",
            role="Collecte des actualités internationales et nationales"
        )
        
        # Sources internationales
        self.international_sources = [
            {"url": "http://feeds.bbci.co.uk/news/world/rss.xml", "source": "BBC World"},
            {"url": "http://rss.cnn.com/rss/edition_world.rss", "source": "CNN International"},
            {"url": "https://www.aljazeera.com/xml/rss/all.xml", "source": "Al Jazeera"},
            {"url": "https://www.france24.com/fr/france/rss", "source": "France 24"},
            {"url": "https://www.lemonde.fr/international/rss_full.xml", "source": "Le Monde"},
            {"url": "https://www.economist.com/international/rss.xml", "source": "The Economist"},
        ]
        
        # Sources nationales marocaines
        self.national_sources = [
            {"url": "https://www.medias24.com/feed", "source": "Médias24", "category": "Économie"},
            {"url": "https://telquel.ma/feed", "source": "TelQuel", "category": "Général"},
            {"url": "https://www.le360.ma/feed", "source": "Le360", "category": "Général"},
            {"url": "https://lematin.ma/feed", "source": "Le Matin", "category": "Général"},
            {"url": "https://www.leconomiste.com/feed", "source": "L'Économiste", "category": "Économie"},
            {"url": "https://www.mapnews.ma/fr/feed", "source": "MAP", "category": "Officiel"},
        ]
        
        self.keywords = [
    # Pays et régions stratégiques
    "maroc", "morocco", "maghreb", "afrique", "africa",
    "algérie", "algeria", "tunisie", "tunisia", "libye", "libya", "mauritanie", "mauritania",
    "usa", "états-unis", "united states", "russie", "russia", "chine", "china",
    "ukraine", "france", "espagne", "spain", "portugal",
    "israel", "palestine", "iran", "turquie", "turkey", "saoudite", "saudi",
    "émirats", "uae", "qatar", "egypte", "egypt",
    "germany", "allemagne", "uk", "royaume-uni", "italy", "italie",
    "japon", "japan", "corée", "korea", "inde", "india",
    
    # Thèmes géopolitiques
    "sahara", "western sahara", "tindouf", "polisario",
    "otan", "nato", "union européenne", "eu", "onu", "un",
    "gazoduc", "gaz", "pétrole", "oil", "gas", "énergie", "energy",
    "commerce", "trade", "investissement", "investment",
    "défense", "defense", "militaire", "military", "armée", "army",
    "diplomatie", "diplomacy", "accord", "agreement",
    "terrorisme", "terrorism", "sécurité", "security",
    
    # Économie et commerce
    "économie", "economy", "marchés", "markets", "bourse",
    "phosphates", "automobile", "aéronautique", "aerospace",
    "tourisme", "tourism", "agriculture",
    
    # Relations internationales
    "sommet", "summit", "conférence", "conference",
    "ambassade", "embassy", "visite", "visit",
    "sanctions", "guerre", "war", "conflit", "conflict",
    "alliance", "partenariat", "partnership"
]
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute la collecte"""
        start_time = time.time()
        
        source_type = context.get("source_type", "both")  # both, international, national
        
        articles = []
        if source_type in ["both", "international"]:
            articles.extend(self._fetch_international())
        if source_type in ["both", "national"]:
            articles.extend(self._fetch_national())
        
        # Trier par date
        articles.sort(key=lambda x: x.get("ts", 0), reverse=True)
        
        result = {
            "articles": articles[:50],
            "count": len(articles),
            "source_type": source_type,
            "timestamp": datetime.now().isoformat()
        }
        
        self.log_execution(context, result, time.time() - start_time)
        return result
    
    def _fetch_international(self):
        """Collecte les actualités internationales"""
        articles = []
        for feed in self.international_sources:
            try:
                r = requests.get(feed["url"], timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200:
                    entries = self._parse_rss(r.text)
                    for entry in entries[:10]:
                        text = (entry.get('title', '') + ' ' + entry.get('summary', '')).lower()
                        if any(kw in text for kw in self.keywords):
                            articles.append({
                                "title": entry.get('title', ''),
                                "summary": entry.get('summary', '')[:300],
                                "source": feed["source"],
                                "type": "international",
                                "link": entry.get('link', '#'),
                                "ts": self._parse_date(entry.get('pubDate', '')),
                                "time_str": datetime.now().strftime("%d/%m/%Y %H:%M")
                            })
            except Exception as e:
                self.logger.error(f"Erreur {feed['source']}: {e}")
        return articles
    
    def _fetch_national(self):
        """Collecte les actualités nationales marocaines"""
        articles = []
        for feed in self.national_sources:
            try:
                r = requests.get(feed["url"], timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200:
                    entries = self._parse_rss(r.text)
                    for entry in entries[:15]:
                        articles.append({
                            "title": entry.get('title', ''),
                            "summary": entry.get('summary', '')[:300],
                            "source": feed["source"],
                            "category": feed.get("category", "Général"),
                            "type": "national",
                            "link": entry.get('link', '#'),
                            "ts": self._parse_date(entry.get('pubDate', '')),
                            "time_str": datetime.now().strftime("%d/%m/%Y %H:%M")
                        })
            except Exception as e:
                self.logger.error(f"Erreur {feed['source']}: {e}")
        return articles
    
    def _parse_rss(self, xml_text):
        """Parse RSS feed"""
        entries = []
        try:
            root = ET.fromstring(xml_text)
            for item in root.findall('.//item'):
                entries.append({
                    'title': (item.findtext('title') or '').strip(),
                    'link': (item.findtext('link') or '#').strip(),
                    'summary': item.findtext('description') or '',
                    'pubDate': item.findtext('pubDate') or '',
                })
        except:
            pass
        return entries
    
    def _parse_date(self, date_str):
        """Parse la date"""
        try:
            from email.utils import parsedate_to_datetime
            return int(parsedate_to_datetime(date_str).timestamp())
        except:
            return int(time.time())