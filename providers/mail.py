# -*- coding: utf-8 -*-
"""📮 数据源积木：邮箱（POP3）

【积木规范】一个 provider 必须提供两个东西：
  1. NAME        : 字符串，本积木的名字
  2. poll(cfg)   : 函数，返回“新消息列表” list[dict]
                   每个 dict 至少含 {"id", "title", "body"}
                   没新消息就返回 []
config 里 provider 段会原样传给 poll(cfg)。
"""
import poplib, email
from email.header import decode_header

NAME = "mail"


def dh(s):
    if not s:
        return ""
    out = []
    for part, enc in decode_header(s):
        if isinstance(part, bytes):
            try:
                out.append(part.decode(enc or "utf-8", errors="replace"))
            except Exception:
                out.append(part.decode("utf-8", errors="replace"))
        else:
            out.append(part)
    return "".join(out)


def poll(cfg, seen):
    """cfg: pop_host/pop_port/user/pass/scan_last；seen: set（已见id）"""
    P = poplib.POP3_SSL(cfg["pop_host"], cfg["pop_port"], timeout=40)
    P.user(cfg["user"])
    P.pass_(cfg["pass"])
    total = len(P.list()[1])
    new = []
    start = max(1, total - cfg.get("scan_last", 5) + 1)
    for i in range(start, total + 1):
        try:
            raw = b"\n".join(P.retr(i)[1])
            msg = email.message_from_bytes(raw)
            mid = msg.get("Message-ID", f"idx-{i}")
            if mid in seen:
                continue
            seen.add(mid)
            sender = dh(msg.get("From"))
            subj = dh(msg.get("Subject"))
            new.append({"id": mid, "title": f"来自 {sender}，主题：{subj}", "body": subj})
        except Exception:
            pass
    P.quit()
    return new
