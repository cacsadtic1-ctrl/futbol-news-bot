# server.py
# Este archivo crea un servidor web mínimo usando Flask.
# Render necesita que tu aplicación escuche en el puerto que él asigna,
# por eso configuramos Flask para usar la variable de entorno PORT.

from flask import Flask        # Importamos Flask, el microframework para crear el servidor web.
import subprocess              # Importamos subprocess para poder ejecutar tu script desde Python.
import os                      # Importamos os para acceder a variables de entorno (ej. PORT).

# Creamos la aplicación Flask
app = Flask(__name__)

# Definimos una ruta principal "/"
@app.route('/')
def run_script():
    # Cada vez que alguien acceda a la URL pública del servicio,
    # Render llamará a esta función.
    # Aquí ejecutamos tu script de noticias con subprocess.
    subprocess.run(["python", "scripts/noticias_virales.py"])
    # Devolvemos un mensaje de confirmación en la página.
    return "✅ Noticias actualizadas y JSON generado"

# Bloque principal: aquí arrancamos el servidor Flask
if __name__ == "__main__":
    # Render asigna el puerto en la variable de entorno PORT.
    # Si no existe (ejecutando localmente), usamos 5000 por defecto.
    port = int(os.environ.get("PORT", 5000))
    # Flask debe escuchar en todas las interfaces ("0.0.0.0") para que Render lo acepte.
    app.run(host="0.0.0.0", port=port)
