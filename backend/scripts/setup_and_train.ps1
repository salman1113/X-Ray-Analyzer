#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup Kaggle credentials and run X-ray model training.
    
.DESCRIPTION
    1. Copies your kaggle.json to the right location
    2. Starts the download + training pipeline
    
.USAGE
    .\scripts\setup_and_train.ps1 -KaggleJsonPath "C:\Users\Jithi\Downloads\kaggle.json"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$KaggleJsonPath
)

$kaggleDir  = "$env:USERPROFILE\.kaggle"
$kaggleDest = "$kaggleDir\kaggle.json"

# Create .kaggle folder if needed
if (-not (Test-Path $kaggleDir)) {
    New-Item -ItemType Directory -Path $kaggleDir | Out-Null
    Write-Host "Created $kaggleDir"
}

# Copy the key
Copy-Item -Path $KaggleJsonPath -Destination $kaggleDest -Force
Write-Host "✅ Kaggle API key installed at $kaggleDest"

# Secure the file (Kaggle requires this on Linux, but good practice)
# icacls $kaggleDest /inheritance:r /grant:r "$env:USERNAME:R"

# Start training
Write-Host ""
Write-Host "🚀 Starting dataset download and model training..."
Write-Host "   This will take ~20-30 min (CPU) or ~5 min (GPU)"
Write-Host "   The dataset is ~1.1 GB — downloading now"
Write-Host ""

Set-Location (Split-Path $PSScriptRoot -Parent)
python scripts/download_and_train.py
