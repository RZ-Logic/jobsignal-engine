#!/usr/bin/env python3
"""
cv_service.py — Lightweight HTTP service for CV rendering
Runs inside a Docker sidecar, called by n8n via HTTP Request node.

POST /render
  Body: { "markdown": "...", "filename": "cv_mistral_123" }
  Returns: { "status": "ok", "filename": "cv_mistral_123.docx", "docx_base64": "..." }

GET /health
  Returns: { "status": "ok" }
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import base64
import os
import sys

sys.path.insert(0, '/opt/jobsignal')
from render_cv import parse_markdown, build_docx


class CVHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self._respond(200, {'status': 'ok'})
        else:
            self._respond(404, {'error': 'not found'})

    def do_POST(self):
        if self.path == '/render':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length))

                markdown = body.get('markdown', '')
                filename = body.get('filename', 'cv_output')

                if not markdown or len(markdown) < 50:
                    self._respond(400, {'error': 'markdown too short or missing'})
                    return

                lines = parse_markdown(markdown)
                tmp_path = f'/tmp/{filename}.docx'
                build_docx(lines, tmp_path)

                with open(tmp_path, 'rb') as f:
                    docx_bytes = f.read()
                docx_base64 = base64.b64encode(docx_bytes).decode('utf-8')

                os.remove(tmp_path)

                self._respond(200, {
                    'status': 'ok',
                    'filename': f'{filename}.docx',
                    'docx_base64': docx_base64
                })
            except Exception as e:
                self._respond(500, {'error': str(e)})
        else:
            self._respond(404, {'error': 'not found'})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        if args and '500' in str(args):
            super().log_message(format, *args)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3456))
    server = HTTPServer(('0.0.0.0', port), CVHandler)
    print(f'CV render service running on port {port}')
    server.serve_forever()
