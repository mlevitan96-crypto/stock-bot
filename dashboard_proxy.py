#!/usr/bin/env python3
"""
Dashboard Reverse Proxy
=======================
Routes traffic from port 5000 to the active A/B instance.
Always accessible on port 5000, regardless of which instance is active.
"""

import os
import json
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import requests
from threading import Thread

BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "state" / "deployment_state.json"
PORT_A = 5000
PORT_B = 5001
PROXY_PORT = 5000

def get_active_port() -> int:
    """Get the port of the currently active instance."""
    try:
        if STATE_FILE.exists():
            state = json.loads(STATE_FILE.read_text())
            active = state.get("active_instance", "A")
            return PORT_B if active == "B" else PORT_A
    except:
        pass
    return PORT_A  # Default to A

class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP request handler that proxies to active instance."""
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def do_GET(self):
        """Handle GET requests."""
        self._proxy_request()
    
    def do_POST(self):
        """Handle POST requests."""
        self._proxy_request()
    
    def do_PUT(self):
        """Handle PUT requests."""
        self._proxy_request()
    
    def do_DELETE(self):
        """Handle DELETE requests."""
        self._proxy_request()
    
    def _proxy_request(self):
        """Proxy request to active instance."""
        try:
            # Get active instance port
            target_port = get_active_port()
            target_url = f"http://localhost:{target_port}{self.path}"
            
            # Get request body if present
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Forward headers (exclude hop-by-hop headers)
            headers = {}
            for key, value in self.headers.items():
                if key.lower() not in ['host', 'connection', 'transfer-encoding']:
                    headers[key] = value
            
            # Make request to target
            method = self.command
            if body:
                response = requests.request(method, target_url, headers=headers, data=body, timeout=10)
            else:
                response = requests.request(method, target_url, headers=headers, timeout=10)
            
            # Send response back to client
            self.send_response(response.status_code)
            
            # Forward response headers
            for key, value in response.headers.items():
                if key.lower() not in ['connection', 'transfer-encoding', 'content-encoding']:
                    self.send_header(key, value)
            
            self.end_headers()
            self.wfile.write(response.content)
            
        except Exception as e:
            self.send_error(502, f"Proxy error: {str(e)}")
    
    def do_HEAD(self):
        """Handle HEAD requests."""
        self._proxy_request()

def run_proxy():
    """Run the proxy server."""
    server = HTTPServer(('0.0.0.0', PROXY_PORT), ProxyHandler)
    print(f"[PROXY] Dashboard proxy running on port {PROXY_PORT}")
    print(f"[PROXY] Routing to active instance (checking every request)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[PROXY] Shutting down proxy...")
        server.shutdown()

if __name__ == "__main__":
    run_proxy()
