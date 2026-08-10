# Reads v4.0 Rebuilt — Split Download

Download **all six files you need**: the Code + Docs ZIP, the four database parts, and the rebuild script for your OS.

## 1. Extract the code
Extract `Reads_v4_Part_1_Code_and_Docs.zip`.

## 2. Put all four database parts together
Keep these in the same folder:

- `Reads_v4_Database.sqlite.gz.part00`
- `Reads_v4_Database.sqlite.gz.part01`
- `Reads_v4_Database.sqlite.gz.part02`
- `Reads_v4_Database.sqlite.gz.part03`

## 3. Rebuild the database
macOS/Linux: run `sh rebuild_database_mac_linux.sh`

Windows PowerShell: run `powershell -ExecutionPolicy Bypass -File rebuild_database_windows.ps1`

This creates `reads_football_v4.0.sqlite`. Move that file into the extracted `Reads_Football_Data_Engine_v4.0` folder.

## Verification
Database SHA-256: `39ed5fe996e6b240642bde46daabb2eec1dc310f46e8cdc7e3ea3365070a549d`
Reassembled GZIP SHA-256: `ce16592b9452aa0675ed63bb00e54d9b8ed46235644086de98ee5051d7e724e5`

Rebuild certification: **PASS**
- 414,165 eligible puzzles
- 208,754 Knowledge Graph nodes
- 496,276 Knowledge Graph edges
- 116,638 SEO entities
- 14/14 platform capabilities READY
- SQLite quick check: OK
- Foreign-key errors: 0
- All 13 primary runtime modules compile
