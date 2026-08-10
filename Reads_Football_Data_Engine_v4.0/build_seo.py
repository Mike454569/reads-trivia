"""Generate SEO metadata, internal-link graph and sitemap files for Reads v2.2."""
from pathlib import Path
import sqlite3,hashlib,html,json,sys
import growth_engine as G
ROOT=Path(__file__).parent
DB=ROOT/"reads_football_v4.0.sqlite"
OUT=ROOT/"seo_output"
BASE=G.BASE_URL

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def generate_sitemaps(chunk=45000):
    OUT.mkdir(exist_ok=True)
    c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
    rows=list(c.execute("SELECT entity_type,canonical_path,updated_at FROM seo_entities WHERE indexable=1 ORDER BY entity_type,canonical_path"))
    files=[]
    for i in range(0,len(rows),chunk):
        part=rows[i:i+chunk];fn=OUT/f"sitemap-{i//chunk+1}.xml"
        body=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for r in part:
            body+=["<url>",f"<loc>{html.escape(BASE+r['canonical_path'])}</loc>",f"<lastmod>{str(r['updated_at'])[:10]}</lastmod>","</url>"]
        body.append("</urlset>");fn.write_text("\n".join(body),encoding="utf-8")
        sid=f"SITEMAP:{i//chunk+1}"
        c.execute("INSERT OR REPLACE INTO sitemap_registry VALUES(?,?,CURRENT_TIMESTAMP,?,?,?)",
                  (sid,"MIXED",len(part),fn.name,sha(fn)));files.append(fn)
    index=OUT/"sitemap-index.xml"
    b=['<?xml version="1.0" encoding="UTF-8"?>','<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for f in files:b+=["<sitemap>",f"<loc>{BASE}/{f.name}</loc>","</sitemap>"]
    b.append("</sitemapindex>");index.write_text("\n".join(b),encoding="utf-8")
    c.commit();c.close()
    return {"urls":len(rows),"files":[x.name for x in files],"index":index.name}

def main():
    entities=G.build_seo_entities()
    links=G.rebuild_internal_links()
    maps=generate_sitemaps()
    print(json.dumps({"entities":entities,"internal_links":links,"sitemaps":maps},indent=2))

if __name__=="__main__":main()
