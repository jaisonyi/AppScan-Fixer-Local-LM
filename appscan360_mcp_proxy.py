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
LLM_ALLOWED_HEADERS = 'Content-Type, Accept, X-LLM-Provider, X-LLM-API-Key'
DEFAULT_TIMEOUT = 30
OLLAMA_STREAM_TIMEOUT = 300
LLM_TIMEOUT = 120

# Hardcoded model lists returned by GET /llm/models?provider=<name>
LLM_MODELS = {
    'openai':  ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'o3-mini', 'o1-mini'],
    'gemini':  ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-pro', 'gemini-1.5-flash'],
    'claude':  ['claude-sonnet-4-5', 'claude-opus-4', 'claude-haiku-3-5', 'claude-3-5-sonnet-20241022'],
    'copilot': ['gpt-4o', 'gpt-4o-mini', 'claude-sonnet-4-5', 'o3-mini'],
}


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
        if self.path.startswith('/llm/'):
            self.send_response(204)
            self._write_llm_cors_headers()
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        if self.path == '/ollama/tags':
            upstream = self.headers.get('X-Ollama-Upstream', '').strip()
            if not upstream:
                self._send_json_error(400, 'Missing X-Ollama-Upstream header', ollama=True)
                return
            target = urllib.parse.urljoin(upstream.rstrip('/') + '/', 'api/tags')
            headers = {'Accept': self.headers.get('Accept', 'application/json')}
            self._forward_request('GET', target, headers, None, ollama=True)
            return

        if self.path.startswith('/llm/models'):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            provider = (qs.get('provider') or [''])[0].strip().lower()
            models = LLM_MODELS.get(provider, [])
            body = json.dumps({'models': models}).encode('utf-8')
            self.send_response(200)
            self._write_llm_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
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

        if self.path == '/llm/chat':
            self._handle_llm_chat()
            return

        if self.path == '/mcp':
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
            return

        self.send_response(404)
        self._write_cors_headers()
        self.end_headers()

    # ── Unified LLM chat handler ──────────────────────────────────────────────
    def _handle_llm_chat(self):
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            self._send_llm_error(400, 'Invalid Content-Length')
            return
        raw_body = self.rfile.read(content_length)
        try:
            req = json.loads(raw_body)
        except Exception:
            self._send_llm_error(400, 'Invalid JSON body')
            return

        provider = self.headers.get('X-LLM-Provider', '').strip().lower()
        api_key  = self.headers.get('X-LLM-API-Key', '').strip()

        if not provider:
            self._send_llm_error(400, 'Missing X-LLM-Provider header')
            return
        if not api_key:
            self._send_llm_error(400, 'Missing X-LLM-API-Key header')
            return

        messages    = req.get('messages', [])
        model       = str(req.get('model', '') or '')
        temperature = float(req.get('temperature', 0.2))
        max_tokens  = int(req.get('max_tokens', 4096))
        json_mode   = bool(req.get('json_mode', False))

        try:
            if provider in ('openai', 'copilot'):
                content = self._call_openai(api_key, model, messages, temperature, max_tokens, json_mode, provider)
            elif provider == 'gemini':
                content = self._call_gemini(api_key, model, messages, temperature, max_tokens, json_mode)
            elif provider == 'claude':
                content = self._call_claude(api_key, model, messages, temperature, max_tokens, json_mode)
            else:
                self._send_llm_error(400, f'Unknown provider: {provider}')
                return
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='replace')
            self._send_llm_error(e.code, f'Provider error ({e.code}): {err_body[:500]}')
            return
        except Exception as e:
            self._send_llm_error(502, f'LLM call failed: {e}')
            return

        resp_body = json.dumps({'message': {'content': content}}).encode('utf-8')
        self.send_response(200)
        self._write_llm_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(resp_body)))
        self.end_headers()
        self.wfile.write(resp_body)

    def _call_openai(self, api_key, model, messages, temperature, max_tokens, json_mode, provider):
        base_url = 'https://api.githubcopilot.com' if provider == 'copilot' else 'https://api.openai.com'
        url = f'{base_url}/v1/chat/completions'
        body = {
            'model': model or 'gpt-4o',
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
        }
        if json_mode:
            body['response_format'] = {'type': 'json_object'}
        req_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
        if provider == 'copilot':
            req_headers['Copilot-Integration-Id'] = 'vscode-chat'
        payload = json.dumps(body).encode('utf-8')
        request = urllib.request.Request(url, data=payload, headers=req_headers, method='POST')
        with urllib.request.urlopen(request, context=SSL_CONTEXT, timeout=LLM_TIMEOUT) as resp:
            data = json.loads(resp.read())
        return data['choices'][0]['message']['content']

    def _call_gemini(self, api_key, model, messages, temperature, max_tokens, json_mode):
        model_id = model or 'gemini-2.0-flash'
        url = (f'https://generativelanguage.googleapis.com/v1beta/models/'
               f'{model_id}:generateContent?key={api_key}')
        system_parts = []
        contents = []
        for msg in messages:
            role = str(msg.get('role', 'user'))
            text = str(msg.get('content', ''))
            if role == 'system':
                system_parts.append({'text': text})
            else:
                gemini_role = 'user' if role == 'user' else 'model'
                contents.append({'role': gemini_role, 'parts': [{'text': text}]})
        if not contents:
            contents = [{'role': 'user', 'parts': [{'text': ''}]}]
        body = {
            'contents': contents,
            'generationConfig': {
                'temperature': temperature,
                'maxOutputTokens': max_tokens,
            },
        }
        if system_parts:
            body['system_instruction'] = {'parts': system_parts}
        if json_mode:
            body['generationConfig']['responseMimeType'] = 'application/json'
        payload = json.dumps(body).encode('utf-8')
        req_headers = {'Content-Type': 'application/json'}
        request = urllib.request.Request(url, data=payload, headers=req_headers, method='POST')
        with urllib.request.urlopen(request, context=SSL_CONTEXT, timeout=LLM_TIMEOUT) as resp:
            data = json.loads(resp.read())
        return data['candidates'][0]['content']['parts'][0]['text']

    def _call_claude(self, api_key, model, messages, temperature, max_tokens, json_mode):
        url = 'https://api.anthropic.com/v1/messages'
        system_content = ''
        user_messages = []
        for msg in messages:
            role = str(msg.get('role', 'user'))
            if role == 'system':
                system_content = str(msg.get('content', ''))
            else:
                user_messages.append(msg)
        if not user_messages:
            user_messages = [{'role': 'user', 'content': ''}]
        if json_mode and user_messages:
            last = dict(user_messages[-1])
            last['content'] = str(last.get('content', '')) + \
                '\n\nRespond with ONLY a valid JSON object — no prose, no code fences.'
            user_messages = user_messages[:-1] + [last]
        body = {
            'model': model or 'claude-sonnet-4-5',
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': user_messages,
        }
        if system_content:
            body['system'] = system_content
        req_headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
        }
        payload = json.dumps(body).encode('utf-8')
        request = urllib.request.Request(url, data=payload, headers=req_headers, method='POST')
        with urllib.request.urlopen(request, context=SSL_CONTEXT, timeout=LLM_TIMEOUT) as resp:
            data = json.loads(resp.read())
        return data['content'][0]['text']

    # ── HTTP forwarding (Ollama / MCP) ────────────────────────────────────────
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

    def _write_llm_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', LLM_ALLOWED_HEADERS)
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

    def _send_llm_error(self, status, message):
        body = json.dumps({'error': message}).encode('utf-8')
        self.send_response(status)
        self._write_llm_cors_headers()
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
    print(f'  MCP endpoint  : http://{HOST}:{PORT}/mcp', flush=True)
    print(f'  Ollama relay  : http://{HOST}:{PORT}/ollama/chat', flush=True)
    print(f'  LLM relay     : http://{HOST}:{PORT}/llm/chat  (OpenAI / Gemini / Claude / Copilot)', flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down relay', flush=True)
    finally:
        httpd.server_close()
