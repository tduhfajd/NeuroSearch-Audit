param()

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "[setup] $Message"
}

function Write-Note {
    param([string]$Message)
    Write-Host "[setup] $Message"
}

function Test-Command {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-WingetPackage {
    param(
        [string]$Id,
        [string]$CommandName
    )

    if ($CommandName -and (Test-Command $CommandName)) {
        return
    }

    Write-Step "Installing $Id"
    winget install --id $Id -e --accept-package-agreements --accept-source-agreements
}

if (-not (Test-Command "winget")) {
    throw "winget is not available. Install App Installer from Microsoft Store and run this script again."
}

Install-WingetPackage -Id "Git.Git" -CommandName "git"
Install-WingetPackage -Id "GoLang.Go" -CommandName "go"
Install-WingetPackage -Id "Python.Python.3.11" -CommandName "python"
Install-WingetPackage -Id "OpenJS.NodeJS.LTS" -CommandName "node"
Install-WingetPackage -Id "JohnMacFarlane.Pandoc" -CommandName "pandoc"

if (-not (Test-Command "lualatex") -and -not (Test-Command "xelatex") -and -not (Test-Command "pdflatex")) {
    Install-WingetPackage -Id "MiKTeX.MiKTeX" -CommandName "pdflatex"
}

Write-Step "Creating Python virtual environment"
if (-not (Test-Path ".venv")) {
    py -3 -m venv .venv
} else {
    Write-Note "Virtual environment .venv already exists"
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\pip.exe" install -r requirements.txt

Write-Step "Installing Node.js dependencies"
npm install

Write-Step "Installing Playwright Chromium browser"
npx playwright install chromium

Write-Step "Setup completed"
Write-Host "Verification:"
Write-Host "  python run_audit.py --help"
Write-Host "Next steps:"
Write-Host "1. Activate the environment: .\.venv\Scripts\activate"
Write-Host "2. Run an audit: python run_audit.py https://example.com"
