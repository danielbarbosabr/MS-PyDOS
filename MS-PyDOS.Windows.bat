@echo off
REM =====================================================================
REM  MS-PyDOS - Instalador / Inicializador para Windows (estilo MS-DOS)
REM  Opcoes: [1] Instalar  [2] Iniciar  [3] Sair
REM
REM  Tudo e' relativo a pasta do aplicativo (%~dp0), nunca a usuario fixo.
REM  Apos a instalacao, NAO depende do PATH: usa sempre o python do venv.
REM =====================================================================
title MS-PyDOS
chcp 65001 >nul 2>nul
color 1F
setlocal EnableDelayedExpansion

set "APP_DIR=%~dp0"
if "%APP_DIR:~-1%"=="\" set "APP_DIR=%APP_DIR:~0,-1%"
set "VENV_DIR=%APP_DIR%\venv"
set "APP=%APP_DIR%\MS-PyDOS.py"
set "DATA_DIR=%APP_DIR%\data"
set "PY_INSTALLER=%TEMP%\python-installer.exe"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "PIP=%VENV_DIR%\Scripts\pip.exe"

:menu
cls
echo.
set "PAD=                                                                "
set "BAR=--------------------------------------------------------------"
set "BAR=%BAR:~0,58%"
echo  +%BAR%+
set "T=MS-PyDOS - PROGRAMA DE INSTALACAO"
set "T=%T%!PAD!"
set "L=| %T:~0,56% |"
echo  !L!
echo  +%BAR%+
set "T=SISTEMA DETECTADO: WINDOWS"
set "T=%T%!PAD!"
set "L=| %T:~0,56% |"
echo  !L!
echo  +%BAR%+
set "O1=[1] INSTALAR   Prepara o ambiente e abre o MS-PyDOS"
set "O1=%O1%!PAD!"
set "L=| %O1:~0,56% |"
echo  !L!
set "O2=[2] INICIAR    Abre o MS-PyDOS ja instalado"
set "O2=%O2%!PAD!"
set "L=| %O2:~0,56% |"
echo  !L!
set "O3=[3] SAIR       Encerra este instalador"
set "O3=%O3%!PAD!"
set "L=| %O3:~0,56% |"
echo  !L!
echo  +%BAR%+
echo.
set /p "OPCAO=   Escolha uma opcao: "

if "%OPCAO%"=="1" goto instalar
if "%OPCAO%"=="2" goto iniciar
if "%OPCAO%"=="3" exit /b 0
echo.
echo  Opcao invalida.
pause
goto menu

REM ===================== PROCURA PYTHON =====================
REM Define PYTHON_CMD como um comando executavel (ja com aspas se preciso).
REM Ordem: python do venv -> py -3 -> where python -> caminhos comuns.
:encontrar_python
set "PYTHON_CMD="
call :try_python "%VENV_PY%"
if defined PYTHON_CMD goto :eof
call :try_python "py -3"
if defined PYTHON_CMD goto :eof
for /f "delims=" %%P in ('where python 2^>nul') do (
    call :try_python "%%P"
    if defined PYTHON_CMD goto :eof
)
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    call :try_python "%%D\python.exe"
    if defined PYTHON_CMD goto :eof
)
for /d %%D in ("%ProgramFiles%\Python3*") do (
    call :try_python "%%D\python.exe"
    if defined PYTHON_CMD goto :eof
)
echo  [AVISO] Python nao encontrado no sistema.
goto :eof

:try_python
set "CAND=%~1"
if "%CAND%"=="" goto :eof
if "%CAND%"=="py -3" (
    %CAND% --version >nul 2>nul
) else (
    "%CAND%" --version >nul 2>nul
)
if errorlevel 1 goto :eof
if "%CAND%"=="py -3" (
    set "PYTHON_CMD=py -3"
) else (
    echo %CAND% | find " " >nul
    if errorlevel 1 ( set "PYTHON_CMD=%CAND%" ) else ( set "PYTHON_CMD=\"%CAND%\"" )
)
echo  [OK] Python encontrado.
goto :eof

REM ===================== INSTALAR PYTHON =====================
:instalar_python
echo  [..] Python nao encontrado. Iniciando instalacao automatica...
where winget >nul 2>nul
if not errorlevel 1 (
    echo  [..] Usando winget para instalar Python 3...
    winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
    if not errorlevel 1 (
        echo  [OK] winget concluiu a instalacao.
        goto :eof
    )
    echo  [AVISO] winget falhou; tentando o instalador oficial.
)
echo  [..] Baixando instalador oficial do Python 3.12...
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe' -OutFile '%PY_INSTALLER%'"
if exist "%PY_INSTALLER%" (
    echo  [..] Instalacao silenciosa ^(adiciona ao PATH do usuario^)...
    "%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1
    if errorlevel 1 (
        echo  [ERRO] A instalacao do Python falhou.
        del "%PY_INSTALLER%" >nul 2>nul
        goto :eof
    )
    del "%PY_INSTALLER%" >nul 2>nul
    echo  [OK] Instalador oficial executado.
) else (
    echo  [ERRO] Nao foi possivel baixar o instalador do Python ^(sem internet?^).
)
goto :eof

REM ===================== INSTALAR =====================
:instalar
cls
echo.
echo  [..] Iniciando instalacao do MS-PyDOS...
echo.

REM 1. Detectar / instalar Python (reutiliza se ja existir)
call :encontrar_python
if not defined PYTHON_CMD (
    call :instalar_python
    call :encontrar_python
)
if not defined PYTHON_CMD (
    echo.
    echo  [ERRO] Nao foi possivel obter nem instalar o Python.
    pause
    goto menu
)

REM O Python ja foi validado por :try_python (executou --version com sucesso).
echo  [OK] Python operacional.

REM 2. Criar venv (reutiliza se ja existir)
if not exist "%VENV_DIR%" (
    echo  [..] Criando ambiente virtual ^(venv^)...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo  [ERRO] Falha ao criar o venv.
        pause
        goto menu
    )
    echo  [OK] Ambiente virtual criado.
) else (
    echo  [OK] Ambiente virtual ^(venv^) ja existe. Reutilizando.
)

if not exist "%VENV_PY%" (
    echo  [ERRO] O Python do venv nao foi criado.
    pause
    goto menu
)

REM 3. pip (com fallback ensurepip)
"%VENV_PY%" -m pip --version >nul 2>nul
if errorlevel 1 (
    echo  [..] pip ausente no venv. Tentando ensurepip...
    "%VENV_PY%" -m ensurepip --upgrade >nul 2>nul
    if errorlevel 1 (
        echo  [ERRO] Nao foi possivel instalar o pip no venv.
        pause
        goto menu
    )
)
echo  [..] Atualizando pip...
"%VENV_PY%" -m pip install --upgrade pip >nul 2>nul

REM 4. Dependencias reais (so se houver requirements.txt)
if exist "%APP_DIR%\requirements.txt" (
    echo  [..] Instalando dependencias de requirements.txt...
    "%VENV_PY%" -m pip install -r "%APP_DIR%\requirements.txt" >nul 2>nul
    if errorlevel 1 (
        echo  [AVISO] Algumas dependencias falharam ao instalar.
    ) else (
        echo  [OK] Dependencias instaladas.
    )
) else (
    echo  [OK] Nenhuma dependencia externa ^(usa a biblioteca padrao do Python^).
)

REM 5. Arquivos de dados
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
echo  [OK] Estrutura de dados pronta.

REM 6. Atalhos (atualiza se ja existirem)
call :criar_atalhos

echo.
echo  ============================================================
echo   INSTALACAO CONCLUIDA!
echo  ============================================================
echo.
echo  [..] Abrindo o MS-PyDOS automaticamente...
call :executar
goto menu

REM ===================== INICIAR =====================
:iniciar
cls
if exist "%VENV_PY%" (
    call :executar
) else (
    echo.
    echo  MS-PyDOS ainda nao foi instalado. Execute a opcao [1] INSTALAR primeiro.
    echo.
    pause
)
goto menu

REM ===================== EXECUTAR =====================
:executar
if not exist "%VENV_PY%" (
    echo  [ERRO] Python do venv nao encontrado. Execute a opcao [1] INSTALAR.
    pause
    goto :eof
)
if not exist "%APP%" (
    echo  [ERRO] MS-PyDOS.py nao encontrado em: %APP%
    pause
    goto :eof
)
"%VENV_PY%" "%APP%"
if errorlevel 1 (
    echo  [AVISO] O MS-PyDOS encerrou com codigo de erro.
    pause
)
goto :eof

REM ===================== ATALHOS =====================
:criar_atalhos
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "DESKTOP=%USERPROFILE%\Desktop"
set "PSFILE=%TEMP%\mspydos_atalho.ps1"
echo $ErrorActionPreference = 'Stop' > "%PSFILE%"
echo $Wsh = New-Object -ComObject WScript.Shell >> "%PSFILE%"
echo $lnk = $Wsh.CreateShortcut('%STARTMENU%\MS-PyDOS.lnk') >> "%PSFILE%"
echo $lnk.TargetPath = '%VENV_PY%' >> "%PSFILE%"
echo $lnk.Arguments = '\"%APP%\"' >> "%PSFILE%"
echo $lnk.WorkingDirectory = '%APP_DIR%' >> "%PSFILE%"
echo $lnk.Description = 'MS-PyDOS' >> "%PSFILE%"
echo $lnk.Save() >> "%PSFILE%"
echo $lnk2 = $Wsh.CreateShortcut('%DESKTOP%\MS-PyDOS.lnk') >> "%PSFILE%"
echo $lnk2.TargetPath = '%VENV_PY%' >> "%PSFILE%"
echo $lnk2.Arguments = '\"%APP%\"' >> "%PSFILE%"
echo $lnk2.WorkingDirectory = '%APP_DIR%' >> "%PSFILE%"
echo $lnk2.Description = 'MS-PyDOS' >> "%PSFILE%"
echo $lnk2.Save() >> "%PSFILE%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%PSFILE%" >nul 2>nul
if errorlevel 1 (
    echo  [AVISO] Nao foi possivel criar os atalhos.
) else (
    echo  [OK] Atalhos criados ^(Menu Iniciar e Area de Trabalho^).
)
del "%PSFILE%" >nul 2>nul
goto :eof
