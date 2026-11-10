"""
lab_web_server.py - a local "business app" to monitor, with pages that behave like real failures.

    /health  -> 200 "ok"                 (what a load balancer / monitor polls)
    /slow    -> 200 after ~1.2 s         (app overloaded / slow database)
    /broken  -> 500 Internal Server Error (app bug)
    /        -> 200 index page
    anything else -> 404

Usage:
    python lab_web_server.py          # http://127.0.0.1:8080
    python lab_web_server.py 8081
Every request is logged in the same format as an Apache/Nginx access log.
"""

import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


class Handler(BaseHTTPRequestHandler):
    def send(self, code: int, body: str) -> None:
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send(200, "ok")
        elif self.path == "/slow":
            time.sleep(1.2)
            self.send(200, "finally done")
        elif self.path == "/broken":
            self.send(500, "Internal Server Error: NullReferenceException in OrderService")
        elif self.path == "/":
            self.send(200, "Lab business app - try /health /slow /broken")
        else:
            self.send(404, "not found")


if __name__ == "__main__":
    print(f"Lab app on http://127.0.0.1:{PORT}  (Ctrl+C to stop) - access log below:")
    try:
        ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
