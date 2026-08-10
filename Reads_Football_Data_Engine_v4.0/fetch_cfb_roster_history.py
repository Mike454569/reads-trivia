"""Reads v1.7 historical CFB roster refresh.
Downloads SportsDataverse/cfbfastR-data roster CSVs and runs update_cfb.py/import logic.
The packaged DB already includes historical roster coverage. This script is for refresh/rebuilds.
"""
from pathlib import Path
import urllib.request,hashlib,json,sys
ROOT=Path(__file__).parent
BASE="https://raw.githubusercontent.com/sportsdataverse/cfbfastR-data/main/rosters/csv/cfb_rosters_{season}.csv"
OUT=ROOT/"imports";OUT.mkdir(exist_ok=True)
def fetch(season):
 p=OUT/f"cfb_rosters_{season}.csv";u=BASE.format(season=season)
 req=urllib.request.Request(u,headers={"User-Agent":"Reads-Football-Data-Engine/1.7"})
 with urllib.request.urlopen(req,timeout=60) as r, p.open("wb") as f: f.write(r.read())
 return {"season":season,"path":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
if __name__=="__main__":
 years=[int(x) for x in sys.argv[1:]] or list(range(2004,2026))
 print(json.dumps([fetch(y) for y in years],indent=2))
