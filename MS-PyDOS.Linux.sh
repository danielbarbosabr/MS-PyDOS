#!/usr/bin/env bash
# =====================================================================
#  MS-PyDOS - Instalador / Inicializador para Linux (estilo MS-DOS)
#  Opcoes: [1] Instalar  [2] Iniciar  [3] Sair
#
#  Tudo e' relativo a pasta do aplicativo. Apos a instalacao, NAO depende
#  do PATH: usa sempre o python do venv (venv/bin/python).
# =====================================================================

# Cores estilo MS-DOS (fundo azul, texto claro)
AZUL="\033[44m"
CINZA="\033[37m"
RESET="\033[0m"

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/venv"
APP="$APP_DIR/MS-PyDOS.py"
DATA_DIR="$APP_DIR/data"
DESKTOP_FILE="$HOME/.local/share/applications/ms-pydos.desktop"
VENV_PY="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

PKG_MANAGER=""

detect_pkg_manager() {
    if command -v apt-get >/dev/null 2>&1; then PKG_MANAGER="apt";
    elif command -v dnf >/dev/null 2>&1; then PKG_MANAGER="dnf";
    elif command -v pacman >/dev/null 2>&1; then PKG_MANAGER="pacman";
    elif command -v zypper >/dev/null 2>&1; then PKG_MANAGER="zypper"; fi
}

# Define PYTHON_CMD (comando executavel) ou deixa vazio.
# Ordem: python do venv -> python3 no PATH -> caminhos comuns.
find_python() {
    PYTHON_CMD=""
    if [ -x "$VENV_PY" ]; then PYTHON_CMD="$VENV_PY"; return 0; fi
    if command -v python3 >/dev/null 2>&1; then PYTHON_CMD="python3"; return 0; fi
    for p in /usr/bin/python3 /usr/local/bin/python3; do
        if [ -x "$p" ]; then PYTHON_CMD="$p"; return 0; fi
    done
    return 1
}

install_system_python() {
    detect_pkg_manager
    if [ -z "$PKG_MANAGER" ]; then
        echo "  [ERRO] Nao foi possivel detectar o gerenciador de pacotes."
        echo "          Instale o Python 3 manualmente e rode o instalador de novo."
        return 1
    fi
    echo "  [..] Python 3 nao encontrado. Instalando via $PKG_MANAGER..."
    case "$PKG_MANAGER" in
        apt)    sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip ;;
        dnf)    sudo dnf install -y python3 python3-pip ;;
        pacman) sudo pacman -S --needed --noconfirm python python-pip ;;
        zypper) sudo zypper install -y python3 python3-pip python3-virtualenv ;;
    esac
    return $?
}

print_banner() {
    clear
    local PAD="                                                            "
    local BAR
    printf -v BAR '%58s'
    BAR=${BAR// /-}
    pad() { printf '%s%s' "$1" "${PAD:0:$((56 - ${#1}))}"; }
    echo -e "${AZUL}${CINZA}"
    echo "  +${BAR}+"
    printf "  | %s |\n" "$(pad 'MS-PyDOS - PROGRAMA DE INSTALACAO')"
    echo "  +${BAR}+"
    printf "  | %s |\n" "$(pad 'SISTEMA DETECTADO: LINUX')"
    echo "  +${BAR}+"
    printf "  | %s |\n" "$(pad '[1] INSTALAR   Prepara o ambiente e abre o MS-PyDOS')"
    printf "  | %s |\n" "$(pad '[2] INICIAR    Abre o MS-PyDOS ja instalado')"
    printf "  | %s |\n" "$(pad '[3] SAIR       Encerra este instalador')"
    echo "  +${BAR}+"
    echo -e "${RESET}"
    echo ""
}

menu() {
    while true; do
        print_banner
        read -r -p "  Escolha uma opcao: " OPCAO
        case "$OPCAO" in
            1) instalar ;;
            2) iniciar ;;
            3) exit 0 ;;
            *) echo "  Opcao invalida."; sleep 1 ;;
        esac
    done
}

instalar() {
    clear
    echo "  [..] Iniciando instalacao do MS-PyDOS..."
    echo ""

    find_python
    if [ -z "$PYTHON_CMD" ]; then
        install_system_python
        find_python
    fi
    if [ -z "$PYTHON_CMD" ]; then
        echo "  [ERRO] Nao foi possivel obter nem instalar o Python."
        read -r -p "  Pressione Enter..."; return
    fi

    if ! "$PYTHON_CMD" --version >/dev/null 2>&1; then
        echo "  [ERRO] O Python encontrado nao funciona corretamente."
        read -r -p "  Pressione Enter..."; return
    fi
    echo "  [OK] Python encontrado: $("$PYTHON_CMD" --version 2>&1)"

    if [ ! -d "$VENV_DIR" ]; then
        echo "  [..] Criando ambiente virtual (venv)..."
        if ! "$PYTHON_CMD" -m venv "$VENV_DIR"; then
            echo "  [ERRO] Falha ao criar o venv."
            read -r -p "  Pressione Enter..."; return
        fi
        echo "  [OK] Ambiente virtual criado."
    else
        echo "  [OK] Ambiente virtual (venv) ja existe. Reutilizando."
    fi

    if [ ! -x "$VENV_PY" ]; then
        echo "  [ERRO] O Python do venv nao foi criado."
        read -r -p "  Pressione Enter..."; return
    fi

    if ! "$VENV_PY" -m pip --version >/dev/null 2>&1; then
        echo "  [..] pip ausente no venv. Tentando ensurepip..."
        if ! "$VENV_PY" -m ensurepip --upgrade >/dev/null 2>&1; then
            echo "  [ERRO] Nao foi possivel instalar o pip no venv."
            read -r -p "  Pressione Enter..."; return
        fi
    fi
    echo "  [..] Atualizando pip..."
    "$VENV_PY" -m pip install --upgrade pip >/dev/null 2>&1 || echo "  [AVISO] Nao foi possivel atualizar o pip."

    if [ -f "$APP_DIR/requirements.txt" ]; then
        echo "  [..] Instalando dependencias de requirements.txt..."
        if "$VENV_PY" -m pip install -r "$APP_DIR/requirements.txt" >/dev/null 2>&1; then
            echo "  [OK] Dependencias instaladas."
        else
            echo "  [AVISO] Algumas dependencias falharam ao instalar."
        fi
    else
        echo "  [OK] Nenhuma dependencia externa (usa a biblioteca padrao do Python)."
    fi

    mkdir -p "$DATA_DIR"
    echo "  [OK] Estrutura de dados pronta."

    criar_atalho

    echo ""
    echo "  ============================================================"
    echo "   INSTALACAO CONCLUIDA!"
    echo "  ============================================================"
    echo ""
    echo "  [..] Abrindo o MS-PyDOS automaticamente..."
    executar
}

iniciar() {
    clear
    if [ -x "$VENV_PY" ]; then
        executar
    else
        echo "  MS-PyDOS ainda nao foi instalado. Execute a opcao [1] INSTALAR primeiro."
        echo ""
        read -r -p "  Pressione Enter..."
    fi
}

executar() {
    if [ ! -x "$VENV_PY" ]; then
        echo "  [ERRO] Python do venv nao encontrado. Execute a opcao [1] INSTALAR."
        read -r -p "  Pressione Enter..."; return
    fi
    if [ ! -f "$APP" ]; then
        echo "  [ERRO] MS-PyDOS.py nao encontrado em: $APP"
        read -r -p "  Pressione Enter..."; return
    fi
    "$VENV_PY" "$APP"
    if [ $? -ne 0 ]; then
        echo "  [AVISO] O MS-PyDOS encerrou com codigo de erro."
    fi
}

criar_atalho() {
    mkdir -p "$(dirname "$DESKTOP_FILE")"
    cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=MS-PyDOS
Comment=Simulador de sistema operacional em Python
Exec=$VENV_PY $APP
Path=$APP_DIR
Terminal=true
Type=Application
Categories=System;Utility;
EOF
    chmod +x "$DESKTOP_FILE"
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$(dirname "$DESKTOP_FILE")" 2>/dev/null || true
    fi
    echo "  [OK] Atalho criado em $DESKTOP_FILE"
}

menu
