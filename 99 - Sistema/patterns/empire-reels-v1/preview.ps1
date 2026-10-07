param([string]$Frames, [string]$Name, [int]$Cols = 7)
# Rebuild plan + overlay bundle, render the given frames, composite stills and a contact sheet.
$ErrorActionPreference = 'Continue'
$env:PYTHONIOENCODING = 'utf-8'
$env:Path = [Environment]::GetEnvironmentVariable('Path','User') + ';' + [Environment]::GetEnvironmentVariable('Path','Machine')
$V = $PSScriptRoot; $py = Join-Path $V '..\..\..\.venv\Scripts\python.exe'; $tools = Join-Path $V '..\..\..\tools'
$edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
& $py "$V\plan.py" | Out-Null; & $py "$V\build_overlay.py" | Out-Null
$sha = (& $py "$tools\studio_render.py" "$V\spec.json" --inspect | ConvertFrom-Json).bundle_sha256
foreach ($d in "$V\_t_$Name", "$V\_s_$Name") { if (Test-Path $d) { Remove-Item $d -Recurse -Force -Confirm:$false } }
& $py "$tools\studio_render.py" "$V\spec.json" --outdir "$V\_t_$Name" --approve-bundle $sha --browser-executable $edge --frames $Frames | Out-Null
& $py "$V\composite.py" "$V\_t_$Name" x.mp4 --frames $Frames --stills "$V\_s_$Name" 2>$null | Out-Null
$f = Get-ChildItem "$V\_s_$Name\*.jpg" | Sort-Object Name
$in = @(); foreach ($x in $f) { $in += '-i'; $in += $x.FullName }
$n = $f.Count; $rows = [math]::Ceiling($n / $Cols)
$fc = (0..($n - 1) | ForEach-Object { "[$_]scale=270:480[s$_]" }) -join ';'
for ($i = $n; $i -lt $rows * $Cols; $i++) { $fc += ";color=black:s=270x480:d=1[s$i]" }
$r = @(); for ($k = 0; $k -lt $rows; $k++) { $fc += ';' + ((($k * $Cols)..(($k + 1) * $Cols - 1) | ForEach-Object { "[s$_]" }) -join '') + "hstack=$Cols[r$k]"; $r += "[r$k]" }
if ($rows -gt 1) { $fc += ';' + ($r -join '') + "vstack=$rows" } else { $fc = $fc -replace "\[r0\]$", '' }
ffmpeg -v error -y @in -filter_complex $fc -frames:v 1 "$V\_contact-$Name.jpg"
"$V\_contact-$Name.jpg"
