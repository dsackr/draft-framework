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
        [string]$RepoRoot
    )
    $mainPath = Join-Path $RepoRoot "app\api\draft_app\main.py"
    if (-not (Test-Path -LiteralPath $mainPath)) {
        throw "DRAFT app module was not found at $mainPath"
    }
    $source = Get-Content -LiteralPath $mainPath -Raw
    $requiredRoutes = @(
        '/api/draftsman/providers',
        '/api/draftsman/chat'
    )
    Write-Host "DRAFT app module source: $mainPath"
    Write-Host "DRAFT route source check:"
    foreach ($route in $requiredRoutes) {
        if ($source.Contains($route)) {
            Write-Host "  found $route"
        }
        else {
            throw "Missing required route source: $route in $mainPath. Run git pull in this framework folder."
        }
    }
}

function Test-RunningAppRoutes {
    param(
        [string]$PythonCommand,
        [string[]]$UvicornArgs,
        [string]$BindHost,
        [int]$ProbePort,
        [string]$AppApiRoot
    )
    $probeArgs = @($UvicornArgs)
    for ($index = 0; $index -lt $probeArgs.Count; $index++) {
        if ($probeArgs[$index] -eq "--port" -and ($index + 1) -lt $probeArgs.Count) {
            $probeArgs[$index + 1] = [string]$ProbePort
        }
    }

    $probeUrl = "http://${BindHost}:$ProbePort"
    Write-Host "DRAFT route runtime check: $probeUrl/openapi.json"
    
    # Start probe server from the AppApiRoot
    $process = Start-Process -FilePath $PythonCommand -ArgumentList $probeArgs -PassThru -NoNewWindow -WorkingDirectory $AppApiRoot
    try {
        $openapi = $null
        for ($attempt = 0; $attempt -lt 40; $attempt++) {
            if ($process.HasExited) {
                throw "DRAFT probe server exited before route validation completed."
            }
            try {
                $openapi = Invoke-RestMethod -Uri "$probeUrl/openapi.json" -TimeoutSec 1
                break
            }
            catch {
                Start-Sleep -Milliseconds 250
            }
        }
        if ($null -eq $openapi) {
            throw "DRAFT probe server did not become ready at $probeUrl."
        }
        $paths = @($openapi.paths.PSObject.Properties.Name)
        $draftRoutes = $paths | Where-Object { $_ -like "*draft*" } | Sort-Object
        Write-Host "DRAFT runtime routes:"
        foreach ($route in $draftRoutes) {
            Write-Host "  $route"
        }
        if (-not ($paths -contains "/api/draftsman/chat")) {
            throw "Running DRAFT app does not expose /api/draftsman/chat. Uvicorn is loading the wrong app module."
        }
    }
    finally {
        if ($process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -Force
        }
    }
}

$repoRoot = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$requirements = Join-Path $repoRoot "app\api\requirements.txt"
$appApiRoot = Join-Path $repoRoot "app\api"
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
Test-AppRoutes -RepoRoot $repoRoot

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

# Simplify uvicorn arguments and run from the app\api directory
$baseUvicornArgs = @("-m", "uvicorn", "draft_app.main:app", "--host", $BindHost, "--port", [string]$Port)
$uvicornArgs = @($baseUvicornArgs)
if ($Reload) {
    $uvicornArgs += "--reload"
}

Write-Host "Uvicorn app:     draft_app.main:app"
Write-Host "Uvicorn root:    $appApiRoot"
Write-Host "Uvicorn args:    $($uvicornArgs -join ' ')"
Write-Host ""

Write-Step "Checking running DRAFT app routes"
$probePort = if ($Port -lt 55000) { $Port + 10000 } else { $Port - 10000 }
Test-RunningAppRoutes -PythonCommand $venvPython -UvicornArgs $baseUvicornArgs -BindHost $BindHost -ProbePort $probePort -AppApiRoot $appApiRoot

if (-not $NoBrowser) {
    try {
        Start-Process $url | Out-Null
    }
    catch {
        Write-Host "Open $url in your browser."
    }
}

# Run the real app from the AppApiRoot
Set-Location $appApiRoot
& $venvPython @uvicornArgs
