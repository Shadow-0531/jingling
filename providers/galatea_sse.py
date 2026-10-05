# -*- coding: utf-8 -*-
"""SSE push-mode provider: Galatea garden wake bridge.

Spec (push mode): NAME / start(cfg) / poll(cfg,seen)
Compliance: no auto-reconnect.
"""
import json, urllib.request, threading, queue, time

NAME = "galatea_sse"

_Q = queue.Queue()
_STARTED = {"v": False}
_LOCK = threading.Lock()


def _listen(cfg):
    url = cfg.get("sse_url", "https://wake-v1.abysslumina.com/api/machine-events/stream")
    token = cfg["token"]
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "text/event-stream",
    })
    try:
        r = urllib.request.urlopen(req, timeout=120)
    except Exception as e:
        _Q.put({"id": "sse-err-" + str(time.time()), "title": "garden SSE connect fail", "body": repr(e)})
        return
    ev = None
    try:
        for raw in r:
            line = raw.decode(errors="replace").rstrip("\n")
            if line.startswith(":"):
                continue
            if line.startswith("event:"):
                ev = line[6:].strip()
                continue
            if line.startswith("data:"):
                data = line[5:].strip()
                if ev == "wake":
                    try:
                        d = json.loads(data)
                    except Exception:
                        d = {"message": data}
                    reason = d.get("reason", "wake")
                    msg = d.get("message", data)
                    _Q.put({
                        "id": "wake|" + reason + "|" + msg[:60] + "|" + str(time.time()),
                        "title": "garden wake[" + reason + "]",
                        "body": msg,
                    })
                ev = None
                continue
            if line == "":
                ev = None
    except Exception as e:
        _Q.put({"id": "sse-end-" + str(time.time()), "title": "garden SSE closed", "body": repr(e)})


def start(cfg):
    with _LOCK:
        if _STARTED["v"]:
            return
        _STARTED["v"] = True
    t = threading.Thread(target=_listen, args=(cfg,), daemon=True)
    t.start()


def poll(cfg, seen):
    items = []
    n = int(cfg.get("limit", 8))
    while len(items) < n:
        try:
            it = _Q.get_nowait()
        except queue.Empty:
            break
        if it["id"] in seen:
            continue
        seen[it["id"]] = 1
        items.append(it)
    return items
