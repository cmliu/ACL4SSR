# -*- coding: utf-8 -*-
"""
把 ACL4SSR_Online_Full.ini（Clash/ACL4SSR风格）自动转换为 Shadowrocket .conf
- 仅转换你实际用到的两块：Ruleset / Groups
- 其它区块（[General]/[Proxy]/[URL Rewrite]/[MITM]）保留最小骨架，节点你在 Shadowrocket 里自己维护/订阅
- 支持：
  ruleset=组名,URL                  -> RULE-SET,URL,组名
  ruleset=组名,[]GEOIP,CN           -> GEOIP,CN,组名
  ruleset=组名,[]GEOIP,LAN          -> GEOIP,LAN,组名
  ruleset=组名,[]DOMAIN-SUFFIX,x.y  -> DOMAIN-SUFFIX,x.y,组名
  ruleset=组名,[]FINAL              -> FINAL,组名
  custom_proxy_group=...            -> [Proxy Group] 对应行
  注：Clash里用于“按正则自动收集节点”的 ( ... ) 无法直接在 SR 里表达，这里会忽略；首次导入后在 SR 里把节点加到这些组里即可（后续组名更新会同步）
"""
import re
from pathlib import Path

SRC = Path("Clash/config/ACL4SSR_Online_Full.ini")           # 你的 Clash 源
DST = Path("Clash/config/LUCK.conf")                          # 生成的小火箭目标

rules_lines = []
pg_lines = []

def parse_ruleset(line):
    # ruleset=组名,目标
    m = re.match(r'^\s*ruleset\s*=\s*([^,]+)\s*,\s*(.+?)\s*$', line, flags=re.I)
    if not m:
        return None
    group = m.group(1).strip()
    target = m.group(2).strip()

    # [] 内置指令
    m2 = re.match(r'^\[\]\s*([A-Z0-9\-]+)(?:\s*,\s*([^,]+))?$', target, flags=re.I)
    if m2:
        typ = m2.group(1).upper()
        arg = (m2.group(2) or "").strip()
        if typ == "FINAL":
            return f"FINAL,{group}"
        elif typ in ("GEOIP", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "IP-CIDR", "IP-CIDR6"):
            if arg:
                return f"{typ},{arg},{group}"
        # 其它类型不常见，这里忽略
        return None

    # URL
    if target.startswith("http://") or target.startswith("https://"):
        return f"RULE-SET,{target},{group}"

    # 兜底：不支持的写法忽略
    return None

def parse_group(line):
    # custom_proxy_group=名称`类型`项1`项2`...（项里常见 []DIRECT / []组名 / .*/(正则) / URL / 参数 300,,50）
    m = re.match(r'^\s*custom_proxy_group\s*=\s*([^\`]+)\`([^\`]+)\`(.+)$', line, flags=re.I)
    if not m:
        return None
    name = m.group(1).strip()
    gtype = m.group(2).strip().lower()
    rest = m.group(3).strip()

    tokens = [t for t in rest.split('`') if t.strip()]

    items = []
    url = None
    interval = None
    tolerance = None

    for t in tokens:
        s = t.strip()
        if s.startswith("[]"):
            items.append(s[2:].strip())     # []DIRECT -> DIRECT, []组名 -> 组名
        elif s == ".*":
            items.append("ALL")             # Clash 的正则“全部”，在 SR 里用 ALL 兜底
        elif s.startswith("(") and s.endswith(")"):
            # Clash 正则收集节点名 —— SR 无法自动匹配，跳过（用户在 SR 里手动把节点加入该组）
            continue
        elif s.startswith("http://") or s.startswith("https://"):
            url = s
        else:
            # 可能是参数块 300,,50
            if re.match(r'^\d+,,\d+$', s):
                parts = s.split(',')
                interval = parts[0]
                tolerance = parts[2]

    # 组行生成
    if gtype in ("select", "fallback", "load-balance", "url-test"):
        line = f"{name} = {gtype}"
        if items:
            line += ", " + ", ".join(items)
        if url:
            line += f", url = {url}"
        if interval:
            line += f", interval = {interval}"
        if tolerance and gtype in ("url-test", "fallback"):
            line += f", tolerance = {tolerance}"
        return line
    else:
        # 其它类型很少见，先按 select 兜底
        line = f"{name} = select"
        if items:
            line += ", " + ", ".join(items)
        return line

def main():
    if not SRC.exists():
        raise SystemExit(f"源文件不存在：{SRC}")

    with SRC.open("r", encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            if not s or s.startswith(";") or s.startswith("#"):
                continue

            if s.lower().startswith("ruleset="):
                r = parse_ruleset(s)
                if r:
                    rules_lines.append(r)
            elif s.lower().startswith("custom_proxy_group="):
                g = parse_group(s)
                if g:
                    pg_lines.append(g)

    # 生成 Shadowrocket .conf
    out = []
    out.append("[General]")
    out.append("bypass-system = true")
    out.append("dns-server = system")
    out.append("ipv6 = true")
    out.append("")

    out.append("[Proxy]")
    out.append("# 节点/订阅留空：在 Shadowrocket 内添加即可")
    out.append("")

    out.append("[Proxy Group]")
    if pg_lines:
        out.extend(pg_lines)
    out.append("")

    out.append("[Rule]")
    if rules_lines:
        out.extend(rules_lines)
    out.append("")

    out.append("[URL Rewrite]")
    out.append("# 如需，后续自行加入或远程 include")
    out.append("")

    out.append("[Host]")
    out.append("# 如需，后续自行加入")
    out.append("")

    out.append("[MITM]")
    out.append("enable = false")
    out.append("")

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text("\n".join(out), encoding="utf-8")
    print(f"✅ 生成完成：{DST}")

if __name__ == "__main__":
    main()
