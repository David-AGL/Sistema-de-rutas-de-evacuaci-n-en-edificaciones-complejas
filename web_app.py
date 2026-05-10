"""
web_app.py

Punto de entrada de la interfaz web del sistema de evacuación.
Ejecutar desde el directorio raíz del proyecto:

    python3 web_app.py

Luego abrir en el navegador: http://localhost:5000
"""

from interface.web import app

if __name__ == '__main__':
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║    SISTEMA DE RUTAS DE EVACUACIÓN — Interfaz Web    ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    print("  Servidor en:  http://localhost:5000")
    print("  Detener con:  Ctrl+C")
    print()
    app.run(debug=False, port=5000)
