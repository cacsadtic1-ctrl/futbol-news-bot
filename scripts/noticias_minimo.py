#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
noticias_minimo.py

Versión mínima: solo lee un RSS (AS.com) y genera un JSON con las noticias.
"""

import feedparser
import json
import logging
from datetime import datetime, timezone
import os

# Configuración de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Fuente RSS de prueba
RSS_URL = "https://as.com/rss/futbol/primera.xml"

def obtener_rss():
    """Lee el RSS de AS y devuelve lista de noticias."""
    noticias = []
    try:
        logging.info(f"Consultando RSS: {RSS_URL}")
        feed = feedparser.parse(RSS_URL)
        for entry in feed.entries[:10]:
            titulo = entry.get("title", "").strip()
            enlace = entry.get("link", "").strip()
            noticias.append({"titulo": titulo, "enlace": enlace})
    except Exception as e:
        logging.warning(f"Error leyendo RSS {RSS_URL}: {e}")
    return noticias

def generar_json():
    """Genera un JSON con las noticias obtenidas."""
    noticias = obtener_rss()
    resultado = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_noticias": len(noticias),
        "noticias": noticias
    }
    os.makedirs("data", exist_ok=True)
    with open("data/rss_as.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    return resultado

if __name__ == "__main__":
    resultado = generar_json()
    print("\n=== Noticias obtenidas del RSS de AS ===\n")
    for i, n in enumerate(resultado["noticias"], start=1):
        print(f"{i}. {n['titulo']}")
        print(f"   Enlace: {n['enlace']}")
        print("-" * 60)
