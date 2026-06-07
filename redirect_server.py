#!/usr/bin/env python3
"""
Redirect server for La Ciudad de los Sentidos
/b/N  ->  t.me/LaCiudad_PostBot?start=gN
Port: 8080
"""
import ast
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_USERNAME = "LaCiudad_PostBot"
PORT = 8080

# Маршруты /b/N -> gN (до 15 групп)
REDIRECT_MAP = {f"/b/{i}": f"https://t.me/{BOT_USERNAME}?start=g{i}" for i in range(1, 16)}


class RedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        target = REDIRECT_MAP.get(self.path)
        if target:
            self.send_response(302)
            self.send_header("Location", target)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Not found")

    def log_message(self, fmt, *args):
        # Пишем в stdout -> systemd journal
        sys.stdout.write(f"{self.address_string()} - {fmt % args}\n")
        sys.stdout.flush()


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), RedirectHandler)
    sys.stdout.write(f"Redirect server started on port {PORT}\n")
    sys.stdout.flush()
    server.serve_forever()
