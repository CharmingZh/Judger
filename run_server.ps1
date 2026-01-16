Write-Host "Starting Resume Builder Server..."
$env:PATH = "C:\Users\JmZha\.conda\envs\cv_helper;C:\Users\JmZha\.conda\envs\cv_helper\Scripts;$env:PATH"
python -m uvicorn app.main:app --reload
