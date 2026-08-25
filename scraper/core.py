"""
中国古玉 / 翡翠 · 海外拍卖实时抓取核心

设计要点
--------
* 所有源由 sources.yml 驱动；新增一家 = 加一段配置，不改代码。
* 每个源按 三级解析 依次尝试，先成功者胜，并把命中的策略写进健康报告：
    1. configured  —— sources.yml 里写好的 CSS 选择器
    2. jsonld      —— 页面内嵌 schema.org JSON-LD（ItemList / Product）
    3. links       —— 按 lot_url_pattern 正则捞链接 + 锚文本，最保底
* 抓取环境（GitHub Actions）与解析规则的正确性无法在开发容器内验证，
  因此 probe 模式会把每个源的真实响应特征打进日志，用于反向校正配置。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from urllib.parse import urljoin, quote_plus

import requests
import yaml
from bs4 import BeautifulSoup

from browser import Browser

BROWSER = Browser()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources.yml")
DATA_DIR = os.path.join(ROOT, "data")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "sec-ch-ua": '"Chromium";v="127", "Not)A;Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "Connection": "keep-alive",
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# ── 关键词：玉 ────────────────────────────────────────────────────────────
JADE_RE = re.compile(
    r"\b(jade|jadeite|jadeit|nephrite|néphrite|jadéite|feicui|hardstone)\b|玉|翡翠|軟玉|硬玉",
    re.I)
# hardstone 单独出现时太宽，需要额外中国信号，见 is_target()

# ── 关键词：中国 ──────────────────────────────────────────────────────────
CHINA_RE = re.compile(
    r"\b(chin(a|ese)|sino|qing|ching|ming|yuan dynasty|song dynasty|tang dynasty|"
    r"han dynasty|zhou|shang|warring states|neolithic|hongshan|liangzhu|qijia|longshan|"
    r"kangxi|yongzheng|qianlong|ch.ien.lung|jiaqing|daoguang|tao.kuang|xianfeng|tongzhi|guangxu|"
    r"hetian|khotan|mughal|moghul|hindustan|archaistic|archaic|mandarin|imperial court|"
    r"cong|bi disc|ruyi|zigang|tsung|pi disc|belt.?hook|scholar.s|qilin|kylin|"
    r"chinois|chinesisch|kinesisk|kinesiska|cinese)\b|中国|中國|清|明|漢|汉|唐|宋|乾隆",
    re.I)

# ── 年代分类（顺序敏感：先排除近现代，再由早到晚）────────────────────────
MODERN_RE = re.compile(
    r"\b(20th\s*century|twentieth\s*century|21st\s*century|republic\s*period|"
    r"art\s*deco|mid.?century|modern|contemporary|c\.?\s*19[2-9]\d|19[2-9]\ds|"
    r"20\d\d|1[89]\d\d-19[5-9]\d)\b|民国|民國|近现代|近現代|現代|现代",
    re.I)
PERIOD_RULES = [
    ("高古", re.compile(
        r"\b(neolithic|hongshan|liangzhu|qijia|longshan|shijiahe|erlitou|"
        r"shang\b|western\s*zhou|eastern\s*zhou|zhou\s*dynasty|spring\s*and\s*autumn|"
        r"warring\s*states|qin\s*dynasty|western\s*han|eastern\s*han|han\s*dynasty|"
        r"six\s*dynasties|archaic)\b|红山|紅山|良渚|齐家|齊家|商代|西周|东周|東周|战国|戰國|汉代|漢代", re.I)),
    ("唐宋辽金", re.compile(
        r"\b(tang\s*dynasty|sui\s*dynasty|song\s*dynasty|northern\s*song|southern\s*song|"
        r"liao\s*dynasty|jin\s*dynasty|xixia|western\s*xia)\b|唐代|宋代|辽代|遼代|金代|西夏", re.I)),
    ("元明", re.compile(
        r"\b(yuan\s*dynasty|ming\s*dynasty|ming\b|xuande|chenghua|jiajing|wanli|"
        r"14th\s*century|15th\s*century|16th\s*century)\b|元代|明代|明中期|明晚期", re.I)),
    ("清", re.compile(
        r"\b(qing\s*dynasty|qing\b|ching\b|kangxi|yongzheng|qianlong|ch.ien.lung|"
        r"jiaqing|daoguang|tao.kuang|xianfeng|tongzhi|guangxu|"
        r"17th\s*century|18th\s*century|19th\s*century)\b|清代|清中期|清晚期|乾隆|康熙|雍正|嘉庆|嘉慶|道光", re.I)),
]
# 允许通过的年代（用户要求：清代之前，含清代）
ALLOWED_PERIODS = {"高古", "唐宋辽金", "元明", "清", "未标注"}

MATERIAL_RULES = [
    ("翡翠", re.compile(r"\b(jadeite|jadeit|jadéite|feicui|imperial\s*green)\b|翡翠|硬玉", re.I)),
    ("和田玉/软玉", re.compile(r"\b(nephrite|néphrite|hetian|khotan|mutton\s*fat|white\s*jade|"
                             r"celadon\s*jade|spinach\s*jade|russet|yellow\s*jade|black\s*jade)\b|和田|软玉|軟玉|白玉|青玉|碧玉|墨玉", re.I)),
]

CURRENCY_RE = re.compile(
    r"(USD|EUR|GBP|CHF|SEK|DKK|NOK|JPY|HKD|AUD|CAD|SGD|TWD|£|\$|€|¥|kr)\s*"
    r"([\d][\d\s.,']*)", re.I)
CUR_MAP = {"£": "GBP", "$": "USD", "€": "EUR", "¥": "JPY", "kr": "SEK"}


# ══════════════════════════════════════════════════════════════════════════
@dataclass
class Lot:
    id: str
    source: str
    house: str
    region: str
    country: str
    title: str
    url: str
    image: str = ""
    price_text: str = ""
    currency: str = ""
    est_low: float | None = None
    est_high: float | None = None
    end_ts: str = ""
    lot_no: str = ""
    period: str = "未标注"
    material: str = "未标注"
    query: str = ""
    strategy: str = ""
    scraped_at: str = ""


@dataclass
class SourceHealth:
    id: str
    name: str
    region: str
    ok: bool = False
    strategy: str = ""
    lots: int = 0
    kept: int = 0
    http: list = field(default_factory=list)
    note: str = ""
    probe: dict = field(default_factory=dict)


# ══════════════════════════════════════════════════════════════════════════
def log(*a):
    print(*a, flush=True)


def load_sources(only: list[str] | None = None) -> list[dict]:
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    srcs = [s for s in cfg["sources"] if s.get("enabled", True)]
    if only:
        srcs = [s for s in srcs if s["id"] in only]
    return srcs


def fetch(url: str, timeout: int = 30, extra_headers: dict | None = None, referer: str = ""):
    h = dict(extra_headers or {})
    if referer:
        h["Referer"] = referer
    last = None
    for attempt in range(2):                     # 失败的源很多，重试要克制，否则整轮拖到几十分钟
        try:
            return SESSION.get(url, headers=h, timeout=timeout, allow_redirects=True)
        except Exception as e:                                   # noqa: BLE001
            last = e
            time.sleep(1.0 * (attempt + 1))
    raise last                                                   # type: ignore[misc]


# ── 选择器迷你语法： "css.selector | text" / "| attr:href" / "| html" ─────
def pick(node, spec: str, base_url: str = ""):
    if not spec:
        return ""
    css, _, mode = [x.strip() for x in spec.partition("|")]
    el = node.select_one(css) if css else node
    if el is None:
        return ""
    mode = mode or "text"
    if mode == "text":
        return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
    if mode.startswith("attr:"):
        val = el.get(mode.split(":", 1)[1], "") or ""
        if val and base_url and mode.split(":", 1)[1] in ("href", "src", "data-src", "content"):
            val = urljoin(base_url, val)
        return val
    if mode == "html":
        return str(el)
    return ""


def first_attr(el, names, base_url=""):
    for n in names:
        v = el.get(n)
        if v:
            return urljoin(base_url, v) if base_url else v
    return ""


# ── 解析策略 1：配置好的 CSS 选择器 ──────────────────────────────────────
def parse_configured(soup, src, page_url):
    item_sel = src.get("item")
    if not item_sel:
        return []
    out = []
    for sel in ([item_sel] if isinstance(item_sel, str) else item_sel):
        nodes = soup.select(sel)
        if not nodes:
            continue
        f = src.get("fields", {})
        for n in nodes:
            title = pick(n, f.get("title", ""), page_url) or re.sub(r"\s+", " ", n.get_text(" ", strip=True))[:200]
            url = pick(n, f.get("url", ""), page_url)
            if not url:
                a = n.select_one("a[href]")
                url = urljoin(page_url, a["href"]) if a else ""
            if not (title and url):
                continue
            img = pick(n, f.get("image", ""), page_url)
            if not img:
                im = n.select_one("img")
                img = first_attr(im, ["src", "data-src", "data-lazy", "data-original"], page_url) if im else ""
            out.append({
                "title": title, "url": url, "image": img,
                "price_text": pick(n, f.get("price", ""), page_url),
                "end": pick(n, f.get("end", ""), page_url),
                "house": pick(n, f.get("house", ""), page_url),
                "lot_no": pick(n, f.get("lot_no", ""), page_url),
            })
        if out:
            return out
    return out


# ── 解析策略 2：schema.org JSON-LD ───────────────────────────────────────
def _walk_products(obj, acc):
    if isinstance(obj, dict):
        t = obj.get("@type") or obj.get("type")
        types = [t] if isinstance(t, str) else (t or [])
        if any(str(x).lower() in ("product", "listitem", "offer", "individualproduct") for x in types):
            acc.append(obj)
        for v in obj.values():
            _walk_products(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _walk_products(v, acc)


def parse_jsonld(soup, src, page_url):
    raw = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        txt = tag.string or tag.get_text() or ""
        try:
            raw.append(json.loads(txt))
        except Exception:                                        # noqa: BLE001
            continue
    prods = []
    _walk_products(raw, prods)
    out = []
    for p in prods:
        item = p.get("item") if isinstance(p.get("item"), dict) else p
        name = item.get("name") or item.get("description") or ""
        url = item.get("url") or item.get("@id") or ""
        if not (name and isinstance(url, str) and url.startswith("http")):
            continue
        img = item.get("image")
        if isinstance(img, list):
            img = img[0] if img else ""
        if isinstance(img, dict):
            img = img.get("url", "")
        offers = item.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        price = offers.get("price") or offers.get("lowPrice") or ""
        cur = offers.get("priceCurrency") or ""
        out.append({
            "title": str(name)[:300], "url": url, "image": img or "",
            "price_text": (f"{cur} {price}".strip() if price else ""),
            "end": offers.get("availabilityEnds", "") or offers.get("validThrough", ""),
            "house": "", "lot_no": "",
        })
    return out


# ── 解析策略 3：链接正则兜底 ─────────────────────────────────────────────
def parse_links(soup, src, page_url):
    pat = src.get("lot_url_pattern")
    if not pat:
        return []
    rx = re.compile(pat, re.I)
    seen, out = set(), []
    for a in soup.select("a[href]"):
        href = urljoin(page_url, a["href"])
        if not rx.search(href) or href in seen:
            continue
        text = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
        if len(text) < 12:
            # 锚点常是图片，向上找卡片容器取文本
            box = a.find_parent(["li", "article", "div"])
            if box:
                text = re.sub(r"\s+", " ", box.get_text(" ", strip=True)).strip()[:300]
        if len(text) < 12:
            continue
        seen.add(href)
        im = a.select_one("img") or (a.find_parent(["li", "article", "div"]) or soup).select_one("img")
        out.append({
            "title": text[:300], "url": href,
            "image": first_attr(im, ["src", "data-src", "data-lazy", "data-original"], page_url) if im else "",
            "price_text": "", "end": "", "house": "", "lot_no": "",
        })
    return out


def href_shapes(soup, page_url, top=12):
    """把页面所有链接归一成形态（数字→#、长 slug→*），统计出现次数。
    这是反推 lot_url_pattern 最有效的证据：拍品链接必然是页面上最高频的形态之一。"""
    from collections import Counter
    host = re.sub(r"^https?://([^/]+).*", r"\1", page_url)
    cnt, sample = Counter(), {}
    for a in soup.select("a[href]"):
        href = urljoin(page_url, a["href"])
        if not href.startswith("http"):
            continue
        h = re.sub(r"^https?://", "", href).split("?")[0].split("#")[0]
        if not h.startswith(host):
            continue
        shape = re.sub(r"\d+", "#", h)
        shape = re.sub(r"/[^/]{25,}", "/*", shape)
        cnt[shape] += 1
        if shape not in sample:
            txt = re.sub(r"\s+", " ", a.get_text(" ", strip=True))[:60]
            sample[shape] = (href, txt)
    return [(sh, n, sample[sh][0], sample[sh][1]) for sh, n in cnt.most_common(top)]


# ── 解析策略 0：纯 JSON API ──────────────────────────────────────────────
def dig(obj, path):
    cur = obj
    for part in path.split("."):
        if part == "":
            continue
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
                continue
            except (ValueError, IndexError):
                return None
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
        if cur is None:
            return None
    return cur


def parse_json_api(payload, src, page_url):
    jf = src.get("json", {})
    items = dig(payload, jf.get("items", "")) if jf.get("items") else None
    if items is None and isinstance(payload, list):
        items = payload
    if not isinstance(items, list):
        return []
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        title = str(dig(it, jf.get("title", "title")) or "")
        url = str(dig(it, jf.get("url", "url")) or "")
        if url and not url.startswith("http"):
            url = urljoin(src.get("home", page_url), url)
        if jf.get("url_template") and not url:
            key = dig(it, jf.get("id", "id"))
            if key:
                url = jf["url_template"].replace("{id}", str(key))
        if not (title and url):
            continue
        img = dig(it, jf.get("image", "")) if jf.get("image") else ""
        if isinstance(img, list):
            img = img[0] if img else ""
        if isinstance(img, dict):
            img = img.get("url") or img.get("src") or ""
        out.append({
            "title": title[:300], "url": url, "image": str(img or ""),
            "price_text": str(dig(it, jf.get("price", "")) or "") if jf.get("price") else "",
            "end": str(dig(it, jf.get("end", "")) or "") if jf.get("end") else "",
            "house": str(dig(it, jf.get("house", "")) or "") if jf.get("house") else "",
            "lot_no": str(dig(it, jf.get("lot_no", "")) or "") if jf.get("lot_no") else "",
        })
    return out


# ══════════════════════ 归一化 / 分类 / 过滤 ══════════════════════════════
def classify_period(text: str) -> str:
    for name, rx in PERIOD_RULES:
        if rx.search(text):
            return name
    return "未标注"


def classify_material(text: str) -> str:
    for name, rx in MATERIAL_RULES:
        if rx.search(text):
            return name
    return "未标注"


def parse_money(text: str):
    if not text:
        return "", None, None
    m = CURRENCY_RE.search(text)
    if not m:
        return "", None, None
    cur = m.group(1).upper()
    cur = CUR_MAP.get(m.group(1), cur)
    nums = re.findall(r"[\d][\d\s.,']*", text)
    vals = []
    for n in nums[:2]:
        n = n.replace(" ", "").replace("'", "")
        # 1,234.56 / 1.234,56 两种写法
        if re.search(r",\d{3}", n) or (n.count(".") <= 1 and n.count(",") == 1 and len(n.split(",")[-1]) != 3):
            n = n.replace(",", "") if re.search(r",\d{3}", n) else n.replace(",", ".")
        else:
            n = n.replace(".", "").replace(",", ".") if n.count(".") > 1 else n.replace(",", "")
        try:
            vals.append(float(n))
        except ValueError:
            pass
    lo = vals[0] if vals else None
    hi = vals[1] if len(vals) > 1 else None
    return cur, lo, hi


def parse_end(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%d %B %Y", "%d %b %Y",
                "%B %d, %Y", "%b %d, %Y"):
        try:
            dt = datetime.strptime(t[:len(datetime.now().strftime(fmt)) + 8].strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            continue
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", t)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc).isoformat()
    return ""


def is_target(title: str, query: str) -> tuple[bool, str]:
    """返回 (是否收录, 原因)。用户口径：中国古玉含翡翠，清代及以前，海外拍行。"""
    t = title or ""
    if not JADE_RE.search(t):
        return False, "no-jade-term"
    # hardstone 太宽：必须另有中国信号
    if not re.search(r"\b(jade|jadeite|jadeit|nephrite|jadéite|feicui)\b|玉|翡翠", t, re.I):
        if not CHINA_RE.search(t):
            return False, "hardstone-only"
    china_ctx = bool(CHINA_RE.search(t)) or ("chin" in query.lower()) or ("jade" in query.lower() and "chinese" in query.lower())
    if not china_ctx:
        return False, "not-chinese"
    if MODERN_RE.search(t):
        return False, "modern-period"
    period = classify_period(t)
    if period not in ALLOWED_PERIODS:
        return False, f"period-{period}"
    return True, "ok"


def make_lot(raw: dict, src: dict, query: str, strategy: str) -> Lot | None:
    title = re.sub(r"\s+", " ", raw.get("title", "")).strip()
    url = raw.get("url", "").strip()
    if not (title and url):
        return None
    cur, lo, hi = parse_money(raw.get("price_text", "") or "")
    text = title + " " + (raw.get("price_text") or "")
    return Lot(
        id=hashlib.sha1(url.encode("utf-8")).hexdigest()[:16],
        source=src["id"], house=(raw.get("house") or src["name"]).strip(),
        region=src.get("region", "其他"), country=src.get("country", ""),
        title=title[:300], url=url, image=raw.get("image", "") or "",
        price_text=(raw.get("price_text") or "").strip()[:80],
        currency=cur, est_low=lo, est_high=hi,
        end_ts=parse_end(raw.get("end", "")),
        lot_no=(raw.get("lot_no") or "").strip()[:20],
        period=classify_period(title), material=classify_material(text),
        query=query, strategy=strategy,
        scraped_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


# ══════════════════════════ 抓取一个源 ════════════════════════════════════
def run_source(src: dict, probe_only: bool = False) -> tuple[list[Lot], SourceHealth, list[str]]:
    health = SourceHealth(id=src["id"], name=src["name"], region=src.get("region", "其他"))
    lots: list[Lot] = []
    samples: list[str] = []
    queries = src.get("queries", ["chinese jade"])
    pages = int(src.get("pages", 1))
    if probe_only:                      # 探测只打一枪，日志才读得完
        queries, pages = queries[:1], 1
    strat_used = set()

    for q in queries:
        for page in range(1, pages + 1):
            tpl = src.get("probe_url") if (probe_only and src.get("probe_url")) else src["url"]
            url = (tpl.replace("{q}", quote_plus(q))
                      .replace("{q_raw}", q)
                      .replace("{page}", str(page)))
            use_browser = bool(src.get("browser"))
            try:
                if use_browser:
                    r = BROWSER.get(url, src.get("wait_selector", ""),
                                    timeout=int(src.get("timeout", 45)) * 1000)
                    if not r.text:
                        health.http.append(f"{q}|p{page}: 浏览器不可用")
                        continue
                else:
                    r = fetch(url, timeout=int(src.get("timeout", 30)),
                              extra_headers=src.get("headers"),
                              referer=src.get("home", ""))
            except Exception as e:                               # noqa: BLE001
                health.http.append(f"{q}|p{page}: EXC {type(e).__name__}")
                continue

            ct = (r.headers.get("content-type") or "").split(";")[0]
            health.http.append(f"{q}|p{page}: {r.status_code} {ct} {len(r.content)}B"
                               f"{' [browser]' if use_browser else ''}")

            if probe_only:
                body = r.text
                flags = []
                if re.search(r"cloudflare|cf-browser-verification|Just a moment", body[:6000], re.I):
                    flags.append("CLOUDFLARE")
                if re.search(r"captcha|px-captcha|perimeterx|datadome", body[:6000], re.I):
                    flags.append("BOT-WALL")
                if "__NEXT_DATA__" in body:
                    flags.append("NEXT_DATA")
                if "application/ld+json" in body:
                    flags.append("JSON-LD")
                jade_hits = len(re.findall(r"jade", body, re.I))
                counts, examples = {}, []
                if r.status_code < 400:
                    soup = BeautifulSoup(body, "lxml")
                    for fn, nm in ((parse_configured, "configured"),
                                   (parse_jsonld, "jsonld"),
                                   (parse_links, "links")):
                        try:
                            got = fn(soup, src, url)
                        except Exception as e:                   # noqa: BLE001
                            got = []
                            flags.append(f"{nm}-ERR:{type(e).__name__}")
                        counts[nm] = len(got)
                        if got and not examples:
                            examples = [g["title"][:90] for g in got[:3]]
                    if src.get("method") == "json" or ct == "application/json":
                        try:
                            counts["json"] = len(parse_json_api(r.json(), src, url))
                        except Exception:                        # noqa: BLE001
                            counts["json"] = -1
                shapes = []
                if r.status_code < 400 and "html" in ct:
                    try:
                        shapes = href_shapes(BeautifulSoup(body, "lxml"), url)
                    except Exception:                            # noqa: BLE001
                        shapes = []
                health.probe = {
                    "http": r.status_code, "ct": ct, "bytes": len(r.content),
                    "jade_mentions": jade_hits, "flags": flags,
                    "counts": counts, "examples": examples, "url": url,
                    "shapes": shapes,
                }
                shp = "\n".join(f"      {n:>4}×  {sh}\n            例: {ex[:110]}\n            文: {tx}"
                                for sh, n, ex, tx in shapes)
                samples.append(
                    f"\n{'='*90}\n[{src['id']}] {url}\n  HTTP {r.status_code} {ct} "
                    f"{len(r.content)}B  jade_mentions={jade_hits}  flags={','.join(flags) or '-'}\n"
                    f"  parsers={counts}  examples={examples}\n"
                    f"  站内链接形态 TOP：\n{shp or '      （无）'}\n")
                continue

            if r.status_code >= 400:
                continue

            raws, strategy = [], ""
            if src.get("method") == "json" or ct == "application/json":
                try:
                    raws = parse_json_api(r.json(), src, url)
                    strategy = "json"
                except Exception as e:                           # noqa: BLE001
                    health.note = f"json parse: {type(e).__name__}"
            if not raws:
                soup = BeautifulSoup(r.text, "lxml")
                for fn, name in ((parse_configured, "configured"),
                                 (parse_jsonld, "jsonld"),
                                 (parse_links, "links")):
                    try:
                        raws = fn(soup, src, url)
                    except Exception as e:                       # noqa: BLE001
                        health.note = f"{name}: {type(e).__name__}"
                        raws = []
                    if raws:
                        strategy = name
                        break
            if not raws:
                continue
            strat_used.add(strategy)
            health.lots += len(raws)
            for raw in raws:
                keep, _why = is_target(raw.get("title", ""), q)
                if not keep:
                    continue
                lot = make_lot(raw, src, q, strategy)
                if lot:
                    lots.append(lot)
            time.sleep(float(src.get("delay", 1.0)))

    health.strategy = "+".join(sorted(strat_used))
    health.kept = len(lots)
    health.ok = bool(lots) or (probe_only and bool(health.http))
    return lots, health, samples


# ══════════════════════════════ 主入口 ═══════════════════════════════════
def main(argv):
    probe_only = "--probe" in argv
    only = None
    for a in argv:
        if a.startswith("--only="):
            only = [x.strip() for x in a.split("=", 1)[1].split(",") if x.strip()]

    sources = load_sources(only)
    log(f"▶ {'PROBE' if probe_only else 'SCRAPE'} · {len(sources)} 个源 · "
        f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}")

    all_lots: list[Lot] = []
    healths: list[SourceHealth] = []
    all_samples: list[str] = []

    for src in sources:
        t0 = time.time()
        try:
            lots, health, samples = run_source(src, probe_only)
        except Exception:                                        # noqa: BLE001
            log(f"  ✖ {src['id']} 崩溃:\n{traceback.format_exc()}")
            healths.append(SourceHealth(id=src["id"], name=src["name"],
                                        region=src.get("region", "其他"),
                                        note="crashed"))
            continue
        all_lots.extend(lots)
        healths.append(health)
        all_samples.extend(samples)
        log(f"  {'✔' if health.kept else '·'} {src['id']:<16} "
            f"抓到 {health.lots:>4} 条 / 命中 {health.kept:>3} 条 "
            f"[{health.strategy or '-'}] {time.time()-t0:.1f}s  {health.http[:2]}")

    BROWSER.close()

    if probe_only:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, "probe.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(all_samples))
        log("\n\n" + "#" * 100 + "\n# 原始响应样本（各 1400 字符，用于校正选择器）\n" + "#" * 100)
        for smp in all_samples:
            log(smp)
        log("\n\n" + "#" * 100)
        log(f"# 探测诊断表  {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
        log("#" * 100)
        log(f"{'源':<18}{'HTTP':>5} {'字节':>9} {'jade':>6}  "
            f"{'cfg':>4}{'jsonld':>7}{'links':>6}{'json':>5}  标志 / 首条示例")
        log("-" * 100)
        for h in healths:
            p = h.probe or {}
            c = p.get("counts", {})
            ex = (p.get("examples") or [""])[0][:44]
            log(f"{h.id:<18}{str(p.get('http','-')):>5} {str(p.get('bytes','-')):>9} "
                f"{str(p.get('jade_mentions','-')):>6}  "
                f"{str(c.get('configured','-')):>4}{str(c.get('jsonld','-')):>7}"
                f"{str(c.get('links','-')):>6}{str(c.get('json','-')):>5}  "
                f"{','.join(p.get('flags') or []) or '-'} | {ex}")
        log("-" * 100)
        usable = [h.id for h in healths if (h.probe.get("counts") or {}) and
                  max((h.probe.get("counts") or {}).values() or [0]) > 0]
        log(f"可解析的源（至少一种策略有产出）：{len(usable)}/{len(healths)} → {', '.join(usable)}")
        return 0

    # 去重：同 URL 只留一条；同标题 + 同拍行 视为重复（聚合站与官网重复）
    seen_url, seen_key, uniq = set(), set(), []
    for lot in sorted(all_lots, key=lambda x: (x.image == "", x.end_ts == "")):
        key = (re.sub(r"[^a-z0-9]", "", lot.title.lower())[:60], lot.house.lower())
        if lot.url in seen_url or key in seen_key:
            continue
        seen_url.add(lot.url)
        seen_key.add(key)
        uniq.append(lot)

    uniq.sort(key=lambda x: (x.end_ts or "9999", x.house))
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "海外（中国大陆以外）拍卖行 · 中国古玉与翡翠 · 清代及以前",
        "count": len(uniq),
        "sources": [asdict(h) for h in healths],
        "lots": [asdict(x) for x in uniq],
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "lots.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    # file:// 直接双击打开时 fetch 会被 CORS 拦，故同时产出 JS 包裹版
    with open(os.path.join(DATA_DIR, "lots.js"), "w", encoding="utf-8") as f:
        f.write("window.__JADE_DATA__ = ")
        json.dump(payload, f, ensure_ascii=False)
        f.write(";\n")

    ok = sum(1 for h in healths if h.kept)
    log(f"\n■ 完成：{len(uniq)} 条拍品（去重前 {len(all_lots)}）· "
        f"{ok}/{len(healths)} 个源有产出")
    for h in healths:
        if not h.kept:
            log(f"    ⚠ 无产出 {h.id:<16} [{h.strategy or '-'}] {h.note} {h.http[:2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
