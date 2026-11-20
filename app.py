"""Compatibilidad con el punto de entrada WSGI."""
from interfaz import app

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
