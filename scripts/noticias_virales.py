#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
noticias_rss_mejorado.py

Versión mejorada y corregida: obtiene noticias de fútbol solo desde RSS confiables.
Genera un JSON con las 3 más virales según criterios:
 - Keywords virales
 - Difusión entre fuentes
 - Decay temporal
"""

import feedparser
import json
import logging
import math
from datetime import datetime, timezone
import os
from difflib import SequenceMatcher
import re

# ---------------------------
# Configuración
# ---------------------------

RSS_SOURCES = [
    "https://www.goal.com/es/feeds/news",
    "https://as.com/rss/futbol/primera.xml",
    "https://www.mundodeportivo.com/rss/futbol.xml"
    # ESPN se omite porque tu red lo bloquea
]

KEYWORDS = ["messi", "cristiano", "haaland", "champions", "mundial", "real madrid", "barcelona"]

SIMILARITY_THRESHOLD = 0.75
DECAY_LAMBDA = 0.08

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------------------
# Utilidades
# ---------------------------

def normalize_text(s: str) -> str:
    """Normaliza un título para comparación."""
    if not s:
        return ""
    s = s.lower()
    s = (s.replace("á", "a").replace("é", "e").replace("í", "i")
           .replace("ó", "o").replace("ú", "u").replace("ñ", "n"))
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def similar(a: str, b: str, thresh: float = SIMILARITY_THRESHOLD) -> bool:
    """Compara dos strings y devuelve True si son suficientemente similares."""
    return SequenceMatcher(None, a, b).ratio() >= thresh

def decay_hours(published_datetime, lambda_h=DECAY_LAMBDA):
    """Aplica decay temporal según horas transcurridas."""
    if not published_datetime:
        return 0.6
    now = datetime.now(timezone.utc)
    delta = now - published_datetime
    h = delta.total_seconds() / 3600.0
    return math.exp(-lambda_h * h)

# ---------------------------
# Extracción de RSS
# ---------------------------

def obtener_rss():
    """Lee todas las fuentes RSS y devuelve lista de noticias."""
    noticias = []
    for url in RSS_SOURCES:
        try:
            logging.info(f"Consultando RSS: {url}")
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                titulo = entry.get("title", "").strip()
                enlace = entry.get("link", "").strip()
                # Intentar obtener fecha publicada
                published = None
                if hasattr(entry, "published"):
                    try:
                        published = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z")
                        published = published.replace(tzinfo=timezone.utc)
                    except Exception:
                        published = None
                noticias.append({
                    "titulo": titulo,
                    "enlace": enlace,
                    "origen": url,
                    "published": published
                })
        except Exception as e:
            logging.warning(f"Error leyendo RSS {url}: {e}")
    return noticias

# ---------------------------
# Agrupado por similitud
# ---------------------------

def agrupar_noticias(noticias):
    """Agrupa noticias similares para contar difusión entre fuentes."""
    grupos = []
    for n in noticias:
        titulo_norm = normalize_text(n["titulo"])
        placed = False
        for g in grupos:
            if similar(titulo_norm, g["titulo_norm"]):
                g["titulos_raw"].append(n["titulo"])
                g["enlaces"].append(n["enlace"])
                g["fuentes"].append(n["origen"])
                if n.get("published"):
                    g["published_candidates"].append(n["published"])
                placed = True
                break
        if not placed:
            grupos.append({
                "titulo_norm": titulo_norm,
                "titulos_raw": [n["titulo"]],
                "enlaces": [n["enlace"]],
                "fuentes": [n["origen"]],
                "published_candidates": [n.get("published")] if n.get("published") else []
            })
    # Normalizar metadatos
    for g in grupos:
        g["titulo_representativo"] = max(g["titulos_raw"], key=len)
        g["fuentes_unicas"] = list(set(g["fuentes"]))
        g["count_sources"] = len(g["fuentes_unicas"])
        g["published"] = max([d for d in g["published_candidates"] if d], default=None)
    return grupos

# ---------------------------
# Scoring avanzado
# ---------------------------

def calcular_score(grupo):
    """Calcula puntaje de viralidad para un grupo de noticias."""
    score = 1  # base
    titulo_norm = grupo["titulo_norm"]

    # Bonus por keywords
    if any(k in titulo_norm for k in KEYWORDS):
        score += 3

    # Bonus por difusión entre fuentes
    if grupo["count_sources"] > 1:
        score += 2 * (grupo["count_sources"] - 1)

    # Decay temporal
    score *= decay_hours(grupo.get("published"))

    grupo["score"] = score
    return score

# ---------------------------
# Flujo principal
# ---------------------------

def obtener_top3_virales():
    """Obtiene las 3 noticias más virales desde RSS."""
    noticias = obtener_rss()
    grupos = agrupar_noticias(noticias)
    for g in grupos:
        calcular_score(g)
    grupos_sorted = sorted(grupos, key=lambda x: x.get("score", 0), reverse=True)
    top3 = grupos_sorted[:3]
    resultado = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_groups": len(grupos),
        "top3": top3
    }
    os.makedirs("data", exist_ok=True)
    with open("data/top3_rss_mejorado.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    return resultado

# ---------------------------
# Ejecución directa
# ---------------------------

if __name__ == "__main__":
    resultado = obtener_top3_virales()
    print("\n=== TOP 3 NOTICIAS DE FÚTBOL MÁS VIRALES DEL DÍA (RSS Mejorado) ===\n")
    for i, n in enumerate(resultado["top3"], start=1):
        print(f"{i}. {n['titulo_representativo']} (Score: {n['score']:.2f})")
        print(f"   Fuentes: {', '.join(n['fuentes_unicas'])}")
        print(f"   Enlaces: {', '.join(n['enlaces'])}")
        print("-" * 60)
