[CmdletBinding()]
param(
    [string]$WorkspaceDir = "",
    [string]$BindHost = "",
    [int]$Port = 0,
    [switch]$NoBrowser,
    [switch]$Reload
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Invoke-Native {
    param(
        [string]$Command,
        [string[]]$Arguments
    )
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command $($Arguments -join ' ')"
    }
}

function Expand-PathValue {
    param([string]$PathValue)
    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return $PathValue
    }
    $expanded = [Environment]::ExpandEnvironmentVariables($PathValue)
    if ($expanded.StartsWith("~")) {
        $suffix = $expanded.Substring(1).TrimStart("\", "/")
        $expanded = Join-Path $HOME $suffix
    }
    return [System.IO.Path]::GetFullPath($expanded)
}

function Get-PythonCommand {
    $python3 = Get-Command python3 -ErrorAction SilentlyContinue
    if ($python3) {
        return @{ Command = $python3.Source; PrefixArgs = @() }
    }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @{ Command = $python.Source; PrefixArgs = @() }
    }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return @{ Command = $py.Source; PrefixArgs = @("-3") }
    }
    throw "Missing required command: python3, python, or py"
}

function Test-AppRoutes {
    param(
        [string]$PythonCommand,
        [string]$RepoRoot
    )
    $script = @"
import importlib
import sys

sys.path.insert(0, r"$RepoRoot")
module = importlib.import_module("app.api.draft_app.main")
routes = []
for route in module.app.routes:
    path = getattr(route, "path", "")
    methods = sorted(getattr(route, "methods", []) or [])
    if path:
        routes.append((path, methods))

print(f"DRAFT app module: {module.__file__}")
print("DRAFT Draftsman routes:")
for path, methods in routes:
    if "draft" in path.lower():
        print(f"  {','.join(methods) or '-'} {path}")

if not any(path == "/api/draftsman/chat" and "POST" in methods for path, methods in routes):
    raise SystemExit("Missing required route: POST /api/draftsman/chat")
"@
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($script))
    & $PythonCommand -c "import base64; exec(base64.b64decode('$encoded').decode('utf-8'))"
    if ($LASTEXITCODE -ne 0) {
        throw "DRAFT app route preflight failed. The app server would start without the Draftsman chat API."
    }
}

$repoRoot = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$requirements = Join-Path $repoRoot "app\api\requirements.txt"
$venvDir = Join-Path $repoRoot "app\api\.venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if ([string]::IsNullOrWhiteSpace($BindHost)) {
    $BindHost = if ($env:DRAFT_HOST) { $env:DRAFT_HOST } else { "127.0.0.1" }
}
if ($Port -eq 0) {
    $Port = if ($env:DRAFT_PORT) { [int]$env:DRAFT_PORT } else { 8000 }
}
if ([string]::IsNullOrWhiteSpace($WorkspaceDir)) {
    if ($env:DRAFT_WORKSPACE) {
        $WorkspaceDir = $env:DRAFT_WORKSPACE
    }
    elseif ($env:DRAFT_WORKSPACE_DIR) {
        $WorkspaceDir = $env:DRAFT_WORKSPACE_DIR
    }
    else {
        $WorkspaceDir = Join-Path $HOME "draft-workspace"
    }
}

$WorkspaceDir = Expand-PathValue $WorkspaceDir

if (-not (Test-Path -LiteralPath $requirements)) {
    throw "DRAFT app requirements were not found at $requirements. Run this script from the draft-framework repo."
}

if (-not (Test-Path -LiteralPath $WorkspaceDir)) {
    throw "Workspace path does not exist: $WorkspaceDir. Pass -WorkspaceDir or run .\install.ps1 -NoStart first."
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Step "Creating missing app virtual environment"
    $pythonSpec = Get-PythonCommand
    Invoke-Native -Command $pythonSpec.Command -Arguments ($pythonSpec.PrefixArgs + @("-m", "venv", $venvDir))
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    $venvPython = Join-Path $venvDir "bin\python"
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Could not find the app Python interpreter under $venvDir."
}

Write-Step "Ensuring app dependencies"
Invoke-Native -Command $venvPython -Arguments @("-m", "pip", "install", "-r", $requirements)

Write-Step "Checking DRAFT app routes"
Test-AppRoutes -PythonCommand $venvPython -RepoRoot $repoRoot

$url = "http://${BindHost}:$Port"
Write-Host ""
Write-Host "Starting DRAFT App"
Write-Host "Framework: $repoRoot"
Write-Host "Workspace: $WorkspaceDir"
Write-Host "URL:       $url"
Write-Host ""
Write-Host "Press Ctrl+C to stop the app."
Write-Host ""

$env:DRAFT_WORKSPACE = $WorkspaceDir
Set-Location $repoRoot

if (-not $NoBrowser) {
    try {
        Start-Process $url | Out-Null
    }
    catch {
        Write-Host "Open $url in your browser."
    }
}

$uvicornArgs = @("-m", "uvicorn", "app.api.draft_app.main:app", "--host", $BindHost, "--port", [string]$Port)
if ($Reload) {
    $uvicornArgs += "--reload"
}

& $venvPython @uvicornArgs
