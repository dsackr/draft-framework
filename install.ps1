[CmdletBinding()]
param(
    [string]$InstallDir = "",
    [string]$WorkspaceDir = "",
    [string]$Repo = "",
    [string]$Ref = "",
    [string]$BindHost = "",
    [int]$Port = 0,
    [switch]$NoStart,
    [switch]$NoWorkspace
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Repo)) {
    $Repo = if ($env:DRAFT_REPO_URL) { $env:DRAFT_REPO_URL } else { "https://github.com/dsackr/draft-framework.git" }
}
if ([string]::IsNullOrWhiteSpace($Ref)) {
    $Ref = if ($env:DRAFT_REF) { $env:DRAFT_REF } else { "main" }
}
if ([string]::IsNullOrWhiteSpace($BindHost)) {
    $BindHost = if ($env:DRAFT_HOST) { $env:DRAFT_HOST } else { "127.0.0.1" }
}
if ($Port -eq 0) {
    $Port = if ($env:DRAFT_PORT) { [int]$env:DRAFT_PORT } else { 8000 }
}

$StartApp = -not $NoStart
if ($env:DRAFT_START_APP -match "^(0|false|no)$") {
    $StartApp = $false
}

$CreateWorkspace = -not $NoWorkspace
if ($env:DRAFT_CREATE_WORKSPACE -match "^(0|false|no)$") {
    $CreateWorkspace = $false
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Require-Command {
    param([string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Missing required command: $Name"
    }
    return $command.Source
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

function Get-RelativePath {
    param(
        [string]$BasePath,
        [string]$TargetPath
    )
    $baseFull = [System.IO.Path]::GetFullPath($BasePath).TrimEnd("\", "/") + [System.IO.Path]::DirectorySeparatorChar
    $targetFull = [System.IO.Path]::GetFullPath($TargetPath)
    $baseUri = New-Object System.Uri -ArgumentList $baseFull
    $targetUri = New-Object System.Uri -ArgumentList $targetFull
    $relativeUri = $baseUri.MakeRelativeUri($targetUri)
    return [System.Uri]::UnescapeDataString($relativeUri.ToString()).Replace("/", [string][System.IO.Path]::DirectorySeparatorChar)
}

function Write-Utf8NoBom {
    param(
        [string]$Path,
        [string]$Content
    )
    $encoding = New-Object System.Text.UTF8Encoding -ArgumentList $false
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Render-Template {
    param(
        [string]$Source,
        [string]$Target,
        [string]$WorkspaceName,
        [string]$FrameworkCommit,
        [string]$Timestamp
    )
    if (Test-Path -LiteralPath $Target) {
        return
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
    $content = Get-Content -LiteralPath $Source -Raw
    $content = $content.Replace("<company-draft-workspace>", $WorkspaceName)
    $content = $content.Replace("<private-repo>", $WorkspaceName)
    $content = $content.Replace("<tag-or-branch>", $Ref)
    $content = $content.Replace("<resolved-sha>", $FrameworkCommit)
    $content = $content.Replace("<iso-8601-timestamp>", $Timestamp)
    Write-Utf8NoBom -Path $Target -Content $content
}

function Copy-WorkspaceTemplate {
    param(
        [string]$FrameworkDir,
        [string]$WorkspaceRoot,
        [string]$FrameworkCommit
    )
    $templateRoot = Join-Path $FrameworkDir "templates\workspace"
    $workspaceName = Split-Path -Leaf $WorkspaceRoot
    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

    New-Item -ItemType Directory -Force -Path $WorkspaceRoot | Out-Null

    Get-ChildItem -LiteralPath $templateRoot -Force -Recurse -Directory | ForEach-Object {
        $templateDirectory = $_
        $relative = Get-RelativePath -BasePath $templateRoot -TargetPath $templateDirectory.FullName
        New-Item -ItemType Directory -Force -Path (Join-Path $WorkspaceRoot $relative) | Out-Null
    }

    Get-ChildItem -LiteralPath $templateRoot -Force -Recurse -File | ForEach-Object {
        $templateFile = $_
        $relative = Get-RelativePath -BasePath $templateRoot -TargetPath $templateFile.FullName
        switch -Wildcard ($relative) {
            ".draft\workspace.yaml.tmpl" {
                Render-Template -Source $templateFile.FullName -Target (Join-Path $WorkspaceRoot ".draft\workspace.yaml") -WorkspaceName $workspaceName -FrameworkCommit $FrameworkCommit -Timestamp $timestamp
            }
            ".draft\framework.lock.tmpl" {
                Render-Template -Source $templateFile.FullName -Target (Join-Path $WorkspaceRoot ".draft\framework.lock") -WorkspaceName $workspaceName -FrameworkCommit $FrameworkCommit -Timestamp $timestamp
            }
            ".gitignore.tmpl" {
                Render-Template -Source $templateFile.FullName -Target (Join-Path $WorkspaceRoot ".gitignore") -WorkspaceName $workspaceName -FrameworkCommit $FrameworkCommit -Timestamp $timestamp
            }
            "*.tmpl" {}
            default {
                $target = Join-Path $WorkspaceRoot $relative
                if (-not (Test-Path -LiteralPath $target)) {
                    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
                    Copy-Item -LiteralPath $templateFile.FullName -Destination $target
                }
            }
        }
    }

    if (-not (Test-Path -LiteralPath (Join-Path $WorkspaceRoot ".git"))) {
        Invoke-Native -Command $script:GitCommand -Arguments @("-C", $WorkspaceRoot, "init")
        Invoke-Native -Command $script:GitCommand -Arguments @("-C", $WorkspaceRoot, "symbolic-ref", "HEAD", "refs/heads/dev")
    }
}

$script:GitCommand = Require-Command "git"
$pythonSpec = Get-PythonCommand

if ([string]::IsNullOrWhiteSpace($InstallDir)) {
    if ($env:DRAFT_INSTALL_DIR) {
        $InstallDir = $env:DRAFT_INSTALL_DIR
    }
    elseif ((Test-Path -LiteralPath (Join-Path (Get-Location) "app\api\requirements.txt")) -and (Test-Path -LiteralPath (Join-Path (Get-Location) "framework\tools\validate.py"))) {
        $InstallDir = (Get-Location).Path
    }
    else {
        $InstallDir = Join-Path $HOME "draft-framework"
    }
}

if ([string]::IsNullOrWhiteSpace($WorkspaceDir)) {
    $WorkspaceDir = if ($env:DRAFT_WORKSPACE_DIR) { $env:DRAFT_WORKSPACE_DIR } else { Join-Path $HOME "draft-workspace" }
}

$InstallDir = Expand-PathValue $InstallDir
$WorkspaceDir = Expand-PathValue $WorkspaceDir
$venvDir = Join-Path $InstallDir "app\api\.venv"

Write-Step "Installing DRAFT framework"
if (Test-Path -LiteralPath (Join-Path $InstallDir ".git")) {
    $dirty = & $script:GitCommand -C $InstallDir status --porcelain
    if ($dirty) {
        throw "Install directory has uncommitted changes: $InstallDir. Commit or stash those changes, or choose another -InstallDir."
    }
    Invoke-Native -Command $script:GitCommand -Arguments @("-C", $InstallDir, "fetch", "origin")
    & $script:GitCommand -C $InstallDir show-ref --verify --quiet "refs/remotes/origin/$Ref"
    $remoteBranchExists = $LASTEXITCODE -eq 0
    if ($remoteBranchExists) {
        Invoke-Native -Command $script:GitCommand -Arguments @("-C", $InstallDir, "checkout", $Ref)
        Invoke-Native -Command $script:GitCommand -Arguments @("-C", $InstallDir, "pull", "--ff-only", "origin", $Ref)
    }
    else {
        Invoke-Native -Command $script:GitCommand -Arguments @("-C", $InstallDir, "checkout", $Ref)
    }
}
elseif (Test-Path -LiteralPath $InstallDir) {
    throw "Install path exists but is not a Git checkout: $InstallDir"
}
else {
    Invoke-Native -Command $script:GitCommand -Arguments @("clone", $Repo, $InstallDir)
    Invoke-Native -Command $script:GitCommand -Arguments @("-C", $InstallDir, "checkout", $Ref)
}

$frameworkCommit = (& $script:GitCommand -C $InstallDir rev-parse HEAD).Trim()

Write-Step "Installing Python app dependencies"
Invoke-Native -Command $pythonSpec.Command -Arguments ($pythonSpec.PrefixArgs + @("-m", "venv", $venvDir))
$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    $venvPython = Join-Path $venvDir "bin\python"
}
Invoke-Native -Command $venvPython -Arguments @("-m", "pip", "install", "-r", (Join-Path $InstallDir "app\api\requirements.txt"))

if ($CreateWorkspace) {
    Write-Step "Creating DRAFT workspace"
    Copy-WorkspaceTemplate -FrameworkDir $InstallDir -WorkspaceRoot $WorkspaceDir -FrameworkCommit $frameworkCommit
}

Write-Host ""
Write-Host "DRAFT install complete."
Write-Host ""
Write-Host "Framework: $InstallDir"
Write-Host "Workspace: $WorkspaceDir"
Write-Host "App URL:   http://${BindHost}:$Port"
Write-Host ""
Write-Host "To start later:"
Write-Host "  cd `"$InstallDir`""
Write-Host "  .\run.ps1 -WorkspaceDir `"$WorkspaceDir`""
Write-Host ""

if ($StartApp) {
    Write-Step "Starting DRAFT App"
    Set-Location $InstallDir
    $env:DRAFT_WORKSPACE = $WorkspaceDir
    & $venvPython -m uvicorn app.api.draft_app.main:app --host $BindHost --port $Port
}
