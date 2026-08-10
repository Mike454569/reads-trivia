#!/bin/sh
set -e
cat Reads_v4_Database.sqlite.gz.part* > Reads_v4_Database.sqlite.gz
gzip -dc Reads_v4_Database.sqlite.gz > reads_football_v4.0.sqlite
echo "Rebuilt reads_football_v4.0.sqlite"
