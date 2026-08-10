"""Fetch and import current nflverse player/roster CSV releases.

Run in an environment with ordinary outbound HTTPS access:
  python fetch_nflverse_current.py --players --rosters 2020 2021 2022 2023 2024 2025 2026

Uses official nflverse-data release asset patterns consumed by nflreadr.
The importer preserves transactional/QA behavior in import_data.py.
"""
from pathlib import Path
import argparse, subprocess, sys, urllib.request, hashlib, json

ROOT=Path(__file__).parent
IMPORTS=ROOT/'imports'
IMPORTS.mkdir(exist_ok=True)
PLAYERS_URL='https://github.com/nflverse/nflverse-data/releases/download/players/players.csv'
ROSTER_URL='https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{season}.csv'

def download(url,path):
    req=urllib.request.Request(url,headers={'User-Agent':'Reads-Football-Data-Engine/1.6'})
    with urllib.request.urlopen(req,timeout=120) as r, open(path,'wb') as f:
        while True:
            chunk=r.read(1024*1024)
            if not chunk: break
            f.write(chunk)
    h=hashlib.sha256(path.read_bytes()).hexdigest()
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':h,'url':url}

def run_import(dataset,path):
    r=subprocess.run([sys.executable,str(ROOT/'import_data.py'),dataset,str(path)],capture_output=True,text=True)
    return {'code':r.returncode,'stdout':r.stdout.strip(),'stderr':r.stderr.strip()[-2000:]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--players',action='store_true')
    ap.add_argument('--rosters',nargs='*',type=int,default=None)
    a=ap.parse_args()
    results=[]
    if a.players:
        p=IMPORTS/'nflverse_players.csv'
        meta=download(PLAYERS_URL,p)
        meta['import']=run_import('nflverse_players',p)
        if meta['import']['code']==0:
            br=subprocess.run([sys.executable,str(ROOT/'identity_bridge_v16.py')],capture_output=True,text=True)
            try: meta['identity_bridge']=json.loads(br.stdout) if br.stdout.strip() else {}
            except Exception: meta['identity_bridge']={'stdout':br.stdout.strip()}
            meta['identity_bridge_code']=br.returncode
        results.append(meta)
    if a.rosters is not None:
        seasons=a.rosters or list(range(2020,2027))
        for season in seasons:
            p=IMPORTS/f'roster_{season}.csv'
            meta=download(ROSTER_URL.format(season=season),p); meta['import']=run_import('nflverse_rosters',p); results.append(meta)
    print(json.dumps(results,indent=2))
if __name__=='__main__': main()
