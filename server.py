from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os

BASE = Path("C:/Dienstplan")

os.chdir(BASE)

server = ThreadingHTTPServer(("0.0.0.0", 8080), SimpleHTTPRequestHandler)
print("Kalender-Server läuft auf http://localhost:8080")
server.serve_forever()
