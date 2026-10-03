"""Simple task list web app using only the Python standard library."""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("APP_HOST", "0.0.0.0")
PORT = int(os.environ.get("APP_PORT", "8080"))
APP_NAME = os.environ.get("APP_NAME", "Simple Task App")
MAX_TITLE_LENGTH = 200
MAX_BODY_BYTES = 10_000

_tasks = {}
_next_id = 1
_lock = threading.Lock()

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name}</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 560px; margin: 40px auto; padding: 0 16px; }}
  form {{ display: flex; gap: 8px; }}
  form input {{ flex: 1; padding: 8px; }}
  button {{ padding: 8px 12px; cursor: pointer; }}
  li {{ display: flex; align-items: center; gap: 8px; padding: 6px 0; }}
  li span {{ flex: 1; }}
  li.done span {{ text-decoration: line-through; color: #888; }}
</style>
</head>
<body>
<h1>{name}</h1>
<form id="add">
  <input id="title" placeholder="New task" maxlength="{maxlen}" required>
  <button type="submit">Add</button>
</form>
<ul id="list"></ul>
<script>
const list = document.getElementById('list');
const json = (method, body) => ({{method, headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(body)}});

async function load() {{
  const tasks = await (await fetch('/api/tasks')).json();
  list.innerHTML = '';
  for (const t of tasks) {{
    const li = document.createElement('li');
    if (t.done) li.className = 'done';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = t.done;
    cb.onchange = () => fetch('/api/tasks/' + t.id, json('PATCH', {{done: cb.checked}})).then(load);
    const span = document.createElement('span');
    span.textContent = t.title;
    const del = document.createElement('button');
    del.textContent = 'Delete';
    del.onclick = () => fetch('/api/tasks/' + t.id, {{method: 'DELETE'}}).then(load);
    li.append(cb, span, del);
    list.append(li);
  }}
}}

document.getElementById('add').onsubmit = async (e) => {{
  e.preventDefault();
  const input = document.getElementById('title');
  await fetch('/api/tasks', json('POST', {{title: input.value}}));
  input.value = '';
  load();
}};

load();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "SimpleTaskApp"

    def _send(self, status, body=None, content_type="application/json"):
        if body is None:
            data = b""
        elif isinstance(body, str):
            data = body.encode()
        else:
            data = json.dumps(body).encode()
        self.send_response(status)
        if data:
            self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            return None
        if length <= 0 or length > MAX_BODY_BYTES:
            return None
        try:
            return json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            return None

    def _task_id(self):
        parts = self.path.rstrip("/").split("/")
        if len(parts) == 4 and parts[:3] == ["", "api", "tasks"] and parts[3].isdigit():
            return int(parts[3])
        return None

    def do_GET(self):
        if self.path == "/":
            html = INDEX_HTML.format(name=APP_NAME, maxlen=MAX_TITLE_LENGTH)
            self._send(200, html, "text/html; charset=utf-8")
        elif self.path == "/healthz":
            self._send(200, {"status": "ok"})
        elif self.path == "/api/tasks":
            with _lock:
                tasks = list(_tasks.values())
            self._send(200, tasks)
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        global _next_id
        if self.path != "/api/tasks":
            return self._send(404, {"error": "not found"})
        body = self._read_json()
        title = body.get("title") if isinstance(body, dict) else None
        title = title.strip() if isinstance(title, str) else ""
        if not title or len(title) > MAX_TITLE_LENGTH:
            return self._send(400, {"error": f"title must be 1-{MAX_TITLE_LENGTH} characters"})
        with _lock:
            task = {"id": _next_id, "title": title, "done": False}
            _tasks[_next_id] = task
            _next_id += 1
        self._send(201, task)

    def do_PATCH(self):
        task_id = self._task_id()
        body = self._read_json()
        if task_id is None or not isinstance(body, dict) or not isinstance(body.get("done"), bool):
            return self._send(400, {"error": "invalid request"})
        with _lock:
            task = _tasks.get(task_id)
            if task is not None:
                task["done"] = body["done"]
                task = dict(task)
        if task is None:
            return self._send(404, {"error": "not found"})
        self._send(200, task)

    def do_DELETE(self):
        task_id = self._task_id()
        with _lock:
            removed = task_id is not None and _tasks.pop(task_id, None) is not None
        if not removed:
            return self._send(404, {"error": "not found"})
        self._send(204)


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"{APP_NAME} listening on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
