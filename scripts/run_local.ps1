# Start the app against a local Ollama model (Windows PowerShell).
$env:SANAD_BASE_URL = "http://localhost:11434/v1"
$env:SANAD_API_KEY  = "ollama"
if (-not $env:SANAD_MODEL) { $env:SANAD_MODEL = "qwen2.5:3b" }
$env:HF_HUB_OFFLINE = "1"   # embedding model is cached after the first run

$env:STREAMLIT_THEME_BASE = "light"
$env:STREAMLIT_THEME_PRIMARY_COLOR = "#2C4BC7"
$env:STREAMLIT_THEME_BACKGROUND_COLOR = "#F4F6FB"
$env:STREAMLIT_THEME_SECONDARY_BACKGROUND_COLOR = "#E8ECF6"
$env:STREAMLIT_THEME_TEXT_COLOR = "#16203A"

Set-Location (Split-Path $PSScriptRoot -Parent)
python -m streamlit run app.py
