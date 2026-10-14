#!/usr/bin/env python3
"""Отдаёт текущий репозиторий симулятору по тому же пути, что и GitHub Pages."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "/ai-bez-lyudey"


class PreviewServer(ThreadingHTTPServer):
    # Браузер запрашивает шрифты и картинки одновременно; очередь не должна их обрывать.
    request_queue_size = 128
    daemon_threads = True


class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def translate_path(self, path):
        if path.startswith(PREFIX + "/"):
            path = path[len(PREFIX):]
        return super().translate_path(path)

    def do_GET(self):
        if urlsplit(self.path).path == "/":
            self.send_response(302)
            self.send_header("Location", PREFIX + "/kursy/")
            self.end_headers()
            return
        super().do_GET()


if __name__ == "__main__":
    print("Просмотр: http://localhost:4376/ai-bez-lyudey/kursy/", flush=True)
    try:
        PreviewServer(("127.0.0.1", 4376), PreviewHandler).serve_forever()
    except OSError as error:
        raise SystemExit("Порт 4376 уже занят или недоступен. Если просмотр сайта работает, второй сервер не нужен.") from error
