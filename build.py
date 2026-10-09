#!/usr/bin/env python3
"""The Semigroup Gazette: prints a fresh index.html each run. Standard library only."""
import csv, datetime as dt, html, io, json, os, re, sys, time
import urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

# ---- Things you may want to edit -------------------------------------------
TITLE = "The Semigroup Gazette"
DEDICATION = "Printed each morning for the finest semigroup theorist in the house, with love."
FIRST_EDITION = dt.date(2026, 10, 9)   # edition No. 1
CATS = "math.GR math.RA math.CO math.LO math.CT math.AC math.NT cs.FL cs.LO".split()
TAGS = {
    "Inverse": ["inverse semigroup", "inverse monoid"],
    "Regular": ["regular semigroup", "completely regular", "orthodox"],
    "Transformation": ["transformation"],
    "Numerical": ["numerical semigroup", "numerical monoid"],
    "Varieties & identities": ["variety", "varieties", "identit", "pseudovariet", "universal algebra", "equational"],
    "Congruences": ["congruence"],
    "Automata & languages": ["automat", "rational language", "regular language", "rewriting"],
    "Semigroup algebras": ["semigroup algebra", "semigroup ring", "monoid algebra"],
    "Finite": ["finite semigroup", "finite monoid"],
}
# city, currency code, symbol
CITIES = [("Lisbon & Berlin", "EUR", "€"), ("London", "GBP", "£"), ("São Paulo", "BRL", "R$"),
          ("Tokyo", "JPY", "¥"), ("Vancouver", "CAD", "C$"), ("Zürich", "CHF", "CHF ")]
# name, Stooq symbol, Yahoo symbol, unit label, price -> USD per kg
COFFEES = [("Arabica", "kc.f", "KC=F", "US¢/lb", lambda p: p / 100 / 0.45359237),
           ("Robusta", "rc.f", None, "US$/tonne", lambda p: p / 1000)]
LEXICON = [
 ("Green's relations", "On a semigroup S: a R b iff aS¹ = bS¹, a L b iff S¹a = S¹b, H = R ∩ L, D = R∘L = L∘R, and a J b iff S¹aS¹ = S¹bS¹. The egg-box picture of a D-class comes from them."),
 ("Rees quotient", "For an ideal I of S, the quotient S/I collapses all of I to a single zero and leaves every other element alone."),
 ("Vagner–Preston theorem", "Every inverse semigroup embeds in the symmetric inverse monoid on some set, the analogue of Cayley's theorem."),
 ("Cayley for semigroups", "Every semigroup S embeds in the full transformation semigroup on S¹, acting by right translations."),
 ("Regular elements", "An element a is regular if a = axa for some x. Inverse semigroups are the regular ones in which every element has a unique inverse."),
 ("Natural partial order", "On the idempotents E(S): e ≤ f iff ef = fe = e. For inverse semigroups it extends to all of S."),
 ("Numerical semigroups", "Cofinite submonoids of (ℕ, +). The Frobenius number is the largest integer outside; the genus counts the gaps."),
 ("Krohn–Rhodes theorem", "Every finite semigroup divides an iterated wreath product of finite simple groups and the three-element flip-flop monoid."),
 ("Eilenberg correspondence", "Pseudovarieties of finite monoids correspond bijectively to varieties of regular languages: algebra meets automata."),
 ("Birkhoff's HSP theorem", "A class of algebras is equationally definable iff it is closed under homomorphic images, subalgebras and products."),
 ("Mal'cev terms", "A variety has a term p with p(x,y,y) = x = p(y,y,x) iff its congruences permute."),
 ("Word problem", "Deciding whether two words are equal in a finitely presented semigroup is undecidable in general (Markov and Post, 1947)."),
 ("Rees matrix semigroups", "The Rees–Suschkewitsch theorem: completely simple semigroups are exactly the Rees matrix semigroups M[G; I, Λ; P] over a group G."),
]
PROBLEMS = [
 ("An idempotent in every finite semigroup", "Show that every finite semigroup contains an idempotent.",
  "Take any a. Two of a, a², a³, … coincide, so a^m = a^(m+p) for some m, p ≥ 1. Choose n ≥ m that is a multiple of p. Then a^(2n) = a^n, so a^n is idempotent."),
 ("Idempotents in T₃", "How many idempotents does the full transformation monoid on {1, 2, 3} have?",
  "An idempotent fixes its image pointwise. Choose an image of size k and send the other 3 − k points anywhere inside it: Σ C(3,k)·k^(3−k) = 3 + 6 + 1 = 10."),
 ("A Frobenius number", "Find the Frobenius number and the genus of the numerical semigroup ⟨3, 5⟩.",
  "Its elements are 0, 3, 5, 6, 8, 9, 10, … The gaps are 1, 2, 4, 7, so the Frobenius number is 7 and the genus is 4. In general ⟨a, b⟩ has Frobenius number ab − a − b."),
 ("Two inverses agree", "In a monoid, a has a left inverse l (la = 1) and a right inverse r (ar = 1). Show that l = r.",
  "l = l(ar) = (la)r = r."),
 ("Semigroups of order 2", "Up to isomorphism, how many semigroups have exactly two elements? Name them.",
  "Five: the cyclic group of order 2, the two-element semilattice, the left-zero semigroup, the right-zero semigroup, and the null semigroup (every product equals one element 0)."),
 ("Counting partial bijections", "How many elements does the symmetric inverse monoid I₂ have?",
  "Count partial bijections of {1, 2} by domain size k: Σ C(2,k)²·k! = 1 + 4 + 2 = 7."),
 ("Cancellative means group", "Show that a finite cancellative semigroup is a group.",
  "For fixed a, x ↦ ax is injective, hence bijective, so ax = b is always solvable; likewise xa = b. Pick e with ae = a. For any b, solve ya = b; then be = yae = ya = b, so e is a right identity. Symmetrically there is a left identity f, and f = fe = e. Solving ax = e gives inverses."),
 ("Brandt idempotents", "The Brandt semigroup B_n consists of the n² matrix units e_ij and a zero, with e_ij e_kl = e_il if j = k and 0 otherwise. How many idempotents does it have?",
  "e_ij e_ij = e_ij only when i = j; otherwise the product is 0. The idempotents are the n elements e_ii and 0: n + 1 in all."),
]
UA = {"User-Agent": "SemigroupGazette/1.0 (personal gift project)"}
esc = html.escape

def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            print(f"fetch failed ({e}): {url}", file=sys.stderr)
            time.sleep(3 * (i + 1))
    return None

def fetch_papers(n=40):
    query = ("(ti:semigroup OR ti:semigroups OR abs:semigroup OR abs:semigroups) AND ("
             + " OR ".join("cat:" + c for c in CATS) + ")")
    q = urllib.parse.urlencode({"search_query": query, "sortBy": "submittedDate",
                                "sortOrder": "descending", "max_results": n})
    xml = get("https://export.arxiv.org/api/query?" + q)
    if not xml:
        return []
    ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    out = []
    for e in ET.fromstring(xml).findall("a:entry", ns):
        txt = lambda tag, e=e: re.sub(r"\s+", " ", e.findtext(tag, "", ns)).strip()
        pc = e.find("x:primary_category", ns)
        out.append({"title": txt("a:title"), "abs": txt("a:summary"),
                    "url": txt("a:id").replace("http://", "https://"), "date": txt("a:published")[:10],
                    "authors": [a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)],
                    "cat": pc.get("term") if pc is not None else ""})
    return out

def tags_for(p):
    text = (p["title"] + " " + p["abs"]).lower()
    return [k for k, words in TAGS.items() if any(w in text for w in words)]

def byline(p):
    au = ", ".join(p["authors"][:4]) + (" et al." if len(p["authors"]) > 4 else "")
    return f'{esc(au)}. <i>{esc(p["cat"])}, submitted {p["date"]}</i>'

def chips_html(p):
    return "".join(f'<span class="tag">{esc(t)}</span>' for t in tags_for(p))

def card(p):
    return (f'<article class="paper" data-tags="{esc("|".join(tags_for(p)))}">'
            f'<h3><a href="{p["url"]}">{esc(p["title"])}</a></h3><p class="by">{byline(p)}</p>'
            f'<div>{chips_html(p)}</div>'
            f'<details><summary>Read the abstract</summary><p>{esc(p["abs"])}</p></details></article>')

def lead(p):
    return (f'<article class="lead"><p class="kicker"><i>Our leading dispatch</i></p>'
            f'<h2><a href="{p["url"]}">{esc(p["title"])}</a></h2><p class="by">{byline(p)}</p>'
            f'<div class="abs">{esc(p["abs"])}</div><div>{chips_html(p)}</div></article>')

def stooq(sym):
    txt = get(f"https://stooq.com/q/d/l/?s={sym}&i=d", tries=2)
    rows = [r for r in csv.DictReader(io.StringIO(txt or "")) if r.get("Close")]
    return (float(rows[-1]["Close"]), float(rows[-2]["Close"])) if len(rows) > 1 else None

def yahoo(sym):
    txt = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=10d&interval=1d", tries=2)
    c = [x for x in json.loads(txt)["chart"]["result"][0]["indicators"]["quote"][0]["close"] if x]
    return (c[-1], c[-2]) if len(c) > 1 else None

def quote(stq, yah):
    for fn, sym in ((stooq, stq), (yahoo, yah)):
        if sym:
            try:
                r = fn(sym)
                if r:
                    return r
            except Exception as e:
                print(f"quote failed ({e}): {sym}", file=sys.stderr)
    return None

def fx():
    syms = ",".join(c for _, c, _ in CITIES)
    for u in (f"https://api.frankfurter.dev/v1/latest?base=USD&symbols={syms}",
              f"https://api.frankfurter.app/latest?from=USD&to={syms}"):
        try:
            return json.loads(get(u, tries=2))["rates"]
        except Exception:
            pass
    return None

def coffee_html():
    found = []
    for name, stq, yah, unit, to_kg in COFFEES:
        q = quote(stq, yah)
        if q:
            found.append((name, unit, q[0], q[1], to_kg(q[0])))
    if not found:
        return '<p class="muted">The telegraph wire is down. No quotations reached us today.</p>'
    out = ""
    for name, unit, last, prev, _ in found:
        ch = (last - prev) / prev * 100
        cls, arrow = ("up", "▲") if ch > 0 else ("dn", "▼") if ch < 0 else ("", "–")
        out += (f'<p class="quote"><b>{name}</b> {last:,.2f} {unit} '
                f'<span class="chg {cls}">{arrow} {abs(ch):.2f}%</span></p>')
    rates = fx()
    if rates:
        out += "<table><tr><th>Per kilogram</th>" + "".join(f"<th>{f[0]}</th>" for f in found) + "</tr>"
        for city, cur, sym in CITIES:
            if cur in rates:
                d = 0 if cur == "JPY" else 2
                out += f"<tr><td>{city}</td>" + "".join(f"<td>{sym}{f[4] * rates[cur]:,.{d}f}</td>" for f in found) + "</tr>"
        out += "</table>"
        if "EUR" in rates:
            out += f'<p class="cup">The beans in one 18 g espresso cost about <b>€{found[0][4] * rates["EUR"] * 0.018:.2f}</b>.</p>'
    out += '<p class="muted">Wholesale green-bean futures, last close. Not what the café charges you.</p>'
    return out

VOID = {"br", "img", "hr", "input", "meta", "link", "wbr"}
SAFE = lambda t: re.sub(r"\son\w+=(\"[^\"]*\"|'[^']*')", "", t)

class Figs(HTMLParser):
    def __init__(self):
        super().__init__(); self.figs = []; self.cur = None; self.depth = 0; self.cap = False
        self.base = None; self.sv = None; self.nest = 0; self.skip = 0
    def handle_starttag(self, tag, a):
        a = dict(a)
        if self.sv is not None or (tag == "svg" and self.depth):
            if self.sv is None: self.sv, self.nest, self.skip = [], 0, 0
            if tag not in VOID: self.nest += 1
            if tag in ("script", "style"): self.skip += 1
            elif not self.skip: self.sv.append(SAFE(self.get_starttag_text()))
            return
        if tag == "base" and a.get("href"): self.base = a["href"]
        elif tag == "figure":
            if self.depth == 0: self.cur = {"imgs": [], "svgs": [], "cap": ""}
            self.depth += 1
        elif self.depth and tag == "img" and a.get("src") and "ltx_Math" not in (a.get("class") or ""):
            self.cur["imgs"].append(a["src"])
        elif self.depth and tag == "figcaption": self.cap = True
    def handle_endtag(self, tag):
        if self.sv is not None:
            if tag not in VOID: self.nest -= 1
            if tag in ("script", "style"): self.skip -= 1
            elif not self.skip and tag not in VOID and not (self.sv and self.sv[-1].endswith("/>")):
                self.sv.append(f"</{tag}>")
            if self.nest <= 0:
                self.cur["svgs"].append("".join(self.sv)); self.sv = None
            return
        if tag == "figcaption": self.cap = False
        elif tag == "figure" and self.depth:
            self.depth -= 1
            if self.depth == 0: self.figs.append(self.cur)
    def handle_data(self, d):
        if self.sv is not None:
            if not self.skip: self.sv.append(esc(d))
        elif self.cap and self.cur is not None: self.cur["cap"] += d

KEYS = ["cayley graph", "diagram", "hasse", "egg-box", "eggbox", "automaton", "graph", "lattice", "quiver", "tree", "picture"]

def diagram_html(papers):
    best, pages, nfig = None, 0, 0
    off = dt.datetime.now(dt.timezone.utc).date().toordinal() % max(1, len(papers))
    for p in (papers[off:] + papers[:off])[:25]:
        idv = p["url"].rsplit("/abs/", 1)[-1]
        txt = get(f"https://arxiv.org/html/{idv}", tries=1)
        if not txt: continue
        pages += 1
        fp = Figs()
        try: fp.feed(txt)
        except Exception: continue
        base = urllib.parse.urljoin("https://arxiv.org", fp.base) if fp.base else f"https://arxiv.org/html/{idv}/"
        for f in fp.figs:
            nfig += 1
            imgs = [s for s in f["imgs"] if (s.startswith("data:image/") and len(s) < 300000) or re.search(r"\.(png|jpe?g|gif|svg|webp)(\?|$)", s, re.I)]
            svgs = [s for s in f["svgs"] if 400 < len(s) < 200000]
            cap = re.sub(r"\s+", " ", f["cap"]).strip()
            score = sum(k in cap.lower() for k in KEYS)
            vis = ("img", urllib.parse.urljoin(base, imgs[0])) if imgs else ("svg", svgs[0]) if svgs else None
            if vis and (best is None or score > best[0]):
                best = (score, p, vis, cap)
        if best and best[0] >= 2: break
        time.sleep(1)
    print(f"diagram scan: {pages} pages, {nfig} figures, found={bool(best)}", file=sys.stderr)
    os.makedirs("archive", exist_ok=True)
    path, fresh = "archive/diagram.json", True
    if best:
        _, p, (kind, payload), cap = best
        d = {"kind": kind, "src": payload, "cap": cap[:260], "title": p["title"], "url": p["url"], "by": byline(p)}
        save(path, json.dumps(d, ensure_ascii=False))
    else:
        fresh = False
        try:
            with open(path, encoding="utf-8") as f: d = json.load(f)
        except Exception:
            return f'<section class="diagram"><p class="muted">No diagram turned up in today&rsquo;s papers (checked {pages} pages and {nfig} figures). One will appear as soon as a recent paper offers one.</p></section>'
    label = "The Diagram of the Day." if fresh else "The Diagram from a Recent Edition."
    vis = (f'<div class="svgbox">{d["src"]}</div>' if d.get("kind") == "svg"
           else f'<img src="{esc(d["src"])}" alt="{esc(d["cap"][:150])}" loading="lazy">')
    return (f'<section class="diagram"><figure>{vis}'
            f'<figcaption><b>{label}</b> {esc(d["cap"])} From <a href="{d["url"]}">{esc(d["title"])}</a>, '
            f'{d["by"]}. Image courtesy of the authors, via arXiv.</figcaption></figure></section>')

def news_html():
    qs = [("Mathematics and AI", 'mathematics ("artificial intelligence" OR AI) when:14d'),
          ("Across mathematics", 'mathematicians (theorem OR proof OR prize OR discovery) when:14d')]
    cols = ""
    for head, q in qs:
        xml = get("https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q, "hl": "en", "gl": "US", "ceid": "US:en"}), tries=2)
        li, seen = "", set()
        try:
            for it in ET.fromstring(xml).iter("item"):
                src = it.findtext("source", "")
                t = it.findtext("title", "")
                if src and t.endswith(" - " + src): t = t[:-len(src) - 3]
                if t.lower() in seen: continue
                seen.add(t.lower())
                li += f'<li><a href="{esc(it.findtext("link", ""))}">{esc(t)}</a> <i>{esc(src)}, {esc(it.findtext("pubDate", "")[:16])}</i></li>'
                if len(seen) == 6: break
        except Exception as e:
            print(f"news failed ({e})", file=sys.stderr)
        cols += f'<div><h4>{head}</h4><ul>{li or "<li class=muted>No headlines reached us today.</li>"}</ul></div>'
    return f'<section class="news"><h3>The Wider World</h3><div class="cols">{cols}</div><p class="muted">Headlines link to their publishers.</p></section>'

def nav(root):
    return f'<nav class="nav"><a href="{root}">Today&rsquo;s edition</a><a href="{root}archive/">Archive</a></nav>'

def save(path, text):
    with open(path, "w", encoding="utf-8") as f: f.write(text)

def archive_page(eds):
    css = re.search(r"<style>.*?</style>", TEMPLATE, re.S).group(0)
    fonts = re.search(r'<link href="https://fonts[^>]*>', TEMPLATE).group(0)
    rows = "".join(f'<li><a href="{e["date"]}.html"><b>No. {e["no"]}</b>, {e["date"]}</a>. Lead: {esc(e["lead"])}</li>'
                   for e in sorted(eds, key=lambda e: e["date"], reverse=True))
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>Archive, {esc(TITLE)}</title>{fonts}{css}</head><body><div class="page"><header><h1>{esc(TITLE)}</h1>'
            f'<p class="sub">The archive of past editions</p>{nav("../")}</header><ul class="arch">{rows}</ul></div></body></html>')

def wide_pool(recent):
    time.sleep(3)  # be polite to the arXiv API
    return fetch_papers(100) or recent

def main():
    today = dt.datetime.now(dt.timezone.utc).date()
    papers = fetch_papers()
    if not papers:
        sys.exit("arXiv unreachable: keeping the previous edition.")
    n = today.day
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    lex = LEXICON[today.toordinal() % len(LEXICON)]
    prob = PROBLEMS[today.toordinal() % len(PROBLEMS)]
    chips = '<button class="chip on" data-tag="">All</button>' + "".join(
        f'<button class="chip" data-tag="{esc(t)}">{esc(t)}</button>' for t in TAGS)
    values = {
        "TITLE": esc(TITLE), "DEDICATION": esc(DEDICATION),
        "NO": str(max(1, (today - FIRST_EDITION).days + 1)),
        "DATE": f"{today:%A}, the {n}{suffix} of {today:%B}, {today:%Y}",
        "COUNT": str(len(papers)), "CHIPS": chips, "LEAD": lead(papers[0]),
        "PAPERS": "".join(card(p) for p in papers[1:]), "COFFEE": coffee_html(),
        "LEX_T": esc(lex[0]), "LEX_D": esc(lex[1]),
        "PROB_T": esc(prob[0]), "PROB_Q": esc(prob[1]), "PROB_A": esc(prob[2]),
        "NEWS": news_html(), "DIAGRAM": diagram_html(wide_pool(papers)),
    }
    base = TEMPLATE
    for k, v in values.items():
        base = base.replace("{{" + k + "}}", v)
    os.makedirs("archive", exist_ok=True)
    stamp = today.isoformat()
    save("index.html", base.replace("{{NAV}}", nav("./")))
    save(f"archive/{stamp}.html", base.replace("{{NAV}}", nav("../")))
    try:
        with open("archive/editions.json", encoding="utf-8") as f: eds = json.load(f)
    except Exception:
        eds = []
    eds = [e for e in eds if e["date"] != stamp] + [{"date": stamp, "no": values["NO"], "lead": papers[0]["title"]}]
    save("archive/editions.json", json.dumps(eds, ensure_ascii=False))
    save("archive/index.html", archive_page(eds))
    print("Edition printed:", len(papers), "papers")

TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&family=Playfair+Display:wght@700;900&family=Old+Standard+TT:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
<script>window.MathJax={tex:{inlineMath:[['$','$']]}}</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
:root{--desk:#c9b98f;--paper:#efe3c2;--ink:#2a2118;--soft:#6b5b45;--red:#7d2a1e;--green:#3f5a3a}
*{box-sizing:border-box}[hidden]{display:none!important}
body{margin:0;background:var(--desk);color:var(--ink);font:1.05rem/1.6 "Old Standard TT",Georgia,serif}
a{color:inherit;text-decoration-color:var(--red);text-underline-offset:3px}a:hover{color:var(--red)}
:focus-visible{outline:2px solid var(--red);outline-offset:2px}
.page{max-width:1120px;margin:1.2rem auto;padding:1.5rem clamp(1rem,3vw,2.5rem) 2rem;background:var(--paper);
 box-shadow:0 0 0 1px #00000022,0 6px 24px #3b2f1c55;background-image:radial-gradient(#0000 60%,#7a5c2a22 130%)}
header{text-align:center;border-bottom:4px double var(--ink);padding-bottom:.6rem}
h1{font:700 clamp(2.4rem,9vw,5.4rem)/1 "UnifrakturCook","Playfair Display",serif;margin:.2rem 0}
.sub{font-style:italic;margin:0 0 .6rem;color:var(--soft)}
.bar{display:flex;justify-content:space-between;gap:.5rem 1rem;flex-wrap:wrap;border-top:1px solid var(--ink);padding-top:.4rem;font-size:.95rem}
h2,h3,.side h3{font-family:"Playfair Display",serif;line-height:1.2}
.lead{padding:1.2rem 0;border-bottom:4px double var(--ink)}
.lead h2{font-size:clamp(1.6rem,4vw,2.5rem);margin:.2rem 0 .3rem;font-weight:900}
.lead h2 a,.paper h3 a{text-decoration:none}
.abs{column-width:20rem;column-gap:2rem;column-rule:1px solid var(--soft);text-align:justify;hyphens:auto}
.abs::first-letter{font:900 3.6rem/.8 "Playfair Display",serif;float:left;padding:.3rem .5rem 0 0;color:var(--red)}
.by{color:var(--soft);margin:.2rem 0 .6rem;font-size:.95rem}
.tag{display:inline-block;border:1px solid var(--soft);padding:0 .45rem;margin:0 .3rem .3rem 0;font-size:.82rem;font-style:italic}
.grid{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:2rem;margin-top:1rem}
.tools{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin-bottom:1rem}
#q{flex:1 1 14rem;font:inherit;padding:.45rem .7rem;background:#f8f1da;border:1px solid var(--ink)}
.chip{font:inherit;font-size:.9rem;padding:.25rem .7rem;background:none;border:1px solid var(--ink);cursor:pointer}
.chip.on{background:var(--ink);color:var(--paper)}
.papers{column-width:17rem;column-gap:2rem;column-rule:1px solid var(--soft)}
.paper{break-inside:avoid;padding-bottom:.9rem;margin-bottom:.9rem;border-bottom:1px dotted var(--soft)}
.paper h3{font-size:1.15rem;margin:0}
summary{cursor:pointer;color:var(--red);font-style:italic}details p{font-size:.95rem;text-align:justify;margin:.4rem 0 0}
.side>section{border:3px double var(--ink);padding:.8rem 1rem;margin-bottom:1.2rem}
.side h3{margin:0 0 .5rem;text-align:center;font-size:1.25rem}
.quote{margin:.2rem 0}.chg.up{color:var(--green)}.chg.dn{color:var(--red)}
table{width:100%;border-collapse:collapse;margin:.6rem 0;font-size:.95rem}
th,td{padding:.2rem .3rem;border-bottom:1px dotted var(--soft);text-align:right}th:first-child,td:first-child{text-align:left}
.muted{color:var(--soft);font-size:.85rem;font-style:italic}.cup{margin:.4rem 0}
footer{border-top:4px double var(--ink);margin-top:1.5rem;padding-top:.7rem;text-align:center;font-size:.9rem;color:var(--soft)}
.nav{display:flex;justify-content:center;gap:2rem;margin:.5rem 0 0;font-style:italic}
.diagram{border-bottom:4px double var(--ink);padding:1rem 0;text-align:center}
.diagram figure{margin:0}.diagram img{max-width:100%;max-height:26rem;background:#fffdf5;padding:.6rem;border:1px solid var(--ink)}
.svgbox{background:#fffdf5;padding:.6rem;border:1px solid var(--ink);overflow-x:auto}.svgbox svg{display:block;margin:auto;max-width:100%;height:auto;max-height:26rem}
.diagram figcaption{max-width:46rem;margin:.6rem auto 0;font-size:.95rem;text-align:left}
.news{border-top:4px double var(--ink);margin-top:1.5rem;padding-top:.8rem}.news h3{text-align:center;font-size:1.4rem;margin:0 0 .6rem}
.news .cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(18rem,1fr));gap:2rem}.news h4{margin:0 0 .4rem;font-family:"Playfair Display",serif}
.news ul,.arch{padding:0;list-style:none}.news li,.arch li{padding:.4rem 0;border-bottom:1px dotted var(--soft)}
@media(max-width:860px){.grid{grid-template-columns:1fr}.page{margin:0;box-shadow:none}}
</style></head><body><div class="page">
<header><h1>{{TITLE}}</h1><p class="sub">Dispatches from the frontiers of semigroup theory</p>
<div class="bar"><span>Vol. I, No. {{NO}}</span><span>{{DATE}}</span><span>Price one penny</span></div>{{NAV}}</header>
{{LEAD}}
{{DIAGRAM}}
<div class="grid"><main>
<div class="tools"><input id="q" type="search" placeholder="Search today's dispatches" aria-label="Search dispatches">{{CHIPS}}</div>
<div class="papers">{{PAPERS}}</div><p id="none" class="muted" hidden>No dispatch matches. Try another word or choose All.</p>
</main><aside class="side">
<section><h3>The Coffee Exchange</h3>{{COFFEE}}</section>
<section><h3>Problem of the Day</h3><p><b>{{PROB_T}}.</b> {{PROB_Q}}</p><details><summary>Show the solution</summary><p>{{PROB_A}}</p></details></section>
<section><h3>Lexicon of the Day</h3><p><b>{{LEX_T}}.</b> {{LEX_D}}</p></section>
</aside></div>
{{NEWS}}
<footer><p>{{DEDICATION}}</p><p>{{COUNT}} recent papers gathered from arXiv. Thank you to arXiv for use of its open access interoperability.</p></footer>
</div><script>
const q=document.getElementById('q'),chips=[...document.querySelectorAll('.chip')],papers=[...document.querySelectorAll('.paper')];let tag='';
function apply(){const s=q.value.toLowerCase();let n=0;papers.forEach(p=>{const ok=(!tag||p.dataset.tags.split('|').includes(tag))&&(!s||p.textContent.toLowerCase().includes(s));p.hidden=!ok;n+=ok});document.getElementById('none').hidden=n>0}
chips.forEach(c=>c.onclick=()=>{tag=c.dataset.tag;chips.forEach(x=>x.classList.toggle('on',x===c));apply()});q.oninput=apply;
</script></body></html>"""

if __name__ == "__main__":
    main()