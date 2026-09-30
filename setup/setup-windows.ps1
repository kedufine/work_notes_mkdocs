# 인수인계 업무노트 Windows 설치 스크립트
# 사용법: setup\setup-windows.cmd 를 더블클릭하거나, PowerShell에서
#   powershell -NoProfile -ExecutionPolicy Bypass -File setup\setup-windows.ps1
# 이미 설치된 프로그램은 건너뛰므로 여러 번 실행해도 안전하다.
# 주의: 이 파일은 PowerShell 5.1이 한글을 읽을 수 있도록 UTF-8 BOM으로 저장한다.

$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Root
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$KordocScripts = 'onnxruntime-node,protobufjs'

function Step([string]$n, [string]$msg) { Write-Host ''; Write-Host "[$n] $msg" -ForegroundColor Cyan }
function Ok([string]$msg) { Write-Host "  완료 $msg" -ForegroundColor Green }
function Warn([string]$msg) { Write-Host "  주의 $msg" -ForegroundColor Yellow }
function Fail([string]$msg) {
    Write-Host "  실패 $msg" -ForegroundColor Red
    Write-Host ''
    Read-Host 'Enter 키를 누르면 창을 닫습니다'
    exit 1
}
function Has([string]$cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Refresh-Path {
    # winget·설치 프로그램이 바꾼 PATH를 현재 창에 다시 읽어 온다
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user;$env:LOCALAPPDATA\OfficeCLI;$env:APPDATA\npm"
}
function Winget-Install([string]$id, [string]$label) {
    Write-Host "  $label 을(를) 설치합니다. 사용자 계정 컨트롤 창이 뜨면 '예'를 누르십시오."
    winget install -e --id $id --accept-source-agreements --accept-package-agreements
    Refresh-Path
}
function Python-Ok {
    if (-not (Has 'py')) { return $false }
    & py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
    return ($LASTEXITCODE -eq 0)
}
function Node-Ok {
    if (-not (Has 'node')) { return $false }
    & node -e "process.exit(+process.versions.node.split('.')[0] >= 20 ? 0 : 1)" 2>$null
    return ($LASTEXITCODE -eq 0)
}

Write-Host "인수인계 업무노트 설치를 시작합니다. 프로젝트 폴더: $Root"
Refresh-Path

# ---------------------------------------------------------------------------
Step '1/8' 'winget (Windows 패키지 관리자)'
if (-not (Has 'winget')) {
    Warn 'winget이 없습니다. Microsoft Store에서 "앱 설치 관리자(App Installer)"를 설치하거나 업데이트한 뒤 다시 실행하십시오.'
    Start-Process 'ms-windows-store://pdp/?productid=9NBLGGH4NNS1' -ErrorAction SilentlyContinue
    Fail 'winget을 찾을 수 없습니다. README.md의 수동 설치 안내를 따라도 됩니다.'
}
Ok "winget $(winget --version)"

# ---------------------------------------------------------------------------
Step '2/8' 'Git · Python · Node.js'
if (Has 'git') { Ok "$(git --version)" } else {
    Winget-Install 'Git.Git' 'Git'
    if (Has 'git') { Ok "$(git --version)" } else { Fail 'Git을 찾을 수 없습니다. 창을 닫고 스크립트를 다시 실행하십시오.' }
}

if (Python-Ok) { Ok "$(py -3 --version)" } else {
    Winget-Install 'Python.Python.3.12' 'Python 3.12'
    if (Python-Ok) { Ok "$(py -3 --version)" } else { Fail 'Python 3.10 이상을 찾을 수 없습니다. 창을 닫고 스크립트를 다시 실행하십시오.' }
}

if (Node-Ok) { Ok "Node.js $(node --version)" } else {
    Winget-Install 'OpenJS.NodeJS.LTS' 'Node.js LTS'
    if (Node-Ok) { Ok "Node.js $(node --version)" } else { Fail 'Node.js 20 이상을 찾을 수 없습니다. 창을 닫고 스크립트를 다시 실행하십시오.' }
}

# ---------------------------------------------------------------------------
Step '3/8' 'PowerShell 스크립트 실행 허용 (현재 사용자)'
# 이후 사용자가 PowerShell에서 npm 등을 직접 실행할 수 있도록 한다
$policy = Get-ExecutionPolicy -Scope CurrentUser
if ($policy -eq 'Undefined' -or $policy -eq 'Restricted' -or $policy -eq 'AllSigned') {
    try {
        Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force -ErrorAction Stop
        Ok 'RemoteSigned로 설정했습니다.'
    } catch {
        Warn '회사 정책으로 변경할 수 없습니다. PowerShell 대신 명령 프롬프트(cmd)에서 명령을 실행하십시오.'
    }
} else { Ok "현재 정책: $policy" }

# ---------------------------------------------------------------------------
Step '4/8' 'kordoc (한글·PDF·워드·엑셀·이미지 읽기)'
if (Has 'kordoc') { Ok 'kordoc 이미 설치됨' } else {
    # npm.ps1 대신 npm.cmd를 호출해 실행 정책의 영향을 받지 않게 한다
    # npm 12부터 설치 스크립트가 기본 차단되므로 OCR 엔진(onnxruntime-node)의 스크립트를 허용한다
    & npm.cmd install -g kordoc "--allow-scripts=$KordocScripts"
    Refresh-Path
    if (Has 'kordoc') { Ok 'kordoc 설치됨' } else { Fail 'kordoc 설치에 실패했습니다. 위의 오류 메시지를 확인하십시오.' }
}

# ---------------------------------------------------------------------------
Step '5/8' 'OfficeCLI (파워포인트 읽기)'
if (Has 'officecli') { Ok 'officecli 이미 설치됨' } else {
    # 공식 설치 스크립트는 실패 시 exit를 호출하므로 별도 프로세스로 실행한다
    $installer = Join-Path $env:TEMP 'officecli-install.ps1'
    try {
        Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.ps1' -OutFile $installer -ErrorAction Stop
    } catch { Fail 'OfficeCLI 설치 파일을 내려받지 못했습니다. 인터넷 연결을 확인하십시오.' }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $installer
    Refresh-Path
    if (Has 'officecli') { Ok 'officecli 설치됨' } else { Fail 'officecli를 찾을 수 없습니다. 창을 닫고 스크립트를 다시 실행하십시오.' }
}

# ---------------------------------------------------------------------------
Step '6/8' '긴 경로 허용'
& git config --global core.longpaths true
$long = (Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -Name LongPathsEnabled -ErrorAction SilentlyContinue).LongPathsEnabled
if ($long -eq 1) { Ok 'Windows 긴 경로가 이미 허용되어 있습니다.' } else {
    Warn 'Windows 긴 경로(260자 초과)가 허용되어 있지 않습니다. 폴더가 깊은 자료는 변환에 실패할 수 있습니다.'
    Warn 'README.md의 "긴 경로 허용" 절을 관리자 권한으로 실행하거나, 프로젝트를 C:\work 처럼 짧은 경로에 두십시오.'
}

# ---------------------------------------------------------------------------
Step '7/8' '파이썬 가상환경과 MkDocs · 다이어그램 도구'
$venvPy = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPy)) {
    & py -3 -m venv .venv
    if (-not (Test-Path -LiteralPath $venvPy)) { Fail '가상환경(.venv)을 만들지 못했습니다.' }
}
& $venvPy -m pip install -q --upgrade pip
& $venvPy -m pip install -q -r mkdocs\requirements.txt
if ($LASTEXITCODE -ne 0) { Fail 'MkDocs 설치에 실패했습니다.' }
Ok "$(& (Join-Path $Root '.venv\Scripts\mkdocs.exe') --version)"

$mermaid = Join-Path $Root '.agents\skills\pretty-mermaid'
if (Test-Path -LiteralPath (Join-Path $mermaid 'node_modules')) { Ok 'pretty-mermaid 이미 설치됨' } else {
    Push-Location -LiteralPath $mermaid
    & npm.cmd install --silent
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -eq 0) { Ok 'pretty-mermaid 설치됨' } else { Warn 'pretty-mermaid를 설치하지 못했습니다. 변환 작업에는 영향이 없습니다.' }
}

# ---------------------------------------------------------------------------
Step '8/8' '설치 확인'
& $venvPy .agents\skills\handover-to-mkdocs\scripts\convert.py --check
if ($LASTEXITCODE -eq 0) {
    Write-Host ''
    Write-Host '설치가 끝났습니다.' -ForegroundColor Green
    Write-Host '다음 순서로 사용하십시오.'
    Write-Host '  1. 열려 있는 PowerShell·터미널 창을 모두 닫고 새로 엽니다(설치한 프로그램의 경로를 반영하기 위해).'
    Write-Host "  2. 받은 자료를 '1. 인수인계 자료 원본' 폴더에 넣습니다."
    Write-Host "  3. 프로젝트 폴더에서 AI 에이전트를 실행하고 '자료를 모두 변환해서 사이트에 등록해줘'라고 요청합니다."
    Write-Host '  4. 사이트 보기: .venv\Scripts\mkdocs serve -f mkdocs\mkdocs.yml  →  http://127.0.0.1:8000'
    Write-Host ''
    Read-Host 'Enter 키를 누르면 창을 닫습니다'
} else {
    Fail '확인에 실패한 도구가 있습니다. 창을 닫고 이 스크립트를 한 번 더 실행하십시오.'
}
