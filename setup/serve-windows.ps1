# 업무노트 사이트 실행 스크립트 (Windows)
# 사용법: 프로젝트 폴더에서
#   powershell -NoProfile -ExecutionPolicy Bypass -File setup\serve-windows.ps1
#   -Prepare  사이트 실행에 필요한 것만 준비하고 끝낸다(서버는 띄우지 않음).
# 사이트에 필요한 Python·MkDocs·Material for MkDocs가 없으면 자동으로 설치한다.
# 사용자 계정 컨트롤(UAC) 창 없이 끝나도록 관리자 권한이 필요 없는 방법만 쓴다.
#   - 쓸 수 있는 Python 3.10 이상이 없으면 uv(사용자 폴더 %USERPROFILE%\.local\bin에 설치)로 Python을 내려받는다.
# 변환 도구(kordoc·OfficeCLI)는 사이트 실행에 필요 없으므로 설치하지 않는다(setup-windows.ps1 담당).
#
# 종료 코드: 0 성공, 1 실패, 3 사용자 조치 필요
#   3이면 '[사용자 조치 필요]' 안내를 출력한다. 사용자가 조치를 마치면 이 스크립트를 다시 실행해 이어서 진행한다.
# 주의: 이 파일은 PowerShell 5.1이 한글을 읽을 수 있도록 UTF-8 BOM으로 저장한다.

param([switch]$Prepare)

$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Root
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
# PowerShell 5.1은 기본값이 TLS 1.0이라 내려받기가 실패할 수 있다
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch { }

$HostAddr = '127.0.0.1'
$Port = 8000
$Url = "http://${HostAddr}:$Port"
$VenvPy = Join-Path $Root '.venv\Scripts\python.exe'
$Mkdocs = Join-Path $Root '.venv\Scripts\mkdocs.exe'
$UvHome = Join-Path $env:USERPROFILE '.local\bin\uv.exe'

function Info([string]$msg) { Write-Host $msg -ForegroundColor Cyan }
function Ok([string]$msg) { Write-Host "  완료 $msg" -ForegroundColor Green }
function Warn([string]$msg) { Write-Host "  주의 $msg" -ForegroundColor Yellow }
function Fail([string]$msg) { Write-Host "  실패 $msg" -ForegroundColor Red; exit 1 }

# AI 에이전트가 대신할 수 없는 일을 안내하고 종료 코드 3으로 끝낸다
function Need-User([string]$title, [string[]]$lines) {
    Write-Host ''
    Write-Host "[사용자 조치 필요] $title" -ForegroundColor Yellow
    foreach ($line in $lines) { Write-Host "  $line" }
    Write-Host '  → 끝나면 AI에게 "했어"라고 말하십시오. 이어서 진행합니다. (직접 실행했다면 이 스크립트를 다시 실행하십시오.)'
    exit 3
}

# 내려받기가 실패했을 때, 인터넷 연결 문제면 사용자 조치로, 아니면 실패로 끝낸다
function Net-OrFail([string]$msg) {
    try {
        Invoke-WebRequest -UseBasicParsing -Method Head -Uri 'https://pypi.org/simple/' -TimeoutSec 10 -ErrorAction Stop | Out-Null
    } catch {
        Need-User '인터넷 연결 확인' @(
            '1. Wi-Fi나 유선 인터넷이 연결되어 있는지 확인하십시오.',
            '2. 회사망이라면 보안 프로그램이나 프록시가 pypi.org, astral.sh, github.com 접속을 막고 있지 않은지 IT 담당자에게 확인하십시오.'
        )
    }
    Fail $msg
}

function Python-Ok([string]$exe, [string[]]$pre) {
    & $exe @pre -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Site-Ok {
    if (-not (Test-Path -LiteralPath $VenvPy)) { return $false }
    & $VenvPy -c "import mkdocs, material, mkdocs_charts_plugin" 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Make-Venv {
    if (Test-Path -LiteralPath (Join-Path $Root '.venv')) {
        Remove-Item -LiteralPath (Join-Path $Root '.venv') -Recurse -Force
    }
    # 설치 없이 쓸 수 있는 Python 3.10 이상을 찾는다
    # WindowsApps의 python.exe는 Microsoft Store로 연결되는 가짜 실행 파일이므로 제외한다
    if ((Get-Command py -ErrorAction SilentlyContinue) -and (Python-Ok 'py' @('-3'))) {
        Write-Host '  설치된 Python(py -3)으로 가상환경(.venv)을 만듭니다.'
        & py -3 -m venv .venv
        if (Test-Path -LiteralPath $VenvPy) { return }
        Warn '가상환경을 만들지 못해 uv로 다시 시도합니다.'
    } else {
        $sys = Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*\WindowsApps\*' } | Select-Object -First 1
        if ($sys -and (Python-Ok $sys.Source @())) {
            Write-Host "  설치된 Python($($sys.Source))으로 가상환경(.venv)을 만듭니다."
            & $sys.Source -m venv .venv
            if (Test-Path -LiteralPath $VenvPy) { return }
            Warn '가상환경을 만들지 못해 uv로 다시 시도합니다.'
        } else {
            Write-Host '  사용할 수 있는 Python이 없어 새로 내려받습니다.'
        }
    }
    if (Test-Path -LiteralPath (Join-Path $Root '.venv')) {
        Remove-Item -LiteralPath (Join-Path $Root '.venv') -Recurse -Force
    }

    # uv를 찾고, 없으면 사용자 폴더에 설치한다(관리자 권한 불필요)
    $uv = (Get-Command uv -ErrorAction SilentlyContinue | Select-Object -First 1).Source
    if (-not $uv -and (Test-Path -LiteralPath $UvHome)) { $uv = $UvHome }
    if (-not $uv) {
        Write-Host '  Python을 받기 위해 uv를 사용자 폴더에 설치합니다.'
        $env:UV_NO_MODIFY_PATH = '1'
        # 새 PowerShell 프로세스는 위의 TLS 1.2 설정을 물려받지 않으므로 명령 안에서 다시 지정한다
        & powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; irm https://astral.sh/uv/install.ps1 | iex"
        if (-not (Test-Path -LiteralPath $UvHome)) { Net-OrFail 'uv를 설치하지 못했습니다.' }
        $uv = $UvHome
    }
    # --seed: pip를 함께 넣어 기존 설치 스크립트(setup-windows.ps1)와 같은 방식으로 쓸 수 있게 한다
    & $uv venv --python 3.12 --seed .venv
    if (-not (Test-Path -LiteralPath $VenvPy)) { Net-OrFail 'Python을 내려받지 못했습니다.' }
}

# ---------------------------------------------------------------------------
Info "업무노트 사이트를 준비합니다. 프로젝트 폴더: $Root"

if (Site-Ok) { Ok 'MkDocs · Material for MkDocs 준비됨' } else {
    # 가상환경이 없거나, 만든 Python이 사라져 깨졌으면 다시 만든다
    $venvOk = $false
    if (Test-Path -LiteralPath $VenvPy) {
        & $VenvPy -c "import sys" 2>$null
        $venvOk = ($LASTEXITCODE -eq 0)
    }
    if (-not $venvOk) {
        if (Test-Path -LiteralPath (Join-Path $Root '.venv')) { Warn '기존 가상환경(.venv)이 동작하지 않아 다시 만듭니다.' }
        Make-Venv
    }
    Write-Host '  MkDocs와 Material for MkDocs를 설치합니다.'
    & $VenvPy -m pip install -q --disable-pip-version-check -r mkdocs\requirements.txt
    if ($LASTEXITCODE -ne 0) { Net-OrFail 'MkDocs 설치에 실패했습니다. 위의 오류 메시지를 확인하십시오.' }
    if (-not (Site-Ok)) { Fail 'Material for MkDocs를 불러오지 못했습니다.' }
    Ok 'MkDocs · Material for MkDocs 설치됨'
}
$materialVer = & $VenvPy -c "import importlib.metadata as m; print(m.version('mkdocs-material'))"
Ok "$(& $Mkdocs --version), Material for MkDocs $materialVer"

if ($Prepare) { Info '준비가 끝났습니다.'; exit 0 }

# 이미 사이트가 떠 있으면 새로 띄우지 않고, 8000 포트를 다른 프로그램이 쓰고 있으면 빈 포트를 쓴다
$probe = & $VenvPy (Join-Path $PSScriptRoot 'find-port.py') $HostAddr | Select-Object -Last 1
$portState, $foundPort = "$probe".Trim() -split ' '
if ($portState -eq 'running') {
    Info "이미 $foundPort 포트에서 실행 중입니다. 브라우저에서 http://${HostAddr}:$foundPort 을 여십시오."
    exit 0
}
if ($portState -ne 'free') { Fail '8000~8010 포트를 모두 다른 프로그램이 쓰고 있습니다. 쓰지 않는 프로그램을 종료한 뒤 다시 실행하십시오.' }
if ([int]$foundPort -ne $Port) { Warn "$Port 포트를 다른 프로그램이 쓰고 있어 $foundPort 포트로 실행합니다." }
$Port = [int]$foundPort
$Url = "http://${HostAddr}:$Port"

Info "사이트를 실행합니다: $Url (종료: Ctrl + C)"
& $Mkdocs serve -a "${HostAddr}:$Port" -f mkdocs\mkdocs.yml
exit $LASTEXITCODE
