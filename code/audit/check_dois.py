import os
os.chdir(os.environ.get("GRC_MANUSCRIPT",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "manuscript")))
import json, re, time, urllib.request, urllib.parse, difflib

def norm(s):
    s = re.sub(r"\{|\}|\\[a-zA-Z]+", "", s or "")
    return re.sub(r"[^a-z0-9 ]", " ", s.lower()).split()

bib = open("refs.bib").read()
entries = re.findall(r"@\w+\{([^,]+),(.*?)\n\}", bib, re.S)
rows = []
for k, body in entries:
    m = re.search(r"doi\s*=\s*\{([^}]+)\}", body)
    if not m: continue
    t = re.search(r"title\s*=\s*\{(.+?)\},?\s*\n", body, re.S)
    rows.append((k.strip(), m.group(1).strip(),
                 " ".join(t.group(1).split()) if t else ""))

print(f"checking {len(rows)} DOIs against Crossref\n")
bad, mism, ok = [], [], 0
def doi_org_resolves(doi):
    # Not every registry (e.g. DataCite for arXiv DOIs like 10.48550/...) is
    # indexed by Crossref; a plain doi.org redirect check catches those.
    try:
        req = urllib.request.Request("https://doi.org/" + urllib.parse.quote(doi),
              headers={"User-Agent": "doi-audit/1.0 (mailto:ttdaiuneti@gmail.com)"}, method="HEAD")
        with urllib.request.urlopen(req, timeout=20) as r:
            return 200 <= r.status < 400
    except urllib.error.HTTPError as e:
        return 200 <= e.code < 400
    except Exception:
        return False

for k, doi, title in rows:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={"User-Agent": "doi-audit/1.0 (mailto:ttdaiuneti@gmail.com)"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            msg = json.load(r)["message"]
        reg = (msg.get("title") or [""])[0]
        a, b = norm(title), norm(reg)
        sim = difflib.SequenceMatcher(None, " ".join(a), " ".join(b)).ratio() if a and b else 0
        if sim < 0.65:
            mism.append((k, doi, title[:52], reg[:52], sim)); print(f"  MISMATCH {k:26s} {doi}")
        else:
            ok += 1
    except Exception as e:
        code = getattr(e, "code", str(e)[:28])
        if code == 404 and doi_org_resolves(doi):
            ok += 1
            print(f"  ok (non-Crossref registry) {k:26s} {doi}")
        else:
            bad.append((k, doi, title[:52], code)); print(f"  NOT FOUND({code}) {k:26s} {doi}")
    time.sleep(0.12)

print(f"\n== resolves & title matches : {ok}/{len(rows)}")
print(f"== DOI does not resolve     : {len(bad)}")
for k, d, t, c in bad: print(f"     {k:26s} {d:42s} [{c}]  bib title: {t}")
print(f"== resolves to a DIFFERENT paper : {len(mism)}")
for k, d, t, r, s in mism:
    print(f"     {k:26s} {d}\n        bib : {t}\n        real: {r}   (sim {s:.2f})")
