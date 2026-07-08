"""SID Browser-based File Explorer - Lightweight HTTP file browser.
Opens a minimal HTTP server on localhost for visual file browsing via browser."""
import os
import json
import time
import threading
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, List, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from functools import partial

class FileBrowserHandler(BaseHTTPRequestHandler):
    """HTTP request handler for file browser."""

    def __init__(self, *args, **kwargs):
        self.root = kwargs.pop('root', Path.home())
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        pass  # Suppress HTTP log output

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_html(self, html, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(html.encode())

    def _send_file(self, path: Path):
        try:
            data = path.read_bytes()
            self.send_response(200)
            # Determine content type
            ext = path.suffix.lower()
            mime_map = {
                '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
                '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.gif': 'image/gif', '.svg': 'image/svg+xml', '.pdf': 'application/pdf',
                '.txt': 'text/plain', '.md': 'text/markdown', '.json': 'application/json',
                '.mp3': 'audio/mpeg', '.mp4': 'video/mp4', '.webm': 'video/webm',
                '.zip': 'application/zip', '.tar': 'application/x-tar', '.gz': 'application/gzip',
            }
            self.send_header('Content-Type', mime_map.get(ext, 'application/octet-stream'))
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == '/':
            self._serve_interface()
        elif path == '/api/list':
            self._api_list(query.get('dir', [str(self.root)])[0])
        elif path == '/api/search':
            self._api_search(query.get('q', [''])[0], query.get('dir', [str(self.root)])[0])
        elif path == '/api/info':
            self._api_info(query.get('path', [''])[0])
        elif path.startswith('/raw/'):
            file_path = Path(path[5:])
            if file_path.exists():
                self._send_file(file_path)
            else:
                self._send_json({"error": "Not found"}, 404)
        else:
            # Try to serve file
            file_path = Path(path.lstrip('/'))
            if file_path.exists():
                self._send_file(file_path)
            else:
                self._send_json({"error": "Not found"}, 404)

    def _api_list(self, dir_path: str):
        p = Path(dir_path).expanduser()
        if not p.exists() or not p.is_dir():
            self._send_json({"error": "Directory not found", "path": dir_path}, 404)
            return

        try:
            items = []
            for entry in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    stat = entry.stat()
                    items.append({
                        "name": entry.name,
                        "path": str(entry),
                        "type": "dir" if entry.is_dir() else "file",
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "permissions": oct(stat.st_mode)[-3:],
                        "ext": entry.suffix.lower(),
                    })
except Exception:
                    pass

            self._send_json({
                "path": str(p),
                "parent": str(p.parent) if str(p) != '/' else None,
                "items": items,
                "total": len(items),
                "disk_usage": self._get_disk_usage(p)
            })
        except PermissionError:
            self._send_json({"error": "Permission denied"}, 403)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _api_search(self, query: str, dir_path: str):
        if not query:
            self._send_json({"results": []})
            return

        try:
            results = []
            import subprocess
            cmd = ['find', dir_path, '-iname', f'*{query}*', '-maxdepth', '5']
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            for line in proc.stdout.strip().split('\n'):
                if line:
                    p = Path(line)
                    try:
                        stat = p.stat()
                        results.append({
                            "name": p.name,
                            "path": str(p),
                            "type": "dir" if p.is_dir() else "file",
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                        })
except Exception:
                        pass
                    
                    if len(results) >= 50:
                        break

            self._send_json({"results": results, "total": len(results), "query": query})
        except Exception as e:
            self._send_json({"error": str(e), "results": []})

    def _api_info(self, path: str):
        p = Path(path).expanduser()
        if not p.exists():
            self._send_json({"error": "Not found"}, 404)
            return

        try:
            stat = p.stat()
            info = {
                "name": p.name,
                "path": str(p),
                "type": "dir" if p.is_dir() else "file",
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "permissions": oct(stat.st_mode)[-3:],
                "owner": stat.st_uid,
                "group": stat.st_gid,
            }
            
            if p.is_dir():
                info["contents"] = len(list(p.iterdir()))
            
            # File preview for text files
            if p.is_file() and p.suffix.lower() in ['.txt', '.md', '.py', '.sh', '.json', '.xml', '.yaml', '.yml', '.cfg', '.conf', '.ini', '.log', '.csv']:
                try:
                    info["preview"] = p.read_text(encoding='utf-8', errors='replace')[:2000]
except Exception:
                    pass

            self._send_json(info)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _get_disk_usage(self, path: Path):
        try:
            stat = os.statvfs(str(path))
            total = stat.f_frsize * stat.f_blocks
            free = stat.f_frsize * stat.f_bfree
            return {
                "total": total,
                "free": free,
                "used": total - free,
                "percent": ((total - free) / total * 100) if total else 0
            }
except Exception:
            return {}

    def _serve_interface(self):
        """Serve the browser-based file manager UI."""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SID File Explorer</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0a0a; color: #0f0; font-family: 'Courier New', monospace; font-size: 14px; padding: 20px; }
.header { border-bottom: 1px solid #0f03; padding-bottom: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
.header h1 { color: #0f0; font-size: 18px; }
.breadcrumb { color: #080; font-size: 12px; margin-bottom: 15px; padding: 8px; background: #0f01; border: 1px solid #0f02; }
.breadcrumb a { color: #0f0; text-decoration: none; }
.breadcrumb a:hover { text-decoration: underline; }
.search-box { display: flex; gap: 8px; margin-bottom: 15px; }
.search-box input { flex: 1; background: #000; border: 1px solid #0f03; color: #0f0; padding: 8px; font-family: inherit; }
.search-box input:focus { outline: none; border-color: #0f0; }
.search-box button { background: #0f02; border: 1px solid #0f0; color: #0f0; padding: 8px 16px; cursor: pointer; font-family: inherit; }
.search-box button:hover { background: #0f04; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 8px; border-bottom: 1px solid #0f03; color: #080; font-weight: normal; font-size: 11px; text-transform: uppercase; }
td { padding: 8px; border-bottom: 1px solid #0f01; }
tr:hover { background: #0f01; }
tr.dir { cursor: pointer; }
.file-icon { width: 24px; text-align: center; }
.file-name { color: #0f0; }
.file-name a { color: #0f0; text-decoration: none; }
.file-name a:hover { text-decoration: underline; }
.file-size { color: #080; text-align: right; }
.file-date { color: #060; font-size: 12px; }
.file-perms { color: #050; font-size: 11px; }
.dir .file-name a { font-weight: bold; }
.dir .file-icon { color: #0f0; }
.stats { color: #060; font-size: 11px; margin-top: 10px; text-align: right; }
.error { color: #f00; padding: 20px; text-align: center; }
.loading { text-align: center; padding: 40px; color: #080; }
.preview { background: #000; border: 1px solid #0f02; padding: 15px; margin-top: 15px; white-space: pre-wrap; font-size: 12px; color: #0a0; max-height: 400px; overflow: auto; }
.actions { display: flex; gap: 8px; }
.actions button { background: none; border: 1px solid #0f03; color: #0f0; padding: 4px 8px; cursor: pointer; font-family: inherit; font-size: 11px; }
.actions button:hover { background: #0f03; }
#status { color: #060; font-size: 11px; }
</style>
</head>
<body>
<div class="header">
  <h1>█ SID File Explorer</h1>
  <div><button onclick="openDir('/')" style="background:#0f02;border:1px solid #0f0;color:#0f0;padding:4px 12px;cursor:pointer;font-family:inherit">/ (root)</button>
  <button onclick="openDir('~')" style="background:#0f02;border:1px solid #0f0;color:#0f0;padding:4px 12px;cursor:pointer;font-family:inherit">~ (home)</button></div>
</div>
<div class="search-box">
  <input type="text" id="searchInput" placeholder="Search files..." onkeydown="if(event.key==='Enter') searchFiles()">
  <button onclick="searchFiles()">Search</button>
  <button onclick="clearSearch()">Clear</button>
  <span id="status"></span>
</div>
<div id="breadcrumb" class="breadcrumb">/</div>
<div id="preview"></div>
<div id="content"><div class="loading">Loading...</div></div>
<div class="stats" id="stats"></div>

<script>
let currentDir = '/';
let currentItems = [];

async function api(url) {
  const resp = await fetch(url);
  return resp.json();
}

async function openDir(dir) {
  if (dir === '~') dir = '/root';
  currentDir = dir;
  document.getElementById('content').innerHTML = '<div class="loading">Loading...</div>';
  document.getElementById('preview').innerHTML = '';
  
  const data = await api('/api/list?dir=' + encodeURIComponent(dir));
  
  if (data.error) {
    document.getElementById('content').innerHTML = '<div class="error">' + data.error + '</div>';
    return;
  }
  
  currentItems = data.items;
  
  let bread = data.path.split('/').filter(Boolean);
  let breadHtml = '<a href="#" onclick="openDir(\'/\')">/</a>';
  let accum = '';
  for (let p of bread) {
    accum += '/' + p;
    breadHtml += ' <span style="color:#030">/</span> <a href="#" onclick="openDir(\'' + accum + '\')">' + p + '</a>';
  }
  if (data.parent) {
    breadHtml = '<a href="#" onclick="openDir(\'' + data.parent + '\')">..</a> / ' + breadHtml;
  }
  document.getElementById('breadcrumb').innerHTML = breadHtml;
  
  let html = '<table><tr><th></th><th>Name</th><th>Size</th><th>Modified</th><th>Perms</th><th></th></tr>';
  
  for (let item of data.items) {
    let icon = item.type === 'dir' ? '📁' : getIcon(item.ext);
    let sizeStr = item.type === 'dir' ? '-' : formatSize(item.size);
    let dateStr = new Date(item.modified * 1000).toLocaleString();
    let rowClass = item.type === 'dir' ? 'dir' : '';
    
    html += '<tr class="' + rowClass + '" onclick="' + (item.type === 'dir' ? 'openDir(\'' + item.path + '\')' : '') + '">';
    html += '<td class="file-icon">' + icon + '</td>';
    html += '<td class="file-name"><a href="#" onclick="' + (item.type === 'dir' ? 'openDir(\'' + item.path + '\');return false' : 'showFile(\'' + item.path + '\');return false') + '">' + item.name + '</a></td>';
    html += '<td class="file-size">' + sizeStr + '</td>';
    html += '<td class="file-date">' + dateStr + '</td>';
    html += '<td class="file-perms">' + item.permissions + '</td>';
    html += '<td class="actions"><button onclick="previewFile(\'' + item.path + '\');event.stopPropagation()">👁</button></td>';
    html += '</tr>';
  }
  
  html += '</table>';
  document.getElementById('content').innerHTML = html;
  
  let ds = data.disk_usage || {};
  if (ds.total) {
    document.getElementById('stats').textContent = data.items.length + ' items | Disk: ' + formatSize(ds.used) + ' / ' + formatSize(ds.total) + ' (' + (ds.percent || 0).toFixed(1) + '%)';
  } else {
    document.getElementById('stats').textContent = data.items.length + ' items';
  }
}

function getIcon(ext) {
  const icons = { '.py':'🐍', '.sh':'⚡', '.js':'🟨', '.html':'🌐', '.css':'🎨', '.json':'📋', '.md':'📝', '.txt':'📄', '.jpg':'🖼', '.png':'🖼', '.mp3':'🎵', '.mp4':'🎬', '.pdf':'📕', '.zip':'📦' };
  return icons[ext] || '📄';
}

function formatSize(bytes) {
  if (!bytes) return '0B';
  const k = 1024;
  const sizes = ['B','KB','MB','GB','TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + sizes[i];
}

async function searchFiles() {
  const q = document.getElementById('searchInput').value;
  if (!q) return;
  document.getElementById('content').innerHTML = '<div class="loading">Searching...</div>';
  
  const data = await api('/api/search?q=' + encodeURIComponent(q) + '&dir=' + encodeURIComponent(currentDir));
  
  if (data.results && data.results.length) {
    let html = '<table><tr><th></th><th>Name (search: ' + q + ')</th><th>Path</th><th>Size</th><th>Modified</th></tr>';
    for (let item of data.results) {
      html += '<tr onclick="openDir(\'' + (item.type==='dir'?item.path:require('path').dirname?item.path:item.path)+ '\')">';
      html += '<td>' + (item.type==='dir'?'📁':'📄') + '</td>';
      html += '<td>' + item.name + '</td>';
      html += '<td style="color:#060;font-size:12px">' + item.path + '</td>';
      html += '<td class="file-size">' + formatSize(item.size) + '</td>';
      html += '<td class="file-date">' + new Date(item.modified * 1000).toLocaleString() + '</td></tr>';
    }
    html += '</table><div class="stats">' + data.total + ' results</div>';
    document.getElementById('content').innerHTML = html;
  } else {
    document.getElementById('content').innerHTML = '<div class="error">No results for: ' + q + '</div>';
  }
}

function clearSearch() {
  document.getElementById('searchInput').value = '';
  openDir(currentDir);
}

async function previewFile(path) {
  const info = await api('/api/info?path=' + encodeURIComponent(path));
  if (info.preview) {
    document.getElementById('preview').innerHTML = '<div class="preview">' + escapeHtml(info.preview) + '</div>';
  } else {
    document.getElementById('preview').innerHTML = '<div class="preview" style="color:#060">Binary file - ' + formatSize(info.size) + ' bytes</div>';
  }
}

function showFile(path) {
  previewFile(path);
}

function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

openDir('/root');
</script>
</body>
</html>"""
        self._send_html(html)


class FileBrowserHTTPServer(HTTPServer, object):
    """Threaded HTTP server for file browser."""

    def __init__(self, host, port, root):
        self.root = Path(root).expanduser()
        handler = partial(FileBrowserHandler, root=self.root)
        super().__init__((host, port), handler)
        self.daemon_threads = True


class BrowserFileExplorer:
    """Browser-based file explorer running on localhost."""

    def __init__(self, port: int = 2025, root: str = "/"):
        self.port = port
        self.root = Path(root).expanduser()
        self._server = None
        self._thread = None

    def start(self) -> Dict:
        """Start the file browser HTTP server."""
        if self._server:
            return {"status": "already_running", "url": f"http://localhost:{self.port}"}

        try:
            self._server = FileBrowserHTTPServer("127.0.0.1", self.port, self.root)
            self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
            self._thread.start()
            
            # Verify it started
            import urllib.request
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{self.port}", timeout=2)
                return {
                    "status": "running",
                    "url": f"http://localhost:{self.port}",
                    "port": self.port,
                    "root": str(self.root)
                }
except Exception:
                return {"status": "started_but_unreachable", "port": self.port}
        except Exception as e:
            return {"error": str(e)}

    def stop(self):
        """Stop the file browser server."""
        if self._server:
            self._server.shutdown()
            self._server = None
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def url(self) -> str:
        """Get browser URL."""
        return f"http://localhost:{self.port}"

    def open(self):
        """Open file browser in system browser."""
        import subprocess
        browsers = ['xdg-open', 'sensible-browser', 'firefox', 'chromium', 'www-browser']
        url = self.url()
        for browser in browsers:
            try:
                subprocess.Popen([browser, url], 
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
except Exception:
                continue
        print(f"[SID] Open {url} in your browser")
        return False
