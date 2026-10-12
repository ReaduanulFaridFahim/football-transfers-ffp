"""
Local Web Server for Football Transfer & FFP Dashboard
======================================================
Serves the TransferFairPlay.AI dashboard on port 8080 (or auto-assigned free port).
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8080
DIRECTORY = Path(__file__).resolve().parent

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

def run_server(port=PORT):
    # Enable address reuse
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("127.0.0.1", port), CustomHandler) as httpd:
            url = f"http://localhost:{port}/index.html"
            print(f"============================================================")
            print(f"  Football Transfer Intelligence Dashboard running at:")
            print(f"  {url}")
            print(f"============================================================")
            print("Press Ctrl+C to stop the server.")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nServer stopped.")
    except OSError as e:
        if port < 8090:
            print(f"Port {port} in use, trying {port+1}...")
            run_server(port + 1)
        else:
            raise e

if __name__ == "__main__":
    run_server()
