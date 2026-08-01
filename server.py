# server.py
# Este archivo convierte tu script en un servicio web mínimo
# para que Render lo acepte en el plan gratuito.

from flask import Flask
import subprocess

# Creamos la aplicación Flask
app = Flask(__name__)

# Definimos una ruta principal "/"
@app.route('/')
def run_script():
    # Ejecuta tu script de noticias
    subprocess.run(["python", "scripts/noticias_virales.py"])
    return "✅ Noticias actualizadas y JSON generado"
