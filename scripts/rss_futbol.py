import feedparser

# URL de un feed RSS de fútbol
rss_url = "https://www.espn.com/espn/rss/soccer/news"

# Leer el feed
feed = feedparser.parse(rss_url)

# Mostrar los 3 titulares más recientes
for entry in feed.entries[:3]:
    print("Título:", entry.title)
    print("Enlace:", entry.link)
    print()
