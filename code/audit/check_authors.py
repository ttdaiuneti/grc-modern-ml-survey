"""Audit the FIRST author of every DOI-bearing entry against Crossref."""
import os
os.chdir(os.environ.get("GRC_MANUSCRIPT",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "manuscript")))
import json, re, time, urllib.request, urllib.parse, unicodedata

def strip(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", s.lower())

bib = open("refs.bib").read()
rows = []
for k, body in re.findall(r"@\w+\{([^,]+),(.*?)\n\}", bib, re.S):
    d = re.search(r"doi\s*=\s*\{([^}]+)\}", body)
    a = re.search(r"author\s*=\s*\{(.+?)\}\s*,\s*\n", body, re.S)
    if d and a:
        rows.append((k.strip(), d.group(1).strip(), " ".join(a.group(1).split())))

print(f"checking first author of {len(rows)} entries\n")
bad, ok = [], 0
for k, doi, authors in rows:
    first = authors.split(" and ")[0]
    fam = strip(first.split(",")[0])
    try:
        req = urllib.request.Request("https://api.crossref.org/works/" + urllib.parse.quote(doi),
              headers={"User-Agent": "author-audit/1.0 (mailto:ttdaiuneti@gmail.com)"})
        with urllib.request.urlopen(req, timeout=25) as r:
            m = json.load(r)["message"]
    except Exception as e:
        print(f"  SKIP {k:26s} ({getattr(e,'code',e)})"); continue
    au = m.get("author") or []
    if not au:
        print(f"  NO-DATA {k:26s}"); continue
    reg_fam = strip(au[0].get("family", ""))
    reg_given = (au[0].get("given") or "").split()[0] if au[0].get("given") else ""
    if fam and reg_fam and fam == reg_fam:
        # surname matches; also compare given name when the bib supplies one
        bib_given = strip(first.split(",")[1]) if "," in first else ""
        if bib_given and reg_given and not strip(reg_given).startswith(bib_given[:3]) \
           and not bib_given.startswith(strip(reg_given)[:3]):
            bad.append((k, first, f"{au[0].get('family')}, {au[0].get('given')}", "given name"))
            print(f"  GIVEN-NAME {k:24s} bib '{first}' vs '{au[0].get('family')}, {au[0].get('given')}'")
        else:
            ok += 1
    else:
        bad.append((k, first, f"{au[0].get('family')}, {au[0].get('given')}", "surname"))
        print(f"  SURNAME    {k:24s} bib '{first}' vs '{au[0].get('family')}, {au[0].get('given')}'")
    time.sleep(0.12)

print(f"\n== first author correct : {ok}/{len(rows)}")
print(f"== first author WRONG   : {len(bad)}")
