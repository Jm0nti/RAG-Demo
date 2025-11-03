import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse as urlparse
import logging

HOST = '127.0.0.1'
PORT = 8000

logger = logging.getLogger(__name__)

# Import required components; fail fast if unavailable
try:
    from Architecture.Retriever import RetrieveFAISS
    from Architecture.Generator import Bot, RAGBot
except Exception as e:
    raise RuntimeError(f"Failed to import Retriever/Generator components: {e}")

# Instantiate components (will raise if dependencies or API keys are missing)
retriever = RetrieveFAISS()
bot = Bot()
rag_bot = RAGBot()


class SimpleHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse.urlparse(self.path)
        # Provide a simple health/root endpoint to avoid 501 when browsers
        # request / or /favicon.ico.
        if parsed.path == '/' or parsed.path == '/index.html':
            body = b'<html><body><h2>RAG Demo server</h2><p>POST to /api/chat with JSON {"query":"...","useRag": true|false}</p></body></html>'
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Some clients request /favicon.ico; respond with 204 No Content
        if parsed.path == '/favicon.ico':
            self.send_response(204)
            self._send_cors_headers()
            self.end_headers()
            return

    def do_POST(self):
        parsed = urlparse.urlparse(self.path)
        if parsed.path != '/api/chat':
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b'Not Found')
            return

        content_length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b'{}'
        try:
            payload = json.loads(raw.decode('utf-8'))
        except Exception:
            self.send_response(400)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b'Invalid JSON')
            return

        query = payload.get('query', '')
        use_rag = bool(payload.get('useRag', False))

        if not query:
            self.send_response(400)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b'Missing query')
            return

        try:
            if use_rag:
                docs = retriever.ask(query)
                reply = rag_bot.ask_with_docs(query, docs)
                used_rag = True
                context = docs
            else:
                reply = bot.ask(query)
                used_rag = False
                context = []

            response = {'reply': reply, 'usedRag': used_rag, 'context': context}
            body = json.dumps(response).encode('utf-8')

            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            logger.exception('Error handling /api/chat: %s', e)
            self.send_response(500)
            self._send_cors_headers()
            self.end_headers()
            error_body = json.dumps({'error': str(e)}).encode('utf-8')
            self.wfile.write(error_body)


if __name__ == '__main__':
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, SimpleHandler)
    print(f"Starting server at http://{HOST}:{PORT} - POST /api/chat")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nStopping server')
        httpd.server_close()
