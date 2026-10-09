"""Local Chrome DevTools MCP bridge for an isolated film-capture browser.

The configured connector cannot attach to the occupied existing Chrome profile.
This helper uses the same installed MCP package against a separate debugging
endpoint; it never closes, reads cookies from, or changes that existing profile.
"""
from pathlib import Path
import json
import os
import queue
import subprocess
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'out' / 'chrome-capture-profile'
PROFILE.mkdir(parents=True, exist_ok=True)
CHROME = Path(os.environ['LOCALAPPDATA']) / 'Google/Chrome/Application/chrome.exe'
MCP = Path(os.environ.get('DRAFTLY_DEVTOOLS_MCP', 'D:/Program Files/dev-caches/npm-cache/_npx/15c61037b1978c83/node_modules/chrome-devtools-mcp/build/src/bin/chrome-devtools-mcp.js'))
HIDDEN = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
browser = subprocess.Popen([
    str(CHROME), '--headless=new', '--remote-debugging-port=9223',
    '--user-data-dir=' + str(PROFILE), '--window-size=1920,1080',
    '--no-first-run', '--no-default-browser-check', '--disable-background-networking',
    'about:blank',
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=HIDDEN)
for _ in range(100):
    try:
        with urllib.request.urlopen('http://127.0.0.1:9223/json/version', timeout=1):
            break
    except Exception:
        time.sleep(.1)
else:
    raise RuntimeError('Isolated Chrome debugging endpoint did not start')

log = (ROOT / 'out' / 'devtools-mcp.log').open('w', encoding='utf8')
server = subprocess.Popen([
    'node', str(MCP), '--browser-url=http://127.0.0.1:9223',
    '--no-usage-statistics',
], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log,
   text=True, encoding='utf8', creationflags=HIDDEN)
responses = {}
condition = threading.Condition()
lock = threading.Lock()
serial = 0

def read_responses():
    for line in server.stdout:
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if 'id' in message:
            with condition:
                responses[message['id']] = message
                condition.notify_all()

threading.Thread(target=read_responses, daemon=True).start()

def rpc(method, params):
    global serial
    with lock:
        serial += 1
        request_id = serial
        server.stdin.write(json.dumps({'jsonrpc':'2.0', 'id':request_id, 'method':method, 'params':params})+'\n')
        server.stdin.flush()
        with condition:
            if not condition.wait_for(lambda: request_id in responses, timeout=180):
                raise TimeoutError('Chrome DevTools MCP request timed out: ' + method)
            message = responses.pop(request_id)
        if 'error' in message:
            raise RuntimeError(str(message['error']))
        return message['result']

rpc('initialize', {'protocolVersion':'2024-11-05', 'capabilities':{}, 'clientInfo':{'name':'draftly-local-film','version':'1.0'}})
server.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n')
server.stdin.flush()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        self.respond({'ready':True,'browserPort':9223,'mcpPid':server.pid,'browserPid':browser.pid})

    def do_POST(self):
        try:
            request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if request.get('method') == 'tools/list':
                result = rpc('tools/list', {})
            else:
                result = rpc('tools/call', {'name':request['name'],'arguments':request.get('arguments',{})})
            self.respond(result)
        except Exception as error:
            self.respond({'error':str(error)}, status=500)

    def respond(self, data, status=200):
        body = json.dumps(data).encode('utf8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

print('Chrome DevTools MCP isolated capture bridge: http://127.0.0.1:9234', flush=True)
try:
    ThreadingHTTPServer(('127.0.0.1', 9234), Handler).serve_forever()
finally:
    server.terminate()
    browser.terminate()
    log.close()
