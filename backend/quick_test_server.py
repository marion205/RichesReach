#!/usr/bin/env python3
"""
Quick Test Server for RichesReach
Simple HTTP server to test mobile app connectivity
"""

import http.server
import socketserver
import json
from urllib.parse import urlparse, parse_qs

class GraphQLHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/graphql/':
            # Simulate GraphQL response
            response_data = {
                "data": {
                    "tokenAuth": {
                        "token": "test-token-123",
                        "user": {
                            "id": "1",
                            "username": "testuser",
                            "email": "test@example.com"
                        }
                    }
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

if __name__ == "__main__":
    PORT = 8000
    with socketserver.TCPServer(("0.0.0.0", PORT), GraphQLHandler) as httpd:
        print(f"🚀 Quick Test Server running on http://0.0.0.0:{PORT}")
        print(f"📱 Mobile app should connect to: http://192.168.1.151:{PORT}/graphql/")
        print("Press Ctrl+C to stop")
        httpd.serve_forever()
