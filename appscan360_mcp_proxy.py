#!/usr/bin/env python3
import json
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = '127.0.0.1'
PORT = 8765
SSL_CONTEXT = ssl._create_unverified_context()
ALLOWED_HEADERS = 'Content-Type, X-API-KEY, Mcp-Session-Id, Accept, X-AppScan-Upstream'
OLLAMA_ALLOWED_HEADERS = 'Content-Type, Accept, X-Ollama-Upstream'
DEFAULT_TIMEOUT = 30
OLLAMA_STREAM_TIMEOUT = 300


class MCPProxyHandler(BaseHTTPRequestHandler):
    server_version = 'AppScanMCPProxy/1.0'

    def do_OPTIONS(self):
        if self.path == '/mcp':
            self.send_response(204)
            self._write_cors_headers()
            self.end_headers()
            return

        if self.path.startswith('/ollama/'):
            self.send_response(204)
            self._write_ollama_cors_headers()
            self.end_headers()
            return

        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        if self.path != '/ollama/tags':
            self.send_response(404)
            self.end_headers()
            return

        upstream = self.headers.get('X-Ollama-Upstream', '').strip()
        if not upstream:
            self._send_json_error(400, 'Missing X-Ollama-Upstream header', ollama=True)
            return

        target = urllib.parse.urljoin(upstream.rstrip('/') + '/', 'api/tags')
        headers = {
            'Accept': self.headers.get('Accept', 'application/json'),
        }
        self._forward_request('GET', target, headers, None, ollama=True)

    def do_POST(self):
        if self.path != '/mcp':
            if self.path == '/ollama/chat':
                upstream = self.headers.get('X-Ollama-Upstream', '').strip()
                if not upstream:
                    self._send_json_error(400, 'Missing X-Ollama-Upstream header', ollama=True)
                    return

                try:
                    content_length = int(self.headers.get('Content-Length', '0'))
                except ValueError:
                    self._send_json_error(400, 'Invalid Content-Length', ollama=True)
                    return

                body = self.rfile.read(content_length)
                headers = {
                    'Content-Type': self.headers.get('Content-Type', 'application/json'),
                    'Accept': self.headers.get('Accept', 'application/json'),
                }
                target = urllib.parse.urljoin(upstream.rstrip('/') + '/', 'api/chat')
                self._forward_request('POST', target, headers, body, ollama=True)
                return

            self.send_response(404)
            self._write_cors_headers()
            self.end_headers()
            return

        upstream = self.headers.get('X-AppScan-Upstream', '').strip()
        if not upstream:
            self._send_json_error(400, 'Missing X-AppScan-Upstream header')
            return

        try:
            content_length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            self._send_json_error(400, 'Invalid Content-Length')
            return

        body = self.rfile.read(content_length)
        headers = {
            'Content-Type': self.headers.get('Content-Type', 'application/json'),
            'Accept': self.headers.get('Accept', 'application/json, text/event-stream'),
        }

        api_key = self.headers.get('X-API-KEY')
        if api_key:
            headers['X-API-KEY'] = api_key

        session_id = self.headers.get('Mcp-Session-Id')
        if session_id:
            headers['Mcp-Session-Id'] = session_id

        self._forward_request('POST', upstream, headers, body, ollama=False)

    def _forward_request(self, method, url, headers, body, ollama=False):
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        timeout = OLLAMA_STREAM_TIMEOUT if ollama else DEFAULT_TIMEOUT

        try:
            with urllib.request.urlopen(request, context=SSL_CONTEXT, timeout=timeout) as response:
                self.send_response(response.status)
                if ollama:
                    self._write_ollama_cors_headers()
                else:
                    self._write_cors_headers()
                for key, value in response.headers.items():
                    lower = key.lower()
                    if lower in {'content-length', 'connection', 'transfer-encoding'}:
                        continue
                    self.send_header(key, value)
                self.end_headers()

                # Forward Ollama streams incrementally so long generations do not
                # block on buffering the full upstream response.
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except urllib.error.HTTPError as error:
            payload = error.read()
            self.send_response(error.code)
            if ollama:
                self._write_ollama_cors_headers()
            else:
                self._write_cors_headers()
            for key, value in error.headers.items():
                lower = key.lower()
                if lower in {'content-length', 'connection', 'transfer-encoding'}:
                    continue
                self.send_header(key, value)
            self.end_headers()
            if payload:
                self.wfile.write(payload)
        except Exception as error:
            self._send_json_error(502, f'Upstream request failed: {error}', ollama=ollama)

    def log_message(self, fmt, *args):
        sys.stdout.write('%s - - [%s] %s\n' % (self.client_address[0], self.log_date_time_string(), fmt % args))
        sys.stdout.flush()

    def _write_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', ALLOWED_HEADERS)
        self.send_header('Access-Control-Expose-Headers', 'Content-Type, Mcp-Session-Id')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Access-Control-Max-Age', '86400')

    def _write_ollama_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', OLLAMA_ALLOWED_HEADERS)
        self.send_header('Access-Control-Expose-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Access-Control-Max-Age', '86400')

    def _send_json_error(self, status, message, ollama=False):
        body = json.dumps({'error': message}).encode('utf-8')
        self.send_response(status)
        if ollama:
            self._write_ollama_cors_headers()
        else:
            self._write_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


if __name__ == '__main__':
    try:
        httpd = ReusableThreadingHTTPServer((HOST, PORT), MCPProxyHandler)
    except OSError as error:
        if getattr(error, 'errno', None) == 48:
            print(
                f'AppScan MCP relay is already running on http://{HOST}:{PORT}/mcp. '
                'Stop the existing process before starting another instance.',
                flush=True,
            )
            sys.exit(0)
        raise

    print(f'AppScan MCP relay listening on http://{HOST}:{PORT}/mcp', flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down relay', flush=True)
    finally:
        httpd.server_close()
