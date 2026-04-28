[CmdletBinding()]
param(
    [string]$InstallDir = "",
    [string]$WorkspaceDir = "",
    [string]$Repo = "",
    [string]$Ref = "",
    [string]$BindHost = "",
    [int]$Port = 0,
    [string]$ContentRepo = "",
    [string]$DevBranch = "",
    [switch]$SetupDraftsman,
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
if ([string]::IsNullOrWhiteSpace($ContentRepo)) {
    $ContentRepo = if ($env:DRAFT_CONTENT_REPO) { $env:DRAFT_CONTENT_REPO } else { "" }
}
if ([string]::IsNullOrWhiteSpace($DevBranch)) {
    $DevBranch = if ($env:DRAFT_DEV_BRANCH) { $env:DRAFT_DEV_BRANCH } else { "draft-dev" }
}

$StartApp = -not $NoStart
if ($env:DRAFT_START_APP -match "^(0|false|no)$") {
    $StartApp = $false
}

$CreateWorkspace = -not $NoWorkspace
if ($env:DRAFT_CREATE_WORKSPACE -match "^(0|false|no)$") {
    $CreateWorkspace = $false
}

$SetupDraftsmanNow = [bool]$SetupDraftsman
if ($env:DRAFT_SETUP_DRAFTSMAN -match "^(1|true|yes)$") {
    $SetupDraftsmanNow = $true
}

$script:ContentOwner = "github-org"
$script:ContentName = ""
$script:DefaultBranch = "main"

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

function Read-Answer {
    param(
        [string]$Prompt,
        [string]$Default = ""
    )
    if ([string]::IsNullOrWhiteSpace($Default)) {
        return Read-Host $Prompt
    }
    $answer = Read-Host "$Prompt [$Default]"
    if ([string]::IsNullOrWhiteSpace($answer)) {
        return $Default
    }
    return $answer
}

function Read-YesNo {
    param(
        [string]$Prompt,
        [string]$Default = "y"
    )
    $answer = Read-Answer -Prompt "$Prompt (y/n)" -Default $Default
    return $answer -match "^[Yy]"
}

function Select-DraftsmanProvider {
    $answer = Read-Answer -Prompt "Draftsman provider. OpenAI OAuth is available now; other models are coming soon" -Default "OpenAI OAuth"
    if ($answer -notmatch "^[Oo]pen[Aa][Ii](\s+[Oo][Aa]uth)?$") {
        Write-Host "Only OpenAI OAuth is available in this version; continuing with OpenAI OAuth."
    }
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

function Invoke-NativeCapture {
    param(
        [string]$Command,
        [string[]]$Arguments
    )
    $output = & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command $($Arguments -join ' ')"
    }
    return ($output -join "`n").Trim()
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
    $content = $content.Replace("<github-org>", $script:ContentOwner)
    $content = $content.Replace("<private-repo>", $(if ($script:ContentName) { $script:ContentName } else { $WorkspaceName }))
    $content = $content.Replace("<default-branch>", $script:DefaultBranch)
    $content = $content.Replace("<dev-branch>", $DevBranch)
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
        Invoke-Native -Command $script:GitCommand -Arguments @("-C", $WorkspaceRoot, "symbolic-ref", "HEAD", "refs/heads/$DevBranch")
    }
}

function Resolve-RepoSlug {
    param([string]$RepoValue)
    $slug = $RepoValue.Trim()
    $slug = $slug -replace "^https://github.com/", ""
    $slug = $slug -replace "^http://github.com/", ""
    $slug = $slug -replace "^git@github.com:", ""
    $slug = $slug -replace "\.git$", ""
    return $slug
}

function Configure-ContentRepo {
    if ([string]::IsNullOrWhiteSpace($ContentRepo)) {
        $script:ContentRepo = Read-Answer -Prompt "What GitHub repo will you use with DRAFT? Use owner/repo or a GitHub URL"
    }
    if ([string]::IsNullOrWhiteSpace($ContentRepo)) {
        throw "A company content repo is required. Pass -ContentRepo owner/repo or set DRAFT_CONTENT_REPO."
    }

    $script:GhCommand = Require-Command "gh"
    Invoke-Native -Command $script:GhCommand -Arguments @("auth", "status")

    $slug = Resolve-RepoSlug -RepoValue $ContentRepo
    Write-Step "Checking GitHub repo access: $slug"
    $infoJson = Invoke-NativeCapture -Command $script:GhCommand -Arguments @("repo", "view", $slug, "--json", "nameWithOwner,defaultBranchRef")
    $info = $infoJson | ConvertFrom-Json
    $script:ContentOwner = ($info.nameWithOwner -split "/")[0]
    $script:ContentName = ($info.nameWithOwner -split "/")[1]
    if ($info.defaultBranchRef -and $info.defaultBranchRef.name) {
        $script:DefaultBranch = $info.defaultBranchRef.name
    }

    if (Test-Path -LiteralPath (Join-Path $WorkspaceDir ".git")) {
        Invoke-Native -Command $script:GitCommand -Arguments @("-C", $WorkspaceDir, "fetch", "origin")
    }
    elseif ((Test-Path -LiteralPath $WorkspaceDir) -and (Get-ChildItem -LiteralPath $WorkspaceDir -Force | Select-Object -First 1)) {
        throw "Workspace path exists but is not an empty Git checkout: $WorkspaceDir"
    }
    else {
        $workspaceParent = Split-Path -Parent $WorkspaceDir
        if (-not [string]::IsNullOrWhiteSpace($workspaceParent)) {
            New-Item -ItemType Directory -Force -Path $workspaceParent | Out-Null
        }
        Invoke-Native -Command $script:GhCommand -Arguments @("repo", "clone", $slug, $WorkspaceDir)
    }

    Invoke-Native -Command $script:GitCommand -Arguments @("-C", $WorkspaceDir, "fetch", "origin")
    & $script:GitCommand -C $WorkspaceDir show-ref --verify --quiet "refs/remotes/origin/$DevBranch"
    if ($LASTEXITCODE -eq 0) {
        Invoke-Native -Command $script:GitCommand -Arguments @("-C", $WorkspaceDir, "checkout", $DevBranch)
        Invoke-Native -Command $script:GitCommand -Arguments @("-C", $WorkspaceDir, "pull", "--ff-only", "origin", $DevBranch)
    }
    else {
        & $script:GitCommand -C $WorkspaceDir rev-parse --verify HEAD | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Invoke-Native -Command $script:GitCommand -Arguments @("-C", $WorkspaceDir, "checkout", "-B", $DevBranch)
        }
        else {
            Invoke-Native -Command $script:GitCommand -Arguments @("-C", $WorkspaceDir, "checkout", "--orphan", $DevBranch)
        }
    }
}

function Commit-WorkspaceSetup {
    Invoke-Native -Command $script:GitCommand -Arguments @("-C", $WorkspaceDir, "add", ".gitignore", ".draft", "catalog", "configurations")
    & $script:GitCommand -C $WorkspaceDir diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        return
    }
    Invoke-Native -Command $script:GitCommand -Arguments @("-C", $WorkspaceDir, "commit", "-m", "Initialize DRAFT workspace")
    Invoke-Native -Command $script:GitCommand -Arguments @("-C", $WorkspaceDir, "push", "-u", "origin", $DevBranch)
}

function Wait-App {
    $url = "http://${BindHost}:$Port/api/health"
    for ($i = 0; $i -lt 40; $i++) {
        try {
            Invoke-RestMethod -Uri $url -TimeoutSec 1 | Out-Null
            return $true
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }
    return $false
}

function Start-DraftsmanOAuth {
    $encodedWorkspace = [System.Uri]::EscapeDataString($WorkspaceDir)
    $url = "http://${BindHost}:$Port/api/draftsman/oauth/openai/start?workspace=$encodedWorkspace"
    $response = Invoke-RestMethod -Uri $url -TimeoutSec 10
    Write-Host ""
    Write-Host "Opening ChatGPT sign-in for DRAFT Draftsman."
    Start-Process $response.authUrl | Out-Null
}

function Enable-EmbeddedDraftsman {
    $configPath = Join-Path $WorkspaceDir ".draft\workspace.yaml"
    $pythonCode = @'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
draftsman = config.setdefault("draftsman", {})
draftsman["mode"] = "embedded"
embedded = draftsman.setdefault("embedded", {})
embedded["enabled"] = True
embedded["provider"] = "openai"
embedded["model"] = embedded.get("model") or "gpt-5.5"
auth = embedded.setdefault("auth", {})
for key in (
    "accessToken",
    "access_token",
    "apiKey",
    "api_key",
    "apiKeyRef",
    "api_key_ref",
    "clientSecret",
    "client_secret",
    "clientSecretRef",
    "client_secret_ref",
    "refreshToken",
    "refresh_token",
):
    auth.pop(key, None)
auth.update(
    {
        "type": "oauth",
        "clientId": "app_EMoamEEZ73f0CkXaXp7hrann",
        "redirectUri": "http://localhost:1455/auth/callback",
        "tokenStorage": "user-local",
        "apiKeysAllowed": False,
    }
)
path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
'@
    $pythonCode | & $venvPython - $configPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to update Draftsman configuration in $configPath"
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
    Write-Step "Configuring company content repo"
    Configure-ContentRepo
    if (-not $SetupDraftsmanNow -and -not $env:DRAFT_SETUP_DRAFTSMAN) {
        $SetupDraftsmanNow = Read-YesNo -Prompt "Set up the AI Draftsman now? OpenAI OAuth is available; other models are coming soon" -Default "y"
        if ($SetupDraftsmanNow) {
            Select-DraftsmanProvider
        }
    }
    Write-Step "Checking DRAFT workspace folders"
    Copy-WorkspaceTemplate -FrameworkDir $InstallDir -WorkspaceRoot $WorkspaceDir -FrameworkCommit $frameworkCommit
    if ($SetupDraftsmanNow) {
        Enable-EmbeddedDraftsman
    }
    Commit-WorkspaceSetup
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
    $env:DRAFT_WORKSPACE = $WorkspaceDir
    $appApiRoot = Join-Path $InstallDir "app\api"
    
    # Run uvicorn from the app\api directory to avoid module resolution issues
    $app = Start-Process -FilePath $venvPython -ArgumentList @("-m", "uvicorn", "draft_app.main:app", "--host", $BindHost, "--port", [string]$Port) -WorkingDirectory $appApiRoot -PassThru -NoNewWindow
    
    if (Wait-App) {
        if ($SetupDraftsmanNow) {
            Start-DraftsmanOAuth
        }
        Start-Process "http://${BindHost}:$Port" | Out-Null
    }
    else {
        Write-Warning "DRAFT App did not become ready on http://${BindHost}:$Port"
    }
    Wait-Process -Id $app.Id
}
