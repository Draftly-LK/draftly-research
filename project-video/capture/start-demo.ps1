$ErrorActionPreference = 'Stop'
$filmRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$researchRoot = [IO.Path]::GetFullPath((Join-Path $filmRoot '..'))
$platformRoot = Join-Path ([IO.Path]::GetFullPath((Join-Path $researchRoot '..'))) 'draftly-platform'
$preparedRoot = Join-Path ([IO.Path]::GetFullPath((Join-Path $researchRoot '..'))) 'draftly-film-continuation\project-video\out\recording-app'
$appRoot = Join-Path $filmRoot 'out\workflow-recording-app'
$captureOut = Join-Path $filmRoot 'out\continuation'
New-Item -ItemType Directory -Path $appRoot,$captureOut -Force | Out-Null
# Read the prepared, secret-free local copy. Do not write to the product checkout.
foreach($directory in @('src','public')) {
    $destination = Join-Path $appRoot $directory
    if(-not(Test-Path $destination)) {Copy-Item -LiteralPath (Join-Path $preparedRoot $directory) -Destination $destination -Recurse}
}
foreach($file in @('package.json','tsconfig.json','next-env.d.ts','next.config.ts','tailwind.config.ts','postcss.config.mjs','components.json','.env.local')) {
    Copy-Item -LiteralPath (Join-Path $preparedRoot $file) -Destination (Join-Path $appRoot $file)
}
$dependencyTarget = Join-Path $appRoot 'node_modules'
if(-not(Test-Path $dependencyTarget)) {New-Item -ItemType Junction -Path $dependencyTarget -Target (Join-Path $platformRoot 'frontend\node_modules') | Out-Null}
$pgCtl = 'C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe'
$databaseRoot = Join-Path $filmRoot 'out\local-db'
& $pgCtl -D $databaseRoot status | Out-Null
if($LASTEXITCODE -ne 0) {
    $pgStart = Start-Process -FilePath $pgCtl -ArgumentList @('-D',('"'+$databaseRoot+'"'),'-l',('"'+(Join-Path $captureOut 'postgres.log')+'"'),'-o','"-p 15439 -h 127.0.0.1"','-w','start') -WindowStyle Hidden -PassThru -Wait
    if($pgStart.ExitCode -ne 0) {throw 'Owned film database did not start'}
}
$env:PYTHONDONTWRITEBYTECODE = '1'
$backend = Start-Process -FilePath (Join-Path $platformRoot 'backend\.venv\Scripts\python.exe') -ArgumentList @('-B','-u',('"'+(Join-Path $PSScriptRoot 'serve-demo.py')+'"')) -WorkingDirectory $filmRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $captureOut 'backend.log') -RedirectStandardError (Join-Path $captureOut 'backend-error.log')
$env:AUTH_BYPASS = 'true'
$env:NEXT_PUBLIC_API_BASE_URL = 'http://127.0.0.1:4325'
$env:NEXT_DIST_DIR = '.next-demo'
$env:NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = ''
$env:CLERK_SECRET_KEY = ''
$frontend = Start-Process -FilePath 'node' -ArgumentList @('node_modules/next/dist/bin/next','dev','--hostname','127.0.0.1','--port','4315') -WorkingDirectory $appRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $captureOut 'frontend.log') -RedirectStandardError (Join-Path $captureOut 'frontend-error.log')
$bridge = Start-Process -FilePath (Join-Path $researchRoot '.venv\Scripts\python.exe') -ArgumentList @('-B','-u',('"'+(Join-Path $PSScriptRoot 'devtools-bridge.py')+'"')) -WorkingDirectory $filmRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $captureOut 'bridge.log') -RedirectStandardError (Join-Path $captureOut 'bridge-error.log')
@{backend=$backend.Id;frontend=$frontend.Id;bridge=$bridge.Id;app='http://127.0.0.1:4315';api='http://127.0.0.1:4325';mcp='http://127.0.0.1:9234'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $captureOut 'runtime-processes.json') -Encoding utf8
Write-Output 'Isolated film services starting. Existing product records and browser profiles are untouched.'
