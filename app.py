import json, os, re, tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from recognition_engine import analyze_image_bytes, ValidationError
from recommendation_engine import recommend_schedule

ROOT = os.path.dirname(os.path.abspath(__file__))
MAX_UPLOAD = 8 * 1024 * 1024

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type="text/html; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code); self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if urlparse(self.path).path == "/":
            with open(os.path.join(ROOT, "static", "index.html"), encoding="utf-8") as f: self._send(200, f.read())
        elif self.path.startswith("/static/"):
            p = os.path.join(ROOT, self.path.removeprefix("/"))
            if os.path.isfile(p):
                c = "text/css; charset=utf-8" if p.endswith(".css") else "application/javascript; charset=utf-8"
                with open(p, "rb") as f: self._send(200, f.read(), c)
            else: self._send(404, "Not found")
        else: self._send(404, "Not found")
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > MAX_UPLOAD: raise ValidationError("파일 크기는 8MB 이하만 지원합니다.")
            raw = self.rfile.read(length)
            if self.path == "/api/recognize": result = analyze_image_bytes(raw)
            elif self.path == "/api/recommend": result = recommend_schedule(json.loads(raw.decode("utf-8")))
            else: self._send(404, "Not found"); return
            self._send(200, json.dumps(result, ensure_ascii=False), "application/json; charset=utf-8")
        except (ValidationError, ValueError, json.JSONDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}, ensure_ascii=False), "application/json; charset=utf-8")
        except Exception as e:
            self._send(500, json.dumps({"error": "처리 중 오류가 발생했습니다.", "detail": str(e)}, ensure_ascii=False), "application/json; charset=utf-8")

if __name__ == "__main__":
    print("Local timetable planner: http://127.0.0.1:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
