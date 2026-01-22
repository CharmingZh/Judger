Write-Host "Starting Resume Builder Server..."
$PythonPath = Join-Path $env:USERPROFILE ".conda\envs\judger_env\python.exe"
& $PythonPath -m uvicorn app.main:app --reload
