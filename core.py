#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🐳🔔 鲸铃 jingling · 核心

一个“脱离任何App”的通用门铃：
  轮询器(provider) → AI引擎(engine) → 唤醒器(waker)
三段都用“积木”组装，config.json 里选。
"""
import json, os, time, threading, importlib.util
from http.server import BaseHTTPRequestHandler, HTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))
LOG = os.path.join(BASE, "data", "log.jsonl")
SEENF = os.path.join(BASE, "data", "seen.json")
os.makedirs(os.path.join(BASE, "data"), exist_ok=True)

STATE = {"count": 0, "ringing": [], "seen": {}}
if os.path.exists(SEENF):
    try:
        STATE["seen"] = dict.fromkeys(json.load(open(SEENF)), 1)
    except Exception:
        pass


def load(kind, name):
    """动态加载一块积木：providers/mail.py 之类"""
    path = os.path.join(BASE, kind, name + ".py")
    spec = importlib.util.spec_from_file_location(f"{kind}_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── 按 config 装载三块积木 ──
PROVIDER = load("providers", CFG["provider"]["use"])
ENGINE = load("engines", CFG["engine"]["use"])
WAKER = load("wakers", CFG["waker"]["use"])
print(f"[jingling] 装载: provider={PROVIDER.NAME} engine={ENGINE.NAME} waker={WAKER.NAME}", flush=True)
# 若 provider 是“推模式”（有 start()），先启动它的后台监听
if hasattr(PROVIDER, "start"):
    try:
        PROVIDER.start(CFG["provider"])
        print("[jingling] provider 推模式监听已启动", flush=True)
    except Exception as e:
        print("[jingling] provider start 失败:", e, flush=True)


def save_seen():
    json.dump(list(STATE["seen"].keys())[-500:], open(SEENF, "w"))


def ring_once():
    msgs = PROVIDER.poll(CFG["provider"], STATE["seen"])
    for m in msgs:
        STATE["count"] += 1
        n = STATE["count"]
        print(f"[门铃 {n}] 收到: {m['title']}", flush=True)
        try:
            reply = ENGINE.think(m, CFG["engine"])
        except Exception as e:
            reply = f"(AI失败: {e})"
        rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "n": n, "msg": m["title"], "reply": reply}
        STATE["ringing"].insert(0, rec)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"[门铃 {n}] AI回: {reply[:80]}", flush=True)
        if CFG.get("waker", {}).get("enabled", True):
            wr = WAKER.wake({"source": CFG["provider"]["use"], "title": m["title"], "n": n}, CFG["waker"])
            print(f"[门铃 {n}] 唤醒 -> {wr[:120]}", flush=True)
    save_seen()


def loop():
    while True:
        time.sleep(CFG.get("interval", 30))
        try:
            ring_once()
        except Exception as e:
            print("loop error:", e, flush=True)


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/api"):
            out = json.dumps({"count": STATE["count"], "interval": CFG.get("interval", 30),
                              "provider": PROVIDER.NAME, "engine": ENGINE.NAME, "waker": WAKER.NAME,
                              "ringing": STATE["ringing"][:20]}, ensure_ascii=False)
            self.send_response(200)
        else:
            p = os.path.join(BASE, "index.html")
            out = open(p, encoding="utf-8").read() if os.path.exists(p) else "<h1>jingling</h1>"
            self.send_response(200)
        self.send_header("Content-Type", ("application/json" if self.path.startswith("/api") else "text/html") + "; charset=utf-8")
        self.end_headers()
        self.wfile.write(out.encode())


if __name__ == "__main__":
    threading.Thread(target=loop, daemon=True).start()
    _host = CFG.get("host", "127.0.0.1")
    _port = CFG.get("port", 8899)
    print(f"[jingling] 启动 → http://{_host}:{_port}", flush=True)
    HTTPServer((_host, _port), H).serve_forever()
