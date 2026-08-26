import argparse
import functools
import http.server
import json
import pathlib
import threading
import urllib.parse
import webbrowser

PORT = 8766
MUSIK_DIR = str(pathlib.Path(__file__).resolve().parent / "musik")
AUDIO = {".mp3": "audio/mpeg", ".wav": "audio/wav", ".flac": "audio/flac",
         ".ogg": "audio/ogg", ".m4a": "audio/mp4"}


class Handler(http.server.SimpleHTTPRequestHandler):
    musik = pathlib.Path(MUSIK_DIR)

    def _send(self, code, headers=(), body=b"", head=False):
        self.send_response(code)
        for key, value in headers:
            self.send_header(key, str(value))
        self.send_header("Content-Length", len(body))
        self.end_headers()
        if not head and body:
            self.wfile.write(body)

    def _json_error(self, code, message):
        body = json.dumps({"error": message}, ensure_ascii=False).encode()
        self._send(code, (("Content-Type", "application/json; charset=utf-8"),
                          ("Cache-Control", "no-store")), body,
                   self.command == "HEAD")

    def _range(self, size):
        value = self.headers.get("Range")
        if not value:
            return None
        if not value.startswith("bytes=") or "," in value:
            return False
        spec = value[6:]
        if "-" not in spec:
            return False
        left, right = spec.split("-", 1)
        try:
            if left:
                start = int(left)
                end = int(right) if right else size - 1
            elif right:
                count = int(right)
                start, end = max(0, size - count), size - 1
            else:
                return False
        except ValueError:
            return False
        if size == 0 or start < 0 or end < start or start >= size:
            return False
        return start, min(end, size - 1)

    def _music(self, name):
        root = self.musik.resolve()
        target = (root / name).resolve()
        if (
            target.parent != root
            or target.name != name
            or not target.is_file()
            or target.suffix.lower() not in AUDIO
        ):
            return None
        return target

    def _serve_music(self, name):
        target = self._music(name)
        if target is None:
            self._json_error(404, "track not found")
            return
        try:
            size = target.stat().st_size
        except OSError:
            self._json_error(404, "track not found")
            return
        span = self._range(size)
        headers = (("Content-Type", AUDIO.get(target.suffix.lower(),
                                             "application/octet-stream")),
                   ("Accept-Ranges", "bytes"), ("Last-Modified",
                   self.date_time_string(target.stat().st_mtime)),
                   ("X-Content-Type-Options", "nosniff"),
                   ("Cache-Control", "no-cache"))
        if span is False:
            self._send(416, headers + (("Content-Range", "bytes */%d" % size),),
                       b"", self.command == "HEAD")
            return
        start, end = (span or (0, size - 1))
        code = 206 if span else 200
        extra = (("Content-Range", "bytes %d-%d/%d" % (start, end, size)),) if span else ()
        self.send_response(code)
        for key, value in headers + extra:
            self.send_header(key, str(value))
        self.send_header("Content-Length", end - start + 1)
        self.end_headers()
        if self.command == "HEAD":
            return
        try:
            with target.open("rb") as stream:
                stream.seek(start)
                remaining = end - start + 1
                while remaining:
                    chunk = stream.read(min(512 * 1024, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def _api(self):
        try:
            root = self.musik.resolve()
            if not root.is_dir():
                raise OSError
            tracks = [{"name": p.name, "size": p.stat().st_size}
                      for p in sorted(root.iterdir(), key=lambda x: x.name.lower())
                      if p.is_file() and p.suffix.lower() in AUDIO]
        except (OSError, ValueError):
            self._json_error(503, "music directory unavailable")
            return
        body = json.dumps(tracks, ensure_ascii=False).encode()
        self._send(200, (("Content-Type", "application/json; charset=utf-8"),
                         ("Cache-Control", "no-store")), body,
                   self.command == "HEAD")

    def do_GET(self):
        self._dispatch()

    def do_HEAD(self):
        self._dispatch()

    def _dispatch(self):
        path = urllib.parse.urlsplit(self.path).path
        if path == "/api/tracks":
            self._api()
        elif path.startswith("/musik/"):
            raw = path[7:]
            try:
                name = urllib.parse.unquote(raw, encoding="utf-8", errors="strict")
            except UnicodeDecodeError:
                name = ""
            if (not name or "/" in name or "\\" in name or "\x00" in name or
                    name == ".." or pathlib.PurePath(name).name != name):
                self._json_error(404, "track not found")
            else:
                self._serve_music(name)
        else:
            super().do_GET() if self.command == "GET" else super().do_HEAD()

    def end_headers(self):
        path = self.path.split("?", 1)[0].lower()
        if path == "/" or path.endswith((".html", ".htm")):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *_):
        pass


class Server(http.server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--musik-dir", default=MUSIK_DIR)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    Handler.musik = pathlib.Path(args.musik_dir)
    root = pathlib.Path(__file__).resolve().parent
    handler = functools.partial(Handler, directory=str(root))
    with Server(("127.0.0.1", args.port), handler) as server:
        print("NEON BEAT : http://127.0.0.1:%d" % args.port, flush=True)
        if not args.no_browser:
            timer = threading.Timer(0.5, webbrowser.open,
                                    args=("http://127.0.0.1:%d" % args.port,))
            timer.daemon = True
            timer.start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()

