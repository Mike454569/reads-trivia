
"""
Reads Football Graph Explorer / Six Degrees engine.

Examples:
python graph_explorer.py search "New England Patriots"
python graph_explorer.py path team NE team GB
python graph_explorer.py random-six 2026-08-07
"""
from pathlib import Path
import sqlite3, json, collections, hashlib, random, sys

DB=Path(__file__).with_name("reads_football_v4.0.sqlite")

def connect():
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    return c

def label(c,node_type,node_id):
    r=c.execute("SELECT display_name FROM graph_nodes WHERE node_type=? AND node_id=?",(node_type,node_id)).fetchone()
    return r[0] if r and r[0] else node_id

def search(query,limit=20):
    c=connect()
    rows=[dict(r) for r in c.execute("""
        SELECT node_type,node_id,display_name,popularity_score
        FROM graph_nodes
        WHERE lower(display_name) LIKE ?
        ORDER BY popularity_score DESC,display_name
        LIMIT ?
    """,(f"%{query.lower()}%",limit))]
    c.close()
    return rows

def shortest_path(start_type,start_id,end_type,end_id,max_depth=6):
    c=connect()
    # Fast use cache where possible.
    cached=c.execute("""
        SELECT path_json FROM graph_path_cache
        WHERE start_type=? AND start_id=? AND end_type=? AND end_id=? AND max_depth>=?
        ORDER BY max_depth LIMIT 1
    """,(start_type,start_id,end_type,end_id,max_depth)).fetchone()
    if cached:
        path=json.loads(cached[0])
        for e in path:
            e["from_name"]=label(c,e["from_type"],e["from_id"])
            e["to_name"]=label(c,e["to_type"],e["to_id"])
        c.close()
        return path

    q=collections.deque([((start_type,start_id),[])])
    seen={(start_type,start_id)}
    while q:
        node,path=q.popleft()
        if len(path)>=max_depth:
            continue
        outgoing=c.execute("""
            SELECT predicate,object_type,object_id FROM graph_edges
            WHERE subject_type=? AND subject_id=? AND verification_status NOT IN ('AUTO_REVIEW','CONFLICT')
        """,node).fetchall()
        incoming=c.execute("""
            SELECT predicate,subject_type,subject_id FROM graph_edges
            WHERE object_type=? AND object_id=? AND verification_status NOT IN ('AUTO_REVIEW','CONFLICT')
        """,node).fetchall()

        nxts=[(r["predicate"],r["object_type"],r["object_id"]) for r in outgoing]
        nxts += [("REVERSE:"+r["predicate"],r["subject_type"],r["subject_id"]) for r in incoming]

        for pred,nt,nid in nxts:
            nxt=(nt,nid)
            edge={
                "from_type":node[0],"from_id":node[1],"from_name":label(c,*node),
                "predicate":pred,
                "to_type":nt,"to_id":nid,"to_name":label(c,nt,nid)
            }
            np=path+[edge]
            if nxt==(end_type,end_id):
                c.close(); return np
            if nxt not in seen:
                seen.add(nxt); q.append((nxt,np))
    c.close()
    return None

def random_six(seed="daily",min_len=2,max_len=4):
    c=connect()
    rows=list(c.execute("""
        SELECT start_type,start_id,end_type,end_id,path_length,path_json
        FROM graph_path_cache WHERE path_length BETWEEN ? AND ?
    """,(min_len,max_len)))
    if not rows:
        c.close(); return None
    h=int(hashlib.sha256(str(seed).encode()).hexdigest()[:16],16)
    r=rows[h%len(rows)]
    start_name=label(c,r["start_type"],r["start_id"])
    end_name=label(c,r["end_type"],r["end_id"])
    path=json.loads(r["path_json"])
    c.close()
    return {
        "mode":"six_degrees",
        "start":{"type":r["start_type"],"id":r["start_id"],"name":start_name},
        "end":{"type":r["end_type"],"id":r["end_id"],"name":end_name},
        "par":r["path_length"],
        "prompt":f"Connect {start_name} to {end_name} in {r['path_length']} moves or fewer.",
        "solution_path":path,
        "verification_status":"SOURCE_BACKED_OR_DERIVED"
    }

if __name__=="__main__":
    if len(sys.argv)>=3 and sys.argv[1]=="search":
        print(json.dumps(search(" ".join(sys.argv[2:])),indent=2))
    elif len(sys.argv)==6 and sys.argv[1]=="path":
        print(json.dumps(shortest_path(*sys.argv[2:],max_depth=6),indent=2))
    else:
        seed=sys.argv[2] if len(sys.argv)>2 and sys.argv[1]=="random-six" else "2026-08-07"
        print(json.dumps(random_six(seed),indent=2))
