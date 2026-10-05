# -*- coding: utf-8 -*-
"""📮 数据源积木：邮箱（POP3）
【积木规范】一个 provider 必须提供两个东西：
  1. NAME        : 字符串，本积木的名字
  2. poll(cfg, seen) : 函数，返回“新消息列表” list[dict]
                   每个 dict 至少含 {"id", "title", "body"}
                   没新消息就返回 []
config 里 provider 段会原样传给 poll(cfg, seen)。
"""
import poplib, email, re
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

def mark_seen(seen, mid):
    """去重兼容层：core.py 传进来的可能是 set，也可能是 dict，两种都接住。"""
    try:
        seen.add(mid)      # 传进来是 set
    except AttributeError:
        seen[mid] = 1      # core.py 实际传的是 dict

def get_body(msg, limit=1500):
    """取正文：优先 text/plain，退一步把 text/html 去标签，最后截断。"""
    text = ""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                disp = str(part.get("Content-Disposition") or "")
                if "attachment" in disp:
                    continue
                if ctype == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                        break
            if not text:
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        payload = part.get_payload(decode=True)
                        if payload:
                            text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                            break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                text = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    except Exception as e:
        print(f"[mail] 取正文失败: {e}", flush=True)
        return ""
    if "<" in text and ">" in text:
        text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 30:
        return "（这封信没有可读正文，可能只有样式/图片）"
    return text[:limit]

def poll(cfg, seen):
    """cfg: pop_host/pop_port/user/pass/scan_last；seen: set 或 dict（已见id）"""
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
            mark_seen(seen, mid)
            sender = dh(msg.get("From"))
            subj = dh(msg.get("Subject"))
            body = get_body(msg)
            new.append({"id": mid, "title": f"来自 {sender}，主题：{subj}", "body": body})
        except Exception as e:
            print(f"[mail] 第 {i} 封处理失败: {e}", flush=True)
    P.quit()
    return new
