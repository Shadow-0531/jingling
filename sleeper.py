#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sleeper.py = whale-bell universal exit (a demo "your own AI").

It receives the POST from jingling waker and does 3 things (all offline):
  1) append to data/woken.jsonl      (raw log)
  2) append to data/inbox.txt        (human-readable inbox)
  3) if cfg webhook set -> forward   (e.g. wechat/serverchan/your own AI)

This file is a TEMPLATE for "how to wake MY AI": replace handle() with
your own logic (call your model, push notification, etc.).
"""
import json, time, os
from http.server import BaseHTTPRequestHandler, HTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
WOKEN = os.path.join(DATA, "woken.jsonl")
INBOX = os.path.join(DATA, "inbox.txt")
os.makedirs(DATA, exist_ok=True)
PORT = int(os.environ.get("JINGLING_SLEEPER_PORT", "8911"))

# optional webhook forward (leave empty to disable)
WEBHOOK = os.environ.get("JINGLING_WEBHOOK", "")


def handle(msg):
    """=== YOUR AI'S ENTRY POINT ===
    The wake payload arrives here. Replace the body with your own logic,
    e.g. call your model API, send a wechat message, push a notification.
    For demo we just record it. Return a short string for the caller.
    """
    title = str(msg.get("title", ""))
    # 1) raw log
    wake = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "payload": msg,
        "status": "awake",
    }
    with open(WOKEN, "a", encoding="utf-8") as f:
        f.write(json.dumps(wake, ensure_ascii=False) + "\n")
    # 2) human inbox
    with open(INBOX, "a", encoding="utf-8") as f:
        f.write("[%s] %s\n" % (wake["ts"], title))
    # 3) optional webhook forward
    if WEBHOOK:
        try:
            import urllib.request
            data = json.dumps(msg, ensure_ascii=False).encode()
            req = urllib.request.Request(WEBHOOK, data=data, method="POST",
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10).read()
        except Exception as e:
            print("[sleeper] webhook fail: %r" % (e,), flush=True)
    return "sleeper awake, got it"


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n).decode("utf-8") if n else ""
        try:
            msg = json.loads(body)
        except Exception:
            msg = {"raw": body}
        result = handle(msg)
        print("[sleeper] woken! payload=%s" % json.dumps(msg, ensure_ascii=False)[:120], flush=True)
        resp = json.dumps({"ok": True, "msg": result}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(resp)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"sleeper alive")


if __name__ == "__main__":
    import os as _os
    _host = _os.environ.get("SLEEPER_HOST", "127.0.0.1")
    print("sleeper (universal exit) start -> http://%s:%d" % (_host, PORT), flush=True)
    HTTPServer((_host, PORT), H).serve_forever()
