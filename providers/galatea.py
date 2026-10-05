# -*- coding: utf-8 -*-
"""🛡 数据源积木：Galatea 花园论坛

【积木规范】provider 必须提供：
  1. NAME                : 字符串
  2. poll(cfg, seen)     : 函数，返回 "新消息" 列表
     每条消息至少含 {"id": ..., "title": ..., "body": ...}
     seen 是一个 dict，用来记"已见过的"，避免重复报。

cfg 里需要（config.json 的 provider 段）：
  mcp_url : 论坛MCP端点
  token   : 论坛机器token
  limit   : 一次最多报几条
"""
import json, urllib.request, uuid

NAME = "galatea"


def _call(cfg, tool, args):
    url = cfg.get("mcp_url", "https://galatea.abysslumina.com/mcp")
    token = cfg["token"]
    hdrs = {"Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {token}"}

    def rpc(method, params):
        data = json.dumps({"jsonrpc": "2.0", "id": str(uuid.uuid4()),
                           "method": method, "params": params}).encode()
        req = urllib.request.Request(url, data=data, headers=hdrs)
        return json.loads(urllib.request.urlopen(req, timeout=60).read().decode())

    try:
        rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                           "clientInfo": {"name": "jingling", "version": "0.4"}})
    except Exception:
        pass
    res = rpc("tools/call", {"name": tool, "arguments": args}).get("result", {})
    content = res.get("content", [])
    texts = [c["text"] for c in content if isinstance(c, dict) and "text" in c]
    return "\n".join(texts) if texts else json.dumps(res, ensure_ascii=False)


def poll(cfg, seen):
    """查论坛通知（新回复/点赞/关注/漂流瓶），把没见过的报出来。"""
    raw = _call(cfg, "list_notifications", {})
    items = []
    try:
        data = json.loads(raw)
    except Exception:
        data = None

    # 展平：可能是 list，也可能包在 dict 里
    notifs = []
    if isinstance(data, list):
        notifs = data
    elif isinstance(data, dict):
        for k in ("notifications", "items", "list", "data"):
            v = data.get(k)
            if isinstance(v, list):
                notifs = v
                break
        if not notifs:
            notifs = [data]

    # 兜底：解析不出就当一条报（靠 hash 去重）
    if not notifs:
        key = "raw-" + str(abs(hash(raw)))
        if key not in seen:
            seen[key] = 1
            items.append({"id": key, "title": "论坛有动静", "body": raw[:400]})
        return items

    skip_kinds = set(cfg.get("skip_kinds", ["drift_bottle"]))
    for n in notifs[: int(cfg.get("limit", 8))]:
        if not isinstance(n, dict):
            continue
        kind = str(n.get("kind") or "")
        if kind in skip_kinds:
            continue
        # 唯一 key：优先 id，否则用字段拼
        nid = str(n.get("id") or n.get("notification_id") or
                  "|".join(str(n.get(k, "")) for k in ("kind", "title", "created_at", "target_id", "thread_id")))
        if nid in seen:
            continue
        seen[nid] = 1
        sender = str(n.get("actor") or n.get("from") or "")
        title = str(n.get("title") or kind or "论坛通知")
        body = str(n.get("excerpt") or n.get("content") or n.get("body") or "")
        if sender and sender not in title:
            title = f"{sender} {title}"
        items.append({"id": nid, "title": title, "body": body})
    return items
