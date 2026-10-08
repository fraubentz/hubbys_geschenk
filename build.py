#!/usr/bin/env python3
"""The Semigroup Gazette: prints a fresh index.html each run. Standard library only."""
import csv, datetime as dt, html, io, json, re, sys, time
import urllib.parse, urllib.request
import xml.etree.ElementTree as ET

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

def main():
    today = dt.datetime.now(dt.timezone.utc).date()
    papers = fetch_papers()
    if not papers:
        sys.exit("arXiv unreachable: keeping the previous edition.")
    n = today.day
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    lex = LEXICON[today.toordinal() % len(LEXICON)]
    chips = '<button class="chip on" data-tag="">All</button>' + "".join(
        f'<button class="chip" data-tag="{esc(t)}">{esc(t)}</button>' for t in TAGS)
    values = {
        "TITLE": esc(TITLE), "DEDICATION": esc(DEDICATION),
        "NO": str(max(1, (today - FIRST_EDITION).days + 1)),
        "DATE": f"{today:%A}, the {n}{suffix} of {today:%B}, {today:%Y}",
        "COUNT": str(len(papers)), "CHIPS": chips, "LEAD": lead(papers[0]),
        "PAPERS": "".join(card(p) for p in papers[1:]), "COFFEE": coffee_html(),
        "LEX_T": esc(lex[0]), "LEX_D": esc(lex[1]),
    }
    page = TEMPLATE
    for k, v in values.items():
        page = page.replace("{{" + k + "}}", v)
    open("index.html", "w", encoding="utf-8").write(page)
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
@media(max-width:860px){.grid{grid-template-columns:1fr}.page{margin:0;box-shadow:none}}
</style></head><body><div class="page">
<header><h1>{{TITLE}}</h1><p class="sub">Dispatches from the frontiers of semigroup theory</p>
<div class="bar"><span>Vol. I, No. {{NO}}</span><span>{{DATE}}</span><span>Price one penny</span></div></header>
{{LEAD}}
<div class="grid"><main>
<div class="tools"><input id="q" type="search" placeholder="Search today's dispatches" aria-label="Search dispatches">{{CHIPS}}</div>
<div class="papers">{{PAPERS}}</div><p id="none" class="muted" hidden>No dispatch matches. Try another word or choose All.</p>
</main><aside class="side">
<section><h3>The Coffee Exchange</h3>{{COFFEE}}</section>
<section><h3>Lexicon of the Day</h3><p><b>{{LEX_T}}.</b> {{LEX_D}}</p></section>
</aside></div>
<footer><p>{{DEDICATION}}</p><p>{{COUNT}} recent papers gathered from arXiv. Thank you to arXiv for use of its open access interoperability.</p></footer>
</div><script>
const q=document.getElementById('q'),chips=[...document.querySelectorAll('.chip')],papers=[...document.querySelectorAll('.paper')];let tag='';
function apply(){const s=q.value.toLowerCase();let n=0;papers.forEach(p=>{const ok=(!tag||p.dataset.tags.split('|').includes(tag))&&(!s||p.textContent.toLowerCase().includes(s));p.hidden=!ok;n+=ok});document.getElementById('none').hidden=n>0}
chips.forEach(c=>c.onclick=()=>{tag=c.dataset.tag;chips.forEach(x=>x.classList.toggle('on',x===c));apply()});q.oninput=apply;
</script></body></html>"""

if __name__ == "__main__":
    main()
