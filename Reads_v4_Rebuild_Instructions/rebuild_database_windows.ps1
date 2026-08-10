$parts = Get-ChildItem "Reads_v4_Database.sqlite.gz.part*" | Sort-Object Name
$gzPath = "Reads_v4_Database.sqlite.gz"
$outPath = "reads_football_v4.0.sqlite"
$joined = [System.IO.File]::Create($gzPath)
try { foreach ($p in $parts) { $input = [System.IO.File]::OpenRead($p.FullName); try { $input.CopyTo($joined) } finally { $input.Close() } } } finally { $joined.Close() }
$inputFile = [System.IO.File]::OpenRead($gzPath)
$outputFile = [System.IO.File]::Create($outPath)
$gzip = New-Object System.IO.Compression.GzipStream($inputFile,[System.IO.Compression.CompressionMode]::Decompress)
try { $gzip.CopyTo($outputFile) } finally { $gzip.Close(); $outputFile.Close(); $inputFile.Close() }
Write-Host "Rebuilt reads_football_v4.0.sqlite"
