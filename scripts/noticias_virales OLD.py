#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
noticias_virales.py

Script para obtener las 3 noticias de fútbol más virales del día.
Incluye:
 - Lectura de múltiples RSS
 - Scraping de MARCA, ESPN, AS y Mundo Deportivo
 - Agrupado y desduplicación de titulares
 - Sistema de puntaje de viralidad con keywords, difusión, confianza de fuente y decay temporal
"""

import requests
from bs4 import BeautifulSoup
import feedparser
import json
import logging
import math
from datetime import datetime, timezone
from difflib import SequenceMatcher
import re
import os

# ---------------------------
# Configuración general
# ---------------------------

RSS_SOURCES = [
    "https://www.espn.com/espn/rss/soccer/news",
    "https://www.goal.com/es/feeds/news",
    "https://as.com/rss/futbol/primera.xml",
    "https://www.mundodeportivo.com/rss/futbol.xml"
]

MARCA_URL = "https://www.marca.com/futbol.html"
ESPN_URL = "https://www.espn.com/soccer/"
AS_URL = "https://as.com/futbol/"
MD_URL = "https://www.mundodeportivo.com/futbol"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/127.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.google.com/"
}

KEYWORDS = ["messi", "cristiano", "haaland", "champions", "mundial", "real madrid", "barcelona"]

ORIGEN_PESOS = {
    "marca_mostread": 5,
    "espn_trending": 4,
    "rss": 1,
    "as_top": 4,
    "md_top": 4
}

FUENTE_CONF = {
    "marca_mostread": 1.0,
    "espn_trending": 0.95,
    "rss": 0.8,
    "as_top": 0.9,
    "md_top": 0.9
}

DECAY_LAMBDA = 0.08
SIMILARITY_THRESHOLD = 0.72

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------------------
# Funciones utilitarias
# ---------------------------

def normalize_text(s: str) -> str:
    """Normaliza un título para comparación: minúsculas, sin acentos ni signos."""
    if not s:
        return ""
    s = s.lower()
    s = (s.replace("á", "a").replace("é", "e").replace("í", "i")
           .replace("ó", "o").replace("ú", "u").replace("ñ", "n"))
    s = re.sub(r"http\S+", "", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def similar(a: str, b: str, thresh: float = SIMILARITY_THRESHOLD) -> bool:
    """Compara dos strings y devuelve True si son suficientemente similares."""
    if not a or not b:
        return False
    return SequenceMatcher(None, a, b).ratio() >= thresh

def hours_since(dt: datetime) -> float:
    """Devuelve horas transcurridas desde dt hasta ahora."""
    if not dt:
        return 9999.0
    now = datetime.now(timezone.utc)
    delta = now - dt
    return delta.total_seconds() / 3600.0

def decay_hours(published_datetime: datetime, lambda_h: float = DECAY_LAMBDA) -> float:
    """Aplica decay exponencial según las horas transcurridas desde publicación."""
    h = hours_since(published_datetime)
    return math.exp(-lambda_h * h)

# ---------------------------
# Extracción de noticias
# ---------------------------

# (Funciones obtener_rss, obtener_marca_mas_leido, obtener_espn_trending,
#  obtener_as_top, obtener_md_top — mismas que ya te mostré, con cabeceras y fallbacks)

# ---------------------------
# Agrupado y scoring
# ---------------------------

def agrupar_noticias(noticias):
    """Agrupa noticias similares para contar apariciones en múltiples fuentes."""
    grupos = []
    for n in noticias:
        titulo_norm = normalize_text(n["titulo"])
        placed = False
        for g in grupos:
            if similar(titulo_norm, g["titulo_norm"]):
                g["titulos_raw"].append(n["titulo"])
                g["enlaces"].append(n["enlace"])
                g["fuentes"].append(n["origen"])
                placed = True
                break
        if not placed:
            grupos.append({
                "titulo_norm": titulo_norm,
                "titulos_raw": [n["titulo"]],
                "enlaces": [n["enlace"]],
                "fuentes": [n["origen"]],
                "published": n.get("published")
            })
    for g in grupos:
        g["titulo_representativo"] = max(g["titulos_raw"], key=len)
        g["fuentes_unicas"] = list(set(g["fuentes"]))
        g["count_sources"] = len(g["fuentes_unicas"])
    return grupos

def calcular_score(grupo):
    """Calcula el puntaje de viralidad para un grupo de noticias."""
    base_editorial = sum(ORIGEN_PESOS.get(f, 1) for f in grupo["fuentes_unicas"])
    kw_bonus = 2 if any(k in grupo["titulo_norm"] for k in KEYWORDS) else 0
    diffusion_bonus = 3 * max(0, grupo["count_sources"] - 1)
    factor_fuente = sum(FUENTE_CONF.get(f, 0.8) for f in grupo["fuentes_unicas"]) / grupo["count_sources"]
    decay = decay_hours(grupo.get("published")) if grupo.get("published") else 0.6
    score_final = (base_editorial + kw_bonus + diffusion_bonus) * factor_fuente * decay
    grupo["score"] = score_final
    return score_final

# ---------------------------
# Flujo principal
# ---------------------------

def obtener_top3_virales():
    """Orquesta la extracción, agrupado, scoring y devuelve las 3 noticias más virales."""
    noticias = []
    noticias.extend(obtener_rss())
    noticias.extend(obtener_marca_mas_leido())
    noticias.extend(obtener_espn_trending())
    noticias.extend(obtener_as_top())
    noticias.extend(obtener_md_top())

    logging.info(f"Noticias extraídas: {len(noticias)}")

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
    with open("data/top3.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    return resultado

# ---------------------------
# Ejecución directa
# ---------------------------

if __name__ == "__main__":
    resultado = obtener_top3_virales()
    print("\n=== TOP 3 NOTICIAS DE FÚTBOL MÁS VIRALES DEL DÍA ===\n")
    for i, n in enumerate(resultado["top3"], start=1):
        print(f"{i}. {n['titulo_representativo']} (Score: {n['score']:.2f})")
        print(f"   Fuentes: {', '.join(n['fuentes_unicas'])}")
        print(f"   Enlaces: {', '.join(n['enlaces'])}")
        print("-" * 60)
