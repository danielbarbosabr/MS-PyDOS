import time
import sys
import os
import json
import re
import random
import subprocess
import platform
import socket
import shutil
import webbrowser
import hashlib
from urllib.parse import quote_plus
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

# --- CORES E ESTILO "MS-DOS OFICIAL" (fundo azul, texto cinza claro, molduras CP437) ---
def _ansi_suportado():
    """Detecta se o terminal atual interpreta corretamente códigos ANSI.
    No cmd.exe clássico do Windows isso precisa ser ativado manualmente (VT100);
    se não for possível ativar, ou se a saída não for um terminal real (ex.: redirecionada
    para um arquivo), as cores são desligadas para não aparecerem como texto bruto (←[44m etc.)."""
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    if platform.system() == "Windows":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            STD_OUTPUT_HANDLE = -11
            handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            modo_atual = ctypes.c_uint32()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(modo_atual)):
                return False
            novo_modo = modo_atual.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            if not kernel32.SetConsoleMode(handle, novo_modo):
                return False
            return True
        except Exception:
            return False
    return True

_ANSI_OK = _ansi_suportado()

def _cor(codigo):
    return codigo if _ANSI_OK else ""

# --- CORES E ESTILO "MS-DOS OFICIAL" (estilo telas de instalação DOS 4.0 SELECT/Setup) ---
def _ansi_suportado():
    """Detecta se o terminal atual interpreta corretamente códigos ANSI.
    No cmd.exe clássico do Windows isso precisa ser ativado manualmente (VT100);
    se não for possível ativar, ou se a saída não for um terminal real (ex.: redirecionada
    para um arquivo), as cores são desligadas para não aparecerem como texto bruto (←[44m etc.)."""
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    if platform.system() == "Windows":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            STD_OUTPUT_HANDLE = -11
            handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            modo_atual = ctypes.c_uint32()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(modo_atual)):
                return False
            novo_modo = modo_atual.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            if not kernel32.SetConsoleMode(handle, novo_modo):
                return False
            return True
        except Exception:
            return False
    return True

_ANSI_OK = _ansi_suportado()

def _cor(codigo):
    return codigo if _ANSI_OK else ""

COR_RESET = _cor("\033[0m")
COR_FUNDO_AZUL = _cor("\033[44m")
COR_TEXTO = _cor("\033[37m")
COR_TEXTO_BRILHANTE = _cor("\033[1;37m")
COR_AMARELO = _cor("\033[1;33m")
COR_VERDE = _cor("\033[1;32m")
COR_VERMELHO = _cor("\033[1;31m")
COR_CIANO = _cor("\033[1;36m")
COR_REVERSO = _cor("\033[7m")
COR_REVERSO_OFF = _cor("\033[27m")

def dos_ligar_tela_azul():
    """Mantido por compatibilidade; o estilo atual (DOS 4.0 SELECT/Setup) usa o fundo
    padrão do terminal em vez de forçar azul, então esta função não altera mais nada."""
    pass

def dos_desligar_tela_azul():
    sys.stdout.write(COR_RESET)
    sys.stdout.flush()

def dos_txt(texto, cor=""):
    return f"{cor}{texto}{COR_TEXTO}" if cor else texto

# --- HELPERS DE FORMATAÇÃO DE TELA (estilo telas de instalação do MS-DOS 4.0, ex.: SELECT/Setup) ---
def desenhar_titulo(texto, largura=68):
    """Imprime um cabeçalho estilo tela de instalação do MS-DOS, ex.:
                                Welcome
    ────────────────────────────────────────────────────────────
    """
    print()
    print(COR_TEXTO_BRILHANTE + texto.center(largura) + COR_TEXTO)
    print(COR_TEXTO_BRILHANTE + "─" * largura + COR_TEXTO)

def desenhar_rodape(largura=68):
    print(COR_TEXTO_BRILHANTE + "─" * largura + COR_TEXTO)

def desenhar_divisoria(largura=68):
    print(COR_TEXTO_BRILHANTE + "─" * largura + COR_TEXTO)

def desenhar_barra_acoes(opcoes, largura=68):
    """Barra de teclas de ação em vídeo reverso, como no rodapé do DOS 4.0 SELECT
    (ex.: [ Enter ] [ Esc=Cancel ])."""
    partes = []
    for tecla, rotulo in opcoes:
        texto = f" {tecla} " if not rotulo else f" {tecla}={rotulo} "
        partes.append(f"{COR_REVERSO}{texto}{COR_REVERSO_OFF}")
    print("  " + "   ".join(partes))
    print()

def pausar_tela(mensagem="Pressione ENTER para continuar..."):
    input("\n" + mensagem)

# --- CLASSE CPU ---
class CPU:
    def __init__(self):
        self.ciclos = 0

    def executar(self, comando):
        self.ciclos += 1
        return comando.split()

    def obter_info(self):
        return {
            "ciclos": self.ciclos
        }

    def limparcpu(self):
        self.ciclos = 0

# --- CLASSE RAM ---
class RAM:
    def __init__(self, tamanho_kb=128 * 1024):
        self.tamanho_kb = tamanho_kb
        self.memoria = {}

    def carregar(self, chave, valor):
        if len(self.memoria) < (self.tamanho_kb * 1024):
            self.memoria[chave] = valor
        else:
            print("[RAM] Memória insuficiente!")

    def obter(self, chave):
        return self.memoria.get(chave, None)

    def limpar(self):
        self.memoria = {}

    def obter_info(self):
        return {
            "total_kb": self.tamanho_kb,
            "usado_kb": len(self.memoria),
            "livre_kb": self.tamanho_kb - len(self.memoria)
        }

# ------------------------------------------------------------
# ARMAZENAMENTO ÚNICO EM DISCO
# Todo o estado persistente do MS-PyDOS (sistema de arquivos virtual
# do DISCO e o cadastro de USUÁRIOS) fica salvo em um único arquivo
# JSON, sempre na mesma pasta do script, cada um em sua própria seção
# ("disco" e "usuarios") para não sobrescrever o outro.
# ------------------------------------------------------------
PASTA_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(PASTA_DADOS, exist_ok=True)
CAMINHO_DADOS_PADRAO = os.path.join(PASTA_DADOS, "ms-pydos-dados.json")

def _carregar_dados_completos(arquivo):
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            conteudo = json.load(f)
            return conteudo if isinstance(conteudo, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _salvar_dados_completos(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def _ler_secao(arquivo, secao):
    return _carregar_dados_completos(arquivo).get(secao, {})

def _gravar_secao(arquivo, secao, conteudo_secao):
    dados = _carregar_dados_completos(arquivo)
    dados[secao] = conteudo_secao
    _salvar_dados_completos(arquivo, dados)

def _migrar_arquivos_antigos_se_necessario():
    """Se ainda existirem os arquivos antigos separados (disco.json / usuarios.json)
    de versões anteriores do MS-PyDOS e o arquivo único ainda não tiver essas seções,
    importa o conteúdo deles para o novo arquivo único."""
    pasta = os.path.dirname(os.path.abspath(__file__))
    caminho_disco_antigo = os.path.join(pasta, "disco.json")
    caminho_usuarios_antigo = os.path.join(pasta, "usuarios.json")
    dados_atuais = _carregar_dados_completos(CAMINHO_DADOS_PADRAO)
    alterado = False

    if "disco" not in dados_atuais and os.path.exists(caminho_disco_antigo):
        conteudo_antigo = _carregar_dados_completos(caminho_disco_antigo)
        if conteudo_antigo:
            dados_atuais["disco"] = conteudo_antigo
            alterado = True

    if "usuarios" not in dados_atuais and os.path.exists(caminho_usuarios_antigo):
        conteudo_antigo = _carregar_dados_completos(caminho_usuarios_antigo)
        if conteudo_antigo:
            dados_atuais["usuarios"] = conteudo_antigo
            alterado = True

    if alterado:
        _salvar_dados_completos(CAMINHO_DADOS_PADRAO, dados_atuais)

_migrar_arquivos_antigos_se_necessario()

# --- CLASSE DISCO ---
class Disco:
    def __init__(self, arquivo=None, tamanho_max_kb=512 * 1024):
        self.arquivo = arquivo or CAMINHO_DADOS_PADRAO
        self.tamanho_max_kb = tamanho_max_kb
        self.rotulo = "MS-PYDOS"
        if not os.path.exists(self.arquivo):
            self.formatar()

    def formatar(self):
        _gravar_secao(self.arquivo, "disco", {})

    def _carregar(self):
        return _ler_secao(self.arquivo, "disco")

    def _salvar(self, dados):
        _gravar_secao(self.arquivo, "disco", dados)

    def _dividir_caminho(self, caminho):
        return [p for p in caminho.strip("/").split("/") if p]

    def _navegar(self, dados, partes_caminho, criar_faltando=False):
        for parte in partes_caminho[:-1]:
            if parte not in dados:
                if criar_faltando:
                    dados[parte] = {}
                else:
                    return None
            dados = dados[parte]
            if not isinstance(dados, dict):
                return None
        return dados

    def escrever_arquivo(self, caminho_arquivo, conteudo):
        dados = self._carregar()
        partes_caminho = self._dividir_caminho(caminho_arquivo)
        if not partes_caminho:
            print("[DISCO] Caminho de arquivo inválido.")
            return
        pai = self._navegar(dados, partes_caminho, criar_faltando=True)
        if pai is None:
            print("[DISCO] Caminho inválido")
            return
        pai[partes_caminho[-1]] = conteudo
        if self._obter_espaco_usado_kb(dados) <= self.tamanho_max_kb:
            self._salvar(dados)
        else:
            print("[DISCO] Espaço insuficiente! Escrita falhou.")
            del pai[partes_caminho[-1]]

    def ler_arquivo(self, caminho_arquivo):
        dados = self._carregar()
        partes_caminho = self._dividir_caminho(caminho_arquivo)
        if not partes_caminho:
            return "[Arquivo não encontrado]"
        pai = dados
        for parte in partes_caminho[:-1]:
            if parte in pai and isinstance(pai[parte], dict):
                pai = pai[parte]
            else:
                return "[Arquivo não encontrado]"
        ultima_parte = partes_caminho[-1]
        if ultima_parte in pai:
            if isinstance(pai[ultima_parte], dict):
                return "[É uma pasta]"
            return pai[ultima_parte]
        return "[Arquivo não encontrado]"

    def apagar_arquivo(self, caminho_arquivo):
        dados = self._carregar()
        partes_caminho = self._dividir_caminho(caminho_arquivo)
        if not partes_caminho:
            return
        pai = self._navegar(dados, partes_caminho)
        if pai and partes_caminho[-1] in pai:
            del pai[partes_caminho[-1]]
            self._salvar(dados)

    def criar_pasta(self, caminho_pasta):
        dados = self._carregar()
        partes_caminho = self._dividir_caminho(caminho_pasta)
        if not partes_caminho:
            print("[DISCO] Caminho de pasta inválido.")
            return
        pai = self._navegar(dados, partes_caminho, criar_faltando=True)
        if pai is None:
            print("[DISCO] Caminho inválido")
            return
        nome_pasta = partes_caminho[-1]
        if nome_pasta not in pai:
            pai[nome_pasta] = {}
            self._salvar(dados)
        else:
            print("[DISCO] Pasta já existe")

    def listar_diretorio(self, caminho_pasta):
        dados = self._carregar()
        partes_caminho = self._dividir_caminho(caminho_pasta)
        if len(partes_caminho) == 0:
            pai = dados
        else:
            pai = dados
            for parte in partes_caminho:
                if parte in pai and isinstance(pai[parte], dict):
                    pai = pai[parte]
                else:
                    return []
        if isinstance(pai, dict):
            return list(pai.keys())
        return []

    def e_pasta(self, caminho):
        dados = self._carregar()
        partes_caminho = self._dividir_caminho(caminho)
        if len(partes_caminho) == 0:
            return True
        pai = dados
        for parte in partes_caminho[:-1]:
            if parte in pai and isinstance(pai[parte], dict):
                pai = pai[parte]
            else:
                return False
        ultimo = partes_caminho[-1]
        return isinstance(pai.get(ultimo, None), dict)

    def _obter_espaco_usado_kb(self, dados):
        def percorrer(d):
            total = 0
            for k, v in d.items():
                total += len(k.encode("utf-8"))
                if isinstance(v, dict):
                    total += percorrer(v)
                else:
                    total += len(v.encode("utf-8"))
            return total
        return percorrer(dados) // 1024

    def obter_info(self):
        dados = self._carregar()
        usado = self._obter_espaco_usado_kb(dados)
        return {
            "max_kb": self.tamanho_max_kb,
            "usado_kb": usado,
            "livre_kb": self.tamanho_max_kb - usado,
            "total_arquivos": self._contar_arquivos(dados)
        }

    def _contar_arquivos(self, d):
        contador = 0
        for v in d.values():
            if isinstance(v, dict):
                contador += self._contar_arquivos(v)
            else:
                contador += 1
        return contador

    def escrever_em_massa(self, dicionario_dados):
        dados = self._carregar()

        for caminho_arquivo, conteudo in dicionario_dados.items():
            partes_caminho = self._dividir_caminho(caminho_arquivo)
            if not partes_caminho:
                continue

            pai = dados
            for parte in partes_caminho[:-1]:
                if parte not in pai or not isinstance(pai[parte], dict):
                    pai[parte] = {}
                pai = pai[parte]
            pai[partes_caminho[-1]] = conteudo
        if self._obter_espaco_usado_kb(dados) <= self.tamanho_max_kb:
            self._salvar(dados)
        else:
            print("[DISCO] Espaço insuficiente! Escrita em massa falhou.")

# ============================================================
# GERENCIAMENTO DE USUÁRIOS (cadastro/login real, persistente em disco)
# ============================================================

# ------------------------------------------------------------
# VALIDADORES (CPF e CEP)
# ------------------------------------------------------------
def validar_cpf(cpf):
    """Valida um CPF (formatado ou não) usando os dígitos verificadores oficiais."""
    if not cpf:
        return False
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    digito1 = 0 if resto == 10 else resto
    if digito1 != int(cpf[9]):
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    digito2 = 0 if resto == 10 else resto
    if digito2 != int(cpf[10]):
        return False
    return True

def formatar_cpf(cpf):
    cpf = re.sub(r"\D", "", cpf)
    return f"{cpf[0:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"

def validar_cep(cep):
    """Valida um CEP (formatado ou não): precisa ter exatamente 8 dígitos."""
    if not cep:
        return False
    cep = re.sub(r"\D", "", cep)
    return len(cep) == 8

def formatar_cep(cep):
    cep = re.sub(r"\D", "", cep)
    return f"{cep[0:5]}-{cep[5:8]}"


class GerenciadorUsuarios:
    """Cadastro e autenticação de usuários do MS-PyDOS.
    Senhas nunca são gravadas em texto puro: são armazenadas como hash SHA-256 + salt."""

    def __init__(self, arquivo=None):
        self.arquivo = arquivo or CAMINHO_DADOS_PADRAO
        if not os.path.exists(self.arquivo):
            self._salvar({})

    def _carregar(self):
        return _ler_secao(self.arquivo, "usuarios")

    def _salvar(self, dados):
        _gravar_secao(self.arquivo, "usuarios", dados)

    def _hash_senha(self, senha, salt):
        return hashlib.sha256((salt + senha).encode("utf-8")).hexdigest()

    def existe_algum_usuario(self):
        return len(self._carregar()) > 0

    def usuario_existe(self, nome):
        return nome.lower() in {u.lower() for u in self._carregar().keys()}

    def cadastrar(self, nome, senha, cpf=None, cep=None):
        nome = nome.strip()
        if not nome or " " in nome:
            return False, "Nome de usuário inválido (não pode ser vazio nem ter espaços)."
        if self.usuario_existe(nome):
            return False, "Já existe um usuário com esse nome."
        if len(senha) < 3:
            return False, "A senha deve ter pelo menos 3 caracteres."
        if not validar_cpf(cpf):
            return False, "CPF inválido."
        if not validar_cep(cep):
            return False, "CEP inválido (deve ter 8 dígitos)."
        dados = self._carregar()
        salt = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
        # Tudo (login, senha, CPF e CEP) fica salvo no único arquivo JSON do MS-PyDOS.
        dados[nome] = {
            "senha_hash": self._hash_senha(senha, salt),
            "salt": salt,
            "cpf": formatar_cpf(cpf),
            "cep": formatar_cep(cep),
            "criado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        self._salvar(dados)
        return True, f"Usuário '{nome}' cadastrado com sucesso!"

    def autenticar(self, nome, senha):
        dados = self._carregar()
        for usuario, info in dados.items():
            if usuario.lower() == nome.strip().lower():
                if info["senha_hash"] == self._hash_senha(senha, info["salt"]):
                    return True, usuario
                return False, "Senha incorreta."
        return False, "Usuário não encontrado."

    def listar(self):
        return self._carregar()

    def trocar_senha(self, nome, senha_atual, senha_nova):
        ok, resultado = self.autenticar(nome, senha_atual)
        if not ok:
            return False, resultado
        if len(senha_nova) < 3:
            return False, "A nova senha deve ter pelo menos 3 caracteres."
        dados = self._carregar()
        salt = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
        dados[resultado]["senha_hash"] = self._hash_senha(senha_nova, salt)
        dados[resultado]["salt"] = salt
        self._salvar(dados)
        return True, "Senha alterada com sucesso!"


def _ler_senha_oculta(prompt="Senha: "):
    """Lê a senha do usuário.
    Tentamos usar getpass (esconde os caracteres digitados), mas em muitos
    terminais/IDEs (VS Code, Thonny, alguns terminais do Windows, ambientes
    web, etc.) o getpass trava ou simplesmente não aceita a digitação, porque
    ele lê as teclas direto do console em baixo nível. Para garantir que o
    cadastro/login SEMPRE funcione, usamos entrada normal e visível (input())
    como padrão — assim como as telas de instalação originais do MS-DOS, que
    também não escondiam a senha digitada."""
    try:
        return input(prompt)
    except EOFError:
        return ""


def tela_cadastro_usuario(gerenciador, obrigatorio=False):
    """Tela de cadastro de usuário no estilo das telas de instalação MS-DOS SELECT/Setup."""
    while True:
        desenhar_titulo("Welcome to MS-PyDOS Setup", 60)
        print("  Vamos criar sua conta de usuário para o MS-PyDOS.")
        print("  Escolha um nome de usuário e uma senha para proteger")
        print("  o acesso ao sistema.")
        print()
        desenhar_divisoria(60)
        desenhar_barra_acoes([("ENTER", "Confirmar"), ("CTRL+C", "Cancelar")], 60)
        try:
            nome = input("  Nome de usuário.......: ").strip()
            senha = _ler_senha_oculta("  Senha.................: ")
            confirmar = _ler_senha_oculta("  Confirme a senha......: ")
            cpf = input("  CPF...................: ").strip()
            cep = input("  CEP...................: ").strip()
        except KeyboardInterrupt:
            print("\n[CANCELADO]\n")
            if obrigatorio:
                print("É necessário criar uma conta para usar o MS-PyDOS.\n")
                continue
            return None
        desenhar_rodape(60)

        if senha != confirmar:
            print("[ERRO] As senhas não coincidem. Tente novamente.\n")
            continue

        if not validar_cpf(cpf):
            print("[ERRO] CPF inválido. Digite os 11 dígitos (com ou sem pontuação).\n")
            continue

        if not validar_cep(cep):
            print("[ERRO] CEP inválido. Digite os 8 dígitos (com ou sem hífen).\n")
            continue

        ok, msg = gerenciador.cadastrar(nome, senha, cpf, cep)
        if ok:
            print(f"[OK] {msg}\n")
            return nome
        else:
            print(f"[ERRO] {msg}\n")
            if not obrigatorio:
                resposta = input("Deseja tentar novamente? (s/n): ").strip().lower()
                if resposta != "s":
                    return None


def tela_login(gerenciador):
    """Tela de login estilo MS-DOS Setup. Permite autenticar ou cadastrar um novo usuário."""
    tentativas = 0
    while tentativas < 5:
        desenhar_titulo("MS-PyDOS - Login", 60)
        print("  Digite seu usuário e senha para continuar.")
        print("  Digite CADASTRAR no campo usuário para criar uma conta.")
        print()
        desenhar_divisoria(60)
        desenhar_barra_acoes([("ENTER", "Confirmar"), ("CTRL+C", "Sair")], 60)
        try:
            nome = input("  Usuário...............: ").strip()
            if nome.lower() == "cadastrar":
                desenhar_rodape(60)
                return tela_cadastro_usuario(gerenciador)
            senha = _ler_senha_oculta("  Senha.................: ")
        except KeyboardInterrupt:
            print("\n[CANCELADO] Encerrando o MS-PyDOS.")
            sys.exit()
        desenhar_rodape(60)

        ok, resultado = gerenciador.autenticar(nome, senha)
        if ok:
            print(f"[OK] Bem-vindo(a), {resultado}!\n")
            return resultado
        else:
            tentativas += 1
            print(f"[ERRO] {resultado} (tentativa {tentativas}/5)\n")

    print("[ERRO] Número máximo de tentativas excedido. Encerrando o MS-PyDOS.")
    sys.exit()


def tela_boas_vindas_usuario(gerenciador):
    """Decide se mostra a tela de cadastro (primeiro uso) ou a tela de login (já existem usuários)."""
    if not gerenciador.existe_algum_usuario():
        print("\nNenhum usuário cadastrado neste MS-PyDOS. É necessário criar uma conta.")
        return tela_cadastro_usuario(gerenciador, obrigatorio=True)
    return tela_login(gerenciador)

# ============================================================
# SIMULADOR DE SISTEMA OPERACIONAL (SSO)
# Implementa os requisitos pedidos pelo professor: processos,
# escalonamento Round Robin, memória (First Fit), arquivos,
# recursos compartilhados, semáforos, log e estatísticas.
# ============================================================

class EstadoProcesso(Enum):
    NOVO = 1
    PRONTO = 2
    EXECUTANDO = 3
    BLOQUEADO = 4
    TERMINADO = 5

class TipoRecurso(Enum):
    IMPRESSORA = 1
    DISCO = 2
    FITA = 3

@dataclass
class PCB:
    pid: int
    nome: str
    prioridade: int
    estado: EstadoProcesso
    tempo_cpu: int
    tempo_total: int
    memoria_alocada: int
    arquivos_abertos: List[str] = field(default_factory=list)
    recursos: List[TipoRecurso] = field(default_factory=list)
    pc: int = 0
    tempo_chegada: float = 0
    tempo_resposta: Optional[float] = None

@dataclass
class ParticaoMemoria:
    tamanho: int
    ocupada: bool = False
    pid: Optional[int] = None
    memoria_usada: int = 0
    inicio: int = 0
    fim: int = 0

@dataclass
class Arquivo:
    nome: str
    tamanho: int
    aberto: bool
    pid_dono: int
    dados: str
    data_criacao: str

# ------------------------------------------------------------
# PERSISTÊNCIA REAL DOS ARQUIVOS DO SIMULADOR SO (ARQUIVOSSO)
# Antes esses arquivos existiam só na RAM e sumiam ao fechar o
# programa. Agora eles são salvos de verdade, na seção "arquivosso"
# do mesmo arquivo único (ms-pydos-dados.json), então continuam lá
# mesmo depois de fechar e abrir o MS-PyDOS de novo.
# ------------------------------------------------------------
def _arquivo_so_para_dict(arquivo):
    return {
        "nome": arquivo.nome,
        "tamanho": arquivo.tamanho,
        "pid_dono": arquivo.pid_dono,
        "dados": arquivo.dados,
        "data_criacao": arquivo.data_criacao,
    }

def _dict_para_arquivo_so(nome, info):
    return Arquivo(
        nome=info.get("nome", nome),
        tamanho=info.get("tamanho", 0),
        aberto=False,  # ao carregar, os arquivos sempre começam fechados
        pid_dono=info.get("pid_dono", 0),
        dados=info.get("dados", ""),
        data_criacao=info.get("data_criacao", ""),
    )

@dataclass
class Recurso:
    tipo: TipoRecurso
    disponivel: bool = True
    pid_dono: Optional[int] = None


class SimuladorSO:
    def __init__(self, memoria_total=1024, quantum=2, arquivo_persistencia=None):
        # Processos
        self.processos: Dict[int, PCB] = {}
        self.proximo_pid = 1000
        self.num_processos = 0
        self.processo_atual = None
        self.fila_prontos = []
        self.fila_bloqueados = []
        # Escalonamento
        self.quantum = quantum
        self.clock = 0
        # Memória
        self.memoria_total = memoria_total
        self.memoria_utilizada = 0
        self.particoes = []
        self.criar_particoes()
        # Arquivos (persistidos de verdade, ver _carregar_arquivos_persistidos)
        self.arquivo_persistencia = arquivo_persistencia or CAMINHO_DADOS_PADRAO
        self.arquivos = {}
        self._carregar_arquivos_persistidos()
        # Recursos
        self.recursos = {
            TipoRecurso.IMPRESSORA: Recurso(TipoRecurso.IMPRESSORA),
            TipoRecurso.DISCO: Recurso(TipoRecurso.DISCO),
            TipoRecurso.FITA: Recurso(TipoRecurso.FITA),
        }
        # Semáforos
        self.semaforos = {
            "mutex": 1,
            "recurso": 1
        }
        # Estatísticas
        self.tempo_total_execucao = 0
        self.total_processos_criados = 0
        self.total_processos_finalizados = 0
        # Log
        self.log = []
        entrada_inicial = f"[{self.clock:>6}] Módulo de processos do MS-PyDOS inicializado com sucesso!"
        self.log.append(entrada_inicial)
        print("Módulo de processos do MS-PyDOS inicializado com sucesso!")
        print(f"  Memória virtual: {self.memoria_total} KB em {len(self.particoes)} partição(ões) | Quantum: {self.quantum}")

    # ---------------- MEMÓRIA ----------------
    def criar_particoes(self):
        tamanhos = [64, 128, 256, 64, 256, 128, 64, 64]
        restante = self.memoria_total
        offset = 0
        for tamanho_base in tamanhos:
            if restante <= 0:
                break
            tamanho = min(tamanho_base, restante)
            particao = ParticaoMemoria(tamanho=tamanho, inicio=offset, fim=offset + tamanho - 1)
            self.particoes.append(particao)
            offset += tamanho
            restante -= tamanho
        if restante > 0:
            self.particoes.append(ParticaoMemoria(tamanho=restante, inicio=offset, fim=offset + restante - 1))

    def alocar_memoria(self, tamanho, pid):
        for indice, particao in enumerate(self.particoes):
            if not particao.ocupada and particao.tamanho >= tamanho:
                particao.ocupada = True
                particao.pid = pid
                particao.memoria_usada = tamanho
                self.memoria_utilizada += tamanho
                self.log_evento(f"Memória alocada: {tamanho} KB na partição {indice + 1}")
                return True
        self.log_evento(f"ERRO: Nenhuma partição comporta {tamanho} KB")
        return False

    def liberar_memoria(self, pid):
        for indice, particao in enumerate(self.particoes):
            if particao.ocupada and particao.pid == pid:
                liberada = particao.memoria_usada
                self.memoria_utilizada -= liberada
                particao.ocupada = False
                particao.pid = None
                particao.memoria_usada = 0
                self.log_evento(f"Memória liberada: {liberada} KB da partição {indice + 1}")

    def exibir_memoria(self):
        desenhar_titulo("ESTADO DA MEMÓRIA PRINCIPAL", 70)
        print(f"Memória Total      : {self.memoria_total} KB")
        print(f"Memória Utilizada  : {self.memoria_utilizada} KB")
        print(f"Memória Livre      : {self.memoria_total - self.memoria_utilizada} KB")
        taxa = (self.memoria_utilizada / self.memoria_total) * 100 if self.memoria_total else 0
        print(f"Taxa de Utilização : {taxa:.2f}%")
        desenhar_divisoria(70)
        for i, particao in enumerate(self.particoes, 1):
            if particao.ocupada:
                status = "OCUPADA"
                dono = "PID " + str(particao.pid)
            else:
                status = "LIVRE"
                dono = "---"
            print(f"Partição {i:2}: {particao.tamanho:4} KB | {status:7} | Uso: {particao.memoria_usada:4} KB | {dono}")
        desenhar_rodape(70)

    # ---------------- PROCESSOS ----------------
    def criar_processo(self, nome, prioridade, tempo_total, memoria):
        nome = nome.strip()
        if nome == "":
            self.log_evento("ERRO: Nome do processo vazio")
            return None
        if prioridade < 1 or prioridade > 10:
            self.log_evento("ERRO: Prioridade deve ser entre 1 e 10")
            return None
        if tempo_total <= 0:
            self.log_evento("ERRO: Tempo deve ser maior que zero")
            return None
        if memoria <= 0:
            self.log_evento("ERRO: Memória deve ser maior que zero")
            return None
        pid = self.proximo_pid
        self.log_evento("Criando processo: " + nome)
        if not self.alocar_memoria(memoria, pid):
            return None
        self.proximo_pid += 1
        self.total_processos_criados += 1
        pcb = PCB(
            pid=pid, nome=nome, prioridade=prioridade, estado=EstadoProcesso.NOVO,
            tempo_cpu=0, tempo_total=tempo_total, memoria_alocada=memoria, tempo_chegada=self.clock
        )
        self.processos[pid] = pcb
        self.num_processos += 1
        self.adicionar_fila_prontos(pid)
        self.log_evento(f"Processo {nome} criado. PID: {pid}")
        return pid

    def adicionar_fila_prontos(self, pid):
        if pid not in self.processos:
            return
        pcb = self.processos[pid]
        if pcb.estado == EstadoProcesso.TERMINADO:
            return
        if pid not in self.fila_prontos:
            self.fila_prontos.append(pid)
        pcb.estado = EstadoProcesso.PRONTO

    def remover_fila_prontos(self, pid):
        if pid in self.fila_prontos:
            self.fila_prontos.remove(pid)

    def escalonar(self):
        if self.processo_atual is not None:
            pcb = self.processos.get(self.processo_atual)
            if pcb is not None and pcb.estado == EstadoProcesso.EXECUTANDO:
                return
        while self.fila_prontos:
            pid = self.fila_prontos.pop(0)
            pcb = self.processos.get(pid)
            if pcb is None:
                continue
            if pcb.estado == EstadoProcesso.TERMINADO:
                continue
            self.processo_atual = pid
            pcb.estado = EstadoProcesso.EXECUTANDO
            if pcb.tempo_resposta is None:
                pcb.tempo_resposta = self.clock - pcb.tempo_chegada
            self.log_evento(f"Escalonador: PID {pid} ({pcb.nome}) executando")
            return
        self.processo_atual = None

    def executar_processo(self):
        if self.processo_atual is None:
            self.escalonar()
        if self.processo_atual is None:
            self.log_evento("Sistema ocioso")
            self.clock += 1
            return
        pid = self.processo_atual
        pcb = self.processos[pid]
        restante = pcb.tempo_total - pcb.tempo_cpu
        tempo_executado = min(self.quantum, restante)
        pcb.tempo_cpu += tempo_executado
        pcb.pc += tempo_executado
        self.clock += tempo_executado
        self.tempo_total_execucao += tempo_executado
        self.log_evento(f"Processo {pcb.nome} executou {tempo_executado} unidade(s)")
        if pcb.tempo_cpu >= pcb.tempo_total:
            self.terminar_processo(pid)
            return
        # 20% de chance de bloqueio por E/S
        if random.random() < 0.20:
            pcb.estado = EstadoProcesso.BLOQUEADO
            if pid not in self.fila_bloqueados:
                self.fila_bloqueados.append(pid)
            self.processo_atual = None
            self.log_evento(f"Processo {pcb.nome} bloqueado para E/S")
            if pid in self.fila_bloqueados:
                self.fila_bloqueados.remove(pid)
            self.adicionar_fila_prontos(pid)
            self.log_evento(f"E/S de {pcb.nome} concluída")
        else:
            self.processo_atual = None
            self.adicionar_fila_prontos(pid)

    def terminar_processo(self, pid):
        pcb = self.processos.get(pid)
        if pcb is None:
            self.log_evento("ERRO: PID não encontrado")
            return
        if pcb.estado == EstadoProcesso.TERMINADO:
            print("Processo já terminado.")
            return
        self.liberar_memoria(pid)
        self.fechar_arquivos_processo(pid)
        self.liberar_recursos_processo(pid)
        self.remover_fila_prontos(pid)
        if pid in self.fila_bloqueados:
            self.fila_bloqueados.remove(pid)
        pcb.estado = EstadoProcesso.TERMINADO
        self.total_processos_finalizados += 1
        self.num_processos -= 1
        if self.processo_atual == pid:
            self.processo_atual = None
        self.log_evento(f"Processo {pcb.nome} (PID {pid}) terminado")

    def listar_processos(self):
        desenhar_titulo("TABELA DE PROCESSOS", 80)
        print(f"{'PID':>6} | {'Nome':<18} | {'Prior.':>6} | {'Estado':<12} | {'CPU':>9} | {'Memória':>9}")
        desenhar_divisoria(80)
        encontrou = False
        for pcb in self.processos.values():
            if pcb.estado != EstadoProcesso.TERMINADO:
                encontrou = True
                print(f"{pcb.pid:>6} | {pcb.nome:<18} | {pcb.prioridade:>6} | {pcb.estado.name:<12} | {pcb.tempo_cpu:>3}/{pcb.tempo_total:<3} | {pcb.memoria_alocada:>6} KB")
        if not encontrou:
            print("Nenhum processo ativo.")
        desenhar_rodape(80)
        print(f"Processos ativos: {self.num_processos} | Total criados: {self.total_processos_criados} | Total finalizados: {self.total_processos_finalizados}")

    # ---------------- SISTEMA DE ARQUIVOS ----------------
    def _carregar_arquivos_persistidos(self):
        dados_salvos = _ler_secao(self.arquivo_persistencia, "arquivosso")
        for nome, info in dados_salvos.items():
            self.arquivos[nome] = _dict_para_arquivo_so(nome, info)

    def _salvar_arquivos_persistidos(self):
        dados = {nome: _arquivo_so_para_dict(arquivo) for nome, arquivo in self.arquivos.items()}
        _gravar_secao(self.arquivo_persistencia, "arquivosso", dados)

    def criar_arquivo(self, nome, pid_dono):
        nome = nome.strip()
        if nome == "":
            self.log_evento("ERRO: Nome vazio")
            return False
        if nome in self.arquivos:
            self.log_evento("ERRO: Arquivo já existe")
            return False
        pcb = self.processos.get(pid_dono)
        if pcb is None or pcb.estado == EstadoProcesso.TERMINADO:
            self.log_evento("ERRO: Processo dono inválido")
            return False
        arquivo = Arquivo(nome=nome, tamanho=0, aberto=False, pid_dono=pid_dono, dados="", data_criacao=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        self.arquivos[nome] = arquivo
        self._salvar_arquivos_persistidos()
        self.log_evento(f"Arquivo '{nome}' criado")
        return True

    def abrir_arquivo(self, nome):
        arquivo = self.arquivos.get(nome)
        if arquivo is None:
            self.log_evento("ERRO: Arquivo não encontrado")
            return False
        if arquivo.aberto:
            self.log_evento("ERRO: Arquivo já aberto")
            return False
        arquivo.aberto = True
        pcb = self.processos.get(arquivo.pid_dono)
        if pcb is not None and nome not in pcb.arquivos_abertos:
            pcb.arquivos_abertos.append(nome)
        self.log_evento(f"Arquivo '{nome}' aberto")
        return True

    def fechar_arquivo(self, nome):
        arquivo = self.arquivos.get(nome)
        if arquivo is None:
            self.log_evento("ERRO: Arquivo não encontrado")
            return False
        if not arquivo.aberto:
            self.log_evento("ERRO: Arquivo já fechado")
            return False
        arquivo.aberto = False
        pcb = self.processos.get(arquivo.pid_dono)
        if pcb is not None and nome in pcb.arquivos_abertos:
            pcb.arquivos_abertos.remove(nome)
        self.log_evento(f"Arquivo '{nome}' fechado")
        return True

    def escrever_arquivo(self, nome, dados):
        arquivo = self.arquivos.get(nome)
        if arquivo is None:
            print("Arquivo não encontrado.")
            return False
        if not arquivo.aberto:
            print("Abra o arquivo primeiro.")
            return False
        arquivo.dados += dados + "\n"
        bytes_dados = len(arquivo.dados.encode("utf-8"))
        arquivo.tamanho = max(1, bytes_dados // 1024 + 1)
        self._salvar_arquivos_persistidos()
        self.log_evento(f"Dados escritos em '{nome}'")
        return True

    def ler_arquivo(self, nome):
        arquivo = self.arquivos.get(nome)
        if arquivo is None:
            print("Arquivo não encontrado.")
            return None
        if not arquivo.aberto:
            print("Abra o arquivo primeiro.")
            return None
        self.log_evento(f"Arquivo '{nome}' lido")
        return arquivo.dados

    def deletar_arquivo(self, nome):
        arquivo = self.arquivos.get(nome)
        if arquivo is None:
            print("Arquivo não encontrado.")
            return False
        if arquivo.aberto:
            print("Feche o arquivo antes de deletar.")
            return False
        del self.arquivos[nome]
        self._salvar_arquivos_persistidos()
        self.log_evento(f"Arquivo '{nome}' deletado")
        return True

    def fechar_arquivos_processo(self, pid):
        for arquivo in self.arquivos.values():
            if arquivo.pid_dono == pid and arquivo.aberto:
                arquivo.aberto = False

    def listar_arquivos(self):
        desenhar_titulo("ARQUIVOS DO SISTEMA", 70)
        if not self.arquivos:
            print("Nenhum arquivo cadastrado.")
        else:
            for arquivo in self.arquivos.values():
                status = "ABERTO" if arquivo.aberto else "FECHADO"
                print(f"Nome: {arquivo.nome} | Tamanho: {arquivo.tamanho} KB | Status: {status} | Dono PID: {arquivo.pid_dono} | Criado em: {arquivo.data_criacao}")
        desenhar_rodape(70)

    # ---------------- RECURSOS E SEMÁFOROS ----------------
    def semaforo_p(self, nome):
        if nome not in self.semaforos:
            print("Semáforo inexistente.")
            return False
        if self.semaforos[nome] <= 0:
            print("Semáforo indisponível.")
            return False
        self.semaforos[nome] -= 1
        self.log_evento(f"Operação P em {nome}")
        return True

    def semaforo_v(self, nome):
        if nome not in self.semaforos:
            print("Semáforo inexistente.")
            return False
        self.semaforos[nome] = min(1, self.semaforos[nome] + 1)
        self.log_evento(f"Operação V em {nome}")
        return True

    def listar_semaforos(self):
        desenhar_titulo("SEMÁFOROS DO SISTEMA", 40)
        for nome, valor in self.semaforos.items():
            estado = "LIVRE" if valor > 0 else "OCUPADO"
            print(f"{nome} = {valor} ({estado})")
        desenhar_rodape(40)

    def solicitar_recurso(self, pid, tipo):
        pcb = self.processos.get(pid)
        if pcb is None or pcb.estado == EstadoProcesso.TERMINADO:
            print("Processo inválido.")
            return False
        recurso = self.recursos[tipo]
        if recurso.pid_dono == pid:
            print("O processo já possui esse recurso.")
            return True
        if not recurso.disponivel:
            print("Recurso ocupado.")
            return False
        recurso.disponivel = False
        recurso.pid_dono = pid
        if tipo not in pcb.recursos:
            pcb.recursos.append(tipo)
        self.log_evento(f"{tipo.name} alocado ao PID {pid}")
        return True

    def liberar_recurso(self, pid, tipo):
        recurso = self.recursos[tipo]
        if recurso.pid_dono != pid:
            print("O processo não possui esse recurso.")
            return False
        recurso.disponivel = True
        recurso.pid_dono = None
        pcb = self.processos.get(pid)
        if pcb is not None and tipo in pcb.recursos:
            pcb.recursos.remove(tipo)
        self.log_evento(f"{tipo.name} liberado pelo PID {pid}")
        return True

    def liberar_recursos_processo(self, pid):
        pcb = self.processos.get(pid)
        if pcb is None:
            return
        for tipo in list(pcb.recursos):
            self.liberar_recurso(pid, tipo)

    def listar_recursos(self):
        desenhar_titulo("RECURSOS DO SISTEMA", 60)
        for tipo, recurso in self.recursos.items():
            status = "DISPONÍVEL" if recurso.disponivel else ("OCUPADO - PID " + str(recurso.pid_dono))
            print(f"{tipo.name:<12}: {status}")
        print("\nSEMÁFOROS")
        for nome, valor in self.semaforos.items():
            print(f"{nome} = {valor}")
        desenhar_rodape(60)

    # ---------------- LOG / ESTATÍSTICAS / SIMULAÇÃO ----------------
    def log_evento(self, mensagem):
        entrada = f"[{self.clock:>6}] " + mensagem
        self.log.append(entrada)
        print(entrada)

    def mostrar_log(self, quantidade=30):
        desenhar_titulo("LOG DO SISTEMA", 60)
        for entrada in self.log[-quantidade:]:
            print(entrada)
        desenhar_rodape(60)

    def executar_ciclo(self):
        self.escalonar()
        self.executar_processo()

    def executar_simulacao(self, ciclos=10):
        print("\nIniciando simulação...")
        for ciclo in range(ciclos):
            if self.num_processos == 0:
                print("Todos os processos foram finalizados.")
                break
            print("\n--- CICLO", ciclo + 1, "---")
            self.executar_ciclo()

    def estatisticas(self):
        desenhar_titulo("ESTATÍSTICAS DO SISTEMA", 60)
        print(f"Tempo de simulação     : {self.clock}")
        print(f"Processos criados      : {self.total_processos_criados}")
        print(f"Processos finalizados  : {self.total_processos_finalizados}")
        print(f"Processos ativos       : {self.num_processos}")
        print(f"Memória utilizada      : {self.memoria_utilizada} / {self.memoria_total} KB")
        print(f"Arquivos               : {len(self.arquivos)}")
        desenhar_rodape(60)

    def carregar_processos_exemplo(self):
        exemplos = [
            ("Browser", 3, 8, 128),
            ("Editor", 2, 5, 64),
            ("Compilador", 5, 12, 256),
            ("Player", 4, 4, 64),
            ("Terminal", 1, 3, 32),
        ]
        for nome, prioridade, tempo, memoria in exemplos:
            self.criar_processo(nome, prioridade, tempo, memoria)

    # ---------------- ALIASES (compatibilidade com os comandos do MS-PyDOS) ----------------
    def criar_arquivo_so(self, nome, pid_dono, dados=""):
        if not self.criar_arquivo(nome, pid_dono):
            return False
        if dados:
            self.abrir_arquivo(nome)
            self.escrever_arquivo(nome, dados)
            self.fechar_arquivo(nome)
        return True

    def abrir_arquivo_so(self, nome):
        return self.abrir_arquivo(nome)

    def fechar_arquivo_so(self, nome):
        return self.fechar_arquivo(nome)

    def escrever_arquivo_so(self, nome, dados):
        return self.escrever_arquivo(nome, dados)

    def ler_arquivo_so(self, nome):
        return self.ler_arquivo(nome)

    def deletar_arquivo_so(self, nome):
        return self.deletar_arquivo(nome)

    def listar_arquivos_so(self):
        return self.listar_arquivos()


# ============================================================
# ABREVIAÇÕES DE COMANDOS (estilo MS-DOS oficial: DIR, DEL, REN, COPY, MD, RD, TYPE, etc.)
# Todo comando abaixo pode ser digitado tanto por extenso quanto pela abreviação.
# ============================================================
ABREVIACOES_COMANDOS = {
    # --- Arquivos e pastas (nomes clássicos do MS-DOS real) ---
    "dir": "listar",
    "type": "tipo",
    "del": "apagar",
    "erase": "apagar",
    "ren": "renomear",
    "rename": "renomear",
    "copy": "copiar",
    "md": "criarpasta",
    "mkdir": "criarpasta",
    "rd": "removerpasta",
    "rmdir": "removerpasta",
    "move": "mover",
    "xcopy": "copiarpasta",
    "find": "localizar",
    "sort": "ordenar",
    "comp": "comparar",
    "chdir": "cd",
    "tree": "arvore",
    "label": "rotulo",
    "echo": "imprimir",
    "edit": "editar",
    "run": "executar",
    "exec": "executar",
    "cd..": "cd",
    # --- Sistema ---
    "exit": "sair",
    "quit": "sair",
    "help": "ajuda",
    "?": "ajuda",
    "cfg": "configuracoes",
    "mem": "mostrarram",
    "wipe": "limparram",
    "load": "carregarram",
    "reboot": "reiniciar",
    "fmt": "formatar",
    "sysinfo": "sistemainfo",
    "apps": "listaraplicativos",
    "google": "pesquisar",
    "search": "pesquisar",
    # --- Usuários ---
    "adduser": "cadastrar",
    "users": "usuarios",
    "passwd": "trocarsenha",
    "whoami": "usuarioatual",
    # --- Simulador de Processos/SO (abreviações próprias, sem equivalente real no MS-DOS) ---
    "mkproc": "criarprocesso",
    "ps": "listarprocessos",
    "kill": "terminarprocesso",
    "cycle": "executarciclo",
    "memso": "exibirmemoria",
    "memtest": "testarmemoria",
    "touch": "criararquivoso",
    "open": "abrirarquivo",
    "close": "fechararquivo",
    "write": "escreverarquivo",
    "cat": "lerarquivo",
    "rm": "apagararquivo",
    "ls": "listararquivos",
    "req": "solicitarrecurso",
    "rel": "liberarrecurso",
    "lsres": "listarrecursos",
    "semp": "semaforop",
    "semv": "semaforov",
    "lssem": "listarsemaforos",
    "stats": "estatisticas",
    "log": "mostrarlog",
    "demo": "carregarexemplos",
    "sim": "executarsimulacao",
}

def resolver_abreviacao(cmd):
    """Traduz uma abreviação estilo MS-DOS para o nome de comando completo interno."""
    return ABREVIACOES_COMANDOS.get(cmd, cmd)

# Mapa inverso: comando completo -> lista de abreviações (usado na tela de AJUDA)
ABREV_POR_COMANDO = {}
for _abrev, _completo in ABREVIACOES_COMANDOS.items():
    ABREV_POR_COMANDO.setdefault(_completo, []).append(_abrev)

# ============================================================
# CATEGORIAS DA AJUDA (AJUDA / AJUDA <categoria>)
# ============================================================
CATEGORIAS_AJUDA = {
    "arquivos": [
        ("listar", "Listar arquivos e pastas na pasta atual"),
        ("arvore", "Mostrar estrutura de pastas recursivamente"),
        ("tipo", "Exibir conteúdo de um arquivo (TIPO nomearquivo)"),
        ("escrever", "Criar ou sobrescrever um arquivo (ESCREVER nomearquivo conteudo)"),
        ("apagar", "Excluir um arquivo (APAGAR nomearquivo)"),
        ("renomear", "Renomear um arquivo (RENOMEAR nome_antigo nome_novo)"),
        ("copiar", "Copiar um arquivo (COPIAR arquivo_origem arquivo_destino)"),
        ("criarpasta", "Criar uma nova pasta (CRIARPASTA nomepasta)"),
        ("removerpasta", "Remover uma pasta vazia (REMOVERPASTA nomepasta)"),
        ("cd", "Mudar de diretório (CD nomepasta, CD ..)"),
        ("mover", "Mover um arquivo para outra pasta (MOVER origem pasta_destino)"),
        ("copiarpasta", "Copiar uma pasta e seu conteúdo recursivamente (COPIARPASTA origem destino)"),
        ("localizar", "Buscar um texto dentro de um arquivo (LOCALIZAR texto nomearquivo)"),
        ("ordenar", "Exibir as linhas de um arquivo em ordem alfabética (ORDENAR nomearquivo)"),
        ("comparar", "Comparar o conteúdo de dois arquivos (COMPARAR arquivo1 arquivo2)"),
    ],
    "sistema": [
        ("ajuda", "Mostrar esta ajuda (AJUDA ou AJUDA categoria)"),
        ("cls", "Limpar a tela"),
        ("ver", "Exibir a versão do MS-PyDOS"),
        ("data", "Exibir a data atual"),
        ("hora", "Exibir a hora atual"),
        ("vol", "Exibir o rótulo e o espaço do volume do disco"),
        ("rotulo", "Alterar o rótulo do volume (ROTULO novorotulo)"),
        ("sistemainfo", "Exibir informações do sistema"),
        ("reiniciar", "Salvar RAM e reiniciar MS-PyDOS"),
        ("formatar", "Formatar o disco"),
        ("limparcpu", "Resetar ciclos da CPU para 0"),
        ("pausa", "Pausar até o usuário pressionar ENTER"),
        ("ams", "Executar varredura do Serviço Anti-Malware"),
        ("sair", "Sair do MS-PyDOS"),
    ],
    "memoria": [
        ("carregarram", "Carregar chave-valor na RAM (CARREGARRAM chave valor)"),
        ("limparram", "Limpar todo o conteúdo da RAM"),
        ("mostrarram", "Exibir conteúdo atual da RAM"),
    ],
    "aplicativos": [
        ("imprimir", "Imprimir texto na tela (IMPRIMIR texto)"),
        ("editar", "Abrir o editor de texto"),
        ("executar", "Executar um arquivo de aplicação (EXECUTAR nomearquivo)"),
        ("abrir", "Abrir um app real do sistema (ABRIR calculadora/navegador/bloconotas/explorador/terminal/bluetooth/wifi)"),
        ("listaraplicativos", "Listar os aplicativos REALMENTE instalados no sistema operacional"),
        ("configuracoes", "Abrir o Painel de Configurações (Wi-Fi, Bluetooth, Rede, Pesquisar na Internet, Sistema)"),
    ],
    "pesquisar": [
        ("pesquisar", "Pesquisar no Google (PESQUISAR termo de busca)"),
        ("youtube", "Pesquisar no YouTube (YOUTUBE termo de busca)"),
        ("piratebay", "Buscar no Pirate Bay (PIRATEBAY termo)"),
        ("massgrave", "Abrir ativador MAS via PowerShell (MAS)"),
    ],
    "usuarios": [
        ("cadastrar", "Cadastrar um novo usuário"),
        ("usuarios", "Listar os usuários cadastrados"),
        ("login", "Trocar de usuário sem reiniciar o MS-PyDOS"),
        ("trocarsenha", "Alterar a senha do usuário atual (TROCARSENHA)"),
        ("usuarioatual", "Mostrar qual usuário está com a sessão aberta"),
    ],
    "processos": [
        ("criarprocesso", "Criar um processo (CRIARPROCESSO nome prioridade tempo memoria)"),
        ("listarprocessos", "Listar todos os processos ativos"),
        ("terminarprocesso", "Finalizar um processo (TERMINARPROCESSO pid)"),
        ("executarciclo", "Executar um ciclo do escalonador Round Robin"),
        ("exibirmemoria", "Exibir o estado das partições de memória"),
        ("testarmemoria", "Testar alocação de memória (TESTARMEMORIA pid tamanho)"),
        ("carregarexemplos", "Criar processos de exemplo automaticamente"),
        ("executarsimulacao", "Executar a simulação automática (EXECUTARSIMULACAO [ciclos])"),
        ("estatisticas", "Exibir estatísticas gerais do simulador"),
        ("mostrarlog", "Exibir o log de eventos do simulador"),
    ],
    "arquivosso": [
        ("criararquivoso", "Criar arquivo no simulador (CRIARARQUIVOSO nome pid_dono [dados])"),
        ("abrirarquivo", "Abrir um arquivo do simulador (ABRIRARQUIVO nome)"),
        ("fechararquivo", "Fechar um arquivo do simulador (FECHARARQUIVO nome)"),
        ("escreverarquivo", "Escrever dados em um arquivo (ESCREVERARQUIVO nome dados)"),
        ("lerarquivo", "Ler o conteúdo de um arquivo (LERARQUIVO nome)"),
        ("apagararquivo", "Apagar um arquivo do simulador (APAGARARQUIVO nome)"),
        ("listararquivos", "Listar arquivos cadastrados no simulador"),
    ],
    "recursos": [
        ("solicitarrecurso", "Solicitar recurso (SOLICITARRECURSO pid IMPRESSORA/DISCO/FITA)"),
        ("liberarrecurso", "Liberar recurso (LIBERARRECURSO pid IMPRESSORA/DISCO/FITA)"),
        ("listarrecursos", "Listar estado dos recursos e semáforos"),
        ("semaforop", "Executar operação P em um semáforo (SEMAFOROP nome)"),
        ("semaforov", "Executar operação V em um semáforo (SEMAFOROV nome)"),
        ("listarsemaforos", "Listar o estado dos semáforos"),
    ],
}


# --- HISTÓRICO DE COMANDOS ---
historico_comandos = {}
disco_obj = None
simulador_ms = None
gerenciador_usuarios = None
usuario_atual = None

def registrar_comando(cmd, ram):
    cmd_lower = cmd.lower()
    if cmd_lower not in historico_comandos:
        historico_comandos[cmd_lower] = 0
    historico_comandos[cmd_lower] += 1
    if historico_comandos[cmd_lower] > 300:
        print(f"[ALERTA AMS] Comando '{cmd_lower}' executado {historico_comandos[cmd_lower]} vezes!")
        while True:
            escolha = input("Deseja limpar a memória RAM ou reiniciar o sistema? (Para sair digite 's') (c/r/s): ").strip().lower()
            if escolha == "c":
                print("[AMS] Limpando memória RAM...")
                if not disco_obj.e_pasta("/ams"):
                    disco_obj.criar_pasta("/ams")
                disco_obj.escrever_arquivo("/ams/amslog", "historico_comandos[cmd_lower] > 300:!!!entradausuario:t;saida:break,limparram!")
                ram.limpar()
                break
            elif escolha == "r":
                print("[AMS] Reiniciando o sistema...")
                if not disco_obj.e_pasta("/ams"):
                    disco_obj.criar_pasta("/ams")
                disco_obj.escrever_arquivo("/ams/amslog", "historico_comandos[cmd_lower] > 300:!!!entradausuario:r;saida:break,inicializar,limparram!")
                ram.limpar()
                inicializar()
                break
            elif escolha == "s":
                print("[AMS] Saindo...")
                if not disco_obj.e_pasta("/ams"):
                    disco_obj.criar_pasta("/ams")
                disco_obj.escrever_arquivo("/ams/amslog", "historico_comandos[cmd_lower] > 300:!!!entradausuario:s;saida:break!")
                break
            else:
                print("Por favor digite c/r/s ")

# --- SERVIÇO ANTI-MALWARE DELUXE ---
def escanear_ams(ram, disco=None, silencioso=False, excluir=False):
    if not silencioso:
        desenhar_titulo("Serviço Anti-Malware Deluxe", 60)
    suspeita_encontrada = False

    for chave in list(ram.memoria.keys()):
        if "formatar" in ram.memoria[chave].lower():
            suspeita_encontrada = True
            if not silencioso:
                print(f"[ALERTA] Comando suspeito 'formatar' na RAM chave: {chave}")
            if excluir:
                ram.memoria.pop(chave)
                if not silencioso:
                    print(f"[REMOVIDO] Entrada RAM {chave} excluída")
                if silencioso:
                    print(f"[REMOVIDO] Entrada RAM {chave} excluída")

    if disco is not None:
        def escanear_pasta(caminho):
            nonlocal suspeita_encontrada
            itens = disco.listar_diretorio(caminho)
            for item in itens:
                caminho_item = caminho.rstrip("/") + "/" + item if caminho != "/" else "/" + item
                if disco.e_pasta(caminho_item):
                    escanear_pasta(caminho_item)
                else:
                    conteudo = disco.ler_arquivo(caminho_item)
                    if conteudo != "[Arquivo não encontrado]" and "formatar," in conteudo.lower():
                        suspeita_encontrada = True
                        if not silencioso:
                            print(f"[ALERTA] Comando suspeito 'formatar' encontrado em {caminho_item}")
                        if silencioso:
                            print(f"[ALERTA] Comando suspeito 'formatar' encontrado em {caminho_item}")
                        if excluir:
                            disco.apagar_arquivo(caminho_item)
                            ram.memoria.pop(caminho_item, None)
                            if not silencioso:
                                print(f"[REMOVIDO] {caminho_item} excluído")
                            if silencioso:
                                print(f"[REMOVIDO] {caminho_item} excluído")
        escanear_pasta("/")
    if not suspeita_encontrada and not silencioso:
        print("Nenhuma atividade suspeita encontrada.")
    if not silencioso:
        desenhar_rodape(60)

# --- MINI EDITOR ---
def iniciar_editor(disco, ram, diretorio_atual="/"):
    arquivo_atual = None
    buffer = []
    desenhar_titulo("Mini Editor", 60)
    print("  Digite texto ou comandos começando com ':'")
    print("  Comandos: :abrir, :novo, :del, :mostrar, :salvar, :sair")
    desenhar_rodape(60)
    while True:
        linha = input().rstrip()
        if linha.startswith(":"):
            cmd = linha[1:].strip()
            if cmd.startswith("abrir "):
                nome_arquivo = cmd[6:].strip()
                caminho_abs = nome_arquivo if nome_arquivo.startswith("/") else f"{diretorio_atual}/{nome_arquivo}"
                conteudo = disco.ler_arquivo(caminho_abs)
                if conteudo in ("[Arquivo não encontrado]", "[É uma pasta]"):
                    print(f"Arquivo não encontrado: {nome_arquivo}")
                    buffer = []
                    arquivo_atual = None
                else:
                    buffer = conteudo.splitlines()
                    arquivo_atual = caminho_abs
                    print(f"Aberto {nome_arquivo}")
            elif cmd.startswith("novo "):
                nome_arquivo = cmd[5:].strip()
                arquivo_atual = nome_arquivo if nome_arquivo.startswith("/") else f"{diretorio_atual}/{nome_arquivo}"
                buffer = []
                print(f"Novo arquivo criado: {arquivo_atual}")
            elif cmd.startswith("del "):
                try:
                    indice = int(cmd[4:]) - 1
                    removido = buffer.pop(indice)
                    print(f"Linha {indice+1} removida: {removido}")
                except:
                    print("Número de linha inválido.")
            elif cmd == "mostrar":
                for i, l in enumerate(buffer):
                    print(f"{i+1}: {l}")
            elif cmd == "salvar":
                if arquivo_atual:
                    conteudo = "\n".join(buffer)
                    ram.carregar(arquivo_atual, conteudo)
                    disco.escrever_arquivo(arquivo_atual, conteudo)
                    print(f"Salvo: {arquivo_atual}")
                else:
                    print("Nenhum arquivo para salvar.")
            elif cmd in ("sair", "squit"):
                break
            else:
                print("Comando desconhecido.")
        else:
            buffer.append(linha)

# --- FUNÇÕES AUXILIARES ---
def obter_caminho_absoluto(caminho, diretorio_atual):
    if caminho.startswith("/"):
        return caminho
    if diretorio_atual == "/":
        return "/" + caminho
    return diretorio_atual.rstrip("/") + "/" + caminho

def comando_arvore(caminho, disco):
    def imprimir_arvore(caminho_atual, prefixo=""):
        itens = disco.listar_diretorio(caminho_atual)
        total = len(itens)
        for i, item in enumerate(itens):
            caminho_item = caminho_atual.rstrip("/") + "/" + item if caminho_atual != "/" else "/" + item
            e_dir = disco.e_pasta(caminho_item)
            conector = "└── " if i == total - 1 else "├── "
            print(prefixo + conector + item)
            if e_dir:
                extensao = " " if i == total - 1 else "│ "
                imprimir_arvore(caminho_item, prefixo + extensao)
    print(caminho)
    imprimir_arvore(caminho)

# --- ABRIR APLICATIVOS REAIS DO SISTEMA ---
# Mapa de apelidos -> comando real por sistema operacional.
# Adicione novas entradas aqui para "ensinar" o MS-PyDOS a abrir mais programas.
APLICATIVOS = {
    "calculadora": {"nt": ["calc"], "darwin": ["open", "-a", "Calculator"], "linux": ["gnome-calculator"]},
    "bloconotas":  {"nt": ["notepad"], "darwin": ["open", "-a", "TextEdit"], "linux": ["gedit"]},
    "navegador":   {"nt": ["cmd", "/c", "start", "", "https://www.google.com"],
                     "darwin": ["open", "https://www.google.com"],
                     "linux": ["xdg-open", "https://www.google.com"]},
    "explorador":  {"nt": ["explorer"], "darwin": ["open", "."], "linux": ["xdg-open", "."]},
    "terminal":    {"nt": ["cmd"], "darwin": ["open", "-a", "Terminal"], "linux": ["x-terminal-emulator"]},
    "bluetooth":   {"nt": ["cmd", "/c", "start", "ms-settings:bluetooth"],
                     "darwin": ["open", "/System/Library/PreferencePanes/Bluetooth.prefPane"],
                     "linux": ["blueman-manager"]},
    "wifi":        {"nt": ["cmd", "/c", "start", "ms-settings:network-wifi"],
                     "darwin": ["open", "/System/Library/PreferencePanes/Network.prefPane"],
                     "linux": ["nm-connection-editor"]},
}

# --- PAINEL DE CONFIGURACOES (estilo Windows, visual DOS) ---
LARGURA_CONFIG = 62

def _linha_config(char="-"):
    if char == "=":
        desenhar_rodape(LARGURA_CONFIG)
    else:
        desenhar_divisoria(LARGURA_CONFIG)

def _titulo_config(texto):
    desenhar_titulo(texto, LARGURA_CONFIG)

def _pausar_config():
    pausar_tela("Pressione ENTER para voltar...")

def obter_info_ram_sistema():
    """Lê a RAM REAL da máquina (não a RAM simulada do MS-PyDOS), sem depender de libs externas."""
    sistema = platform.system()
    try:
        if sistema == "Windows":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            status = MEMORYSTATUSEX()
            status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            return {
                "total_mb": status.ullTotalPhys // (1024 * 1024),
                "livre_mb": status.ullAvailPhys // (1024 * 1024),
            }
        elif sistema == "Linux":
            dados = {}
            with open("/proc/meminfo") as f:
                for linha in f:
                    partes = linha.split(":")
                    if len(partes) == 2:
                        dados[partes[0].strip()] = int(partes[1].strip().split()[0])
            total_mb = dados.get("MemTotal", 0) // 1024
            livre_mb = dados.get("MemAvailable", dados.get("MemFree", 0)) // 1024
            return {"total_mb": total_mb, "livre_mb": livre_mb}
        elif sistema == "Darwin":
            total_bytes = int(subprocess.run(["sysctl", "-n", "hw.memsize"],
                                              capture_output=True, text=True, timeout=3).stdout.strip())
            return {"total_mb": total_bytes // (1024 * 1024), "livre_mb": None}
    except Exception:
        return None
    return None

def obter_info_disco_sistema():
    """Lê o armazenamento REAL do PC (não o disco simulado do MS-PyDOS)."""
    try:
        caminho = os.path.dirname(os.path.abspath(__file__)) or os.sep
        uso = shutil.disk_usage(caminho)
        return {
            "total_gb": uso.total / (1024 ** 3),
            "usado_gb": uso.used / (1024 ** 3),
            "livre_gb": uso.free / (1024 ** 3),
        }
    except Exception:
        return None

def obter_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Indisponível (sem conexão detectada)"

def menu_rede_internet():
    _titulo_config("REDE E INTERNET")
    print(f"Nome do host  : {socket.gethostname()}")
    print(f"Endereço IPv4 : {obter_ip_local()}")
    print(f"Sistema       : {platform.system()} {platform.release()}")
    sistema = platform.system()
    try:
        if sistema == "Windows":
            saida = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=6).stdout
        elif sistema == "Darwin":
            saida = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=6).stdout
        else:
            saida = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=6).stdout
        if saida.strip():
            print("\n--- Detalhes da interface (resumo) ---")
            print(saida.strip()[:1200])
    except Exception:
        print("\n[AVISO] Detalhes de interface indisponíveis neste ambiente.")
    _linha_config()
    _pausar_config()

def listar_redes_wifi():
    sistema = platform.system()
    redes = []
    try:
        if sistema == "Windows":
            saida = subprocess.run(["netsh", "wlan", "show", "networks"],
                                    capture_output=True, text=True, timeout=8).stdout
            for linha in saida.splitlines():
                if "SSID" in linha and ":" in linha and "BSSID" not in linha:
                    nome = linha.split(":", 1)[1].strip()
                    if nome:
                        redes.append(nome)
        elif sistema == "Linux":
            saida = subprocess.run(["nmcli", "-t", "-f", "SSID", "dev", "wifi"],
                                    capture_output=True, text=True, timeout=8).stdout
            redes = [l.strip() for l in saida.splitlines() if l.strip() and l.strip() != "--"]
        elif sistema == "Darwin":
            caminho_airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
            saida = subprocess.run([caminho_airport, "-s"], capture_output=True, text=True, timeout=8).stdout
            linhas = saida.splitlines()[1:]
            redes = [l.split()[0] for l in linhas if l.strip()]
    except FileNotFoundError:
        print("[AVISO] Ferramenta de rede do sistema não encontrada.")
    except Exception as e:
        print(f"[AVISO] Não foi possível escanear redes: {e}")
    # remove duplicadas mantendo ordem
    vistas = set()
    unicas = []
    for r in redes:
        if r not in vistas:
            vistas.add(r)
            unicas.append(r)
    return unicas

def conectar_wifi(ssid):
    sistema = platform.system()
    try:
        if sistema == "Windows":
            resultado = subprocess.run(["netsh", "wlan", "connect", f"name={ssid}"],
                                        capture_output=True, text=True, timeout=12)
            saida = (resultado.stdout or resultado.stderr).strip()
            print(saida if saida else "Comando enviado ao Windows.")
        elif sistema == "Linux":
            senha = input("Senha (ENTER se a rede for aberta): ").strip()
            comando = ["nmcli", "dev", "wifi", "connect", ssid]
            if senha:
                comando += ["password", senha]
            resultado = subprocess.run(comando, capture_output=True, text=True, timeout=20)
            saida = (resultado.stdout or resultado.stderr).strip()
            print(saida if saida else "Comando enviado ao NetworkManager.")
        else:
            print("Conexão automática não suportada neste SO.")
            print("Abrindo as configurações de Wi-Fi do sistema...")
            abrir_aplicativo("wifi")
    except FileNotFoundError:
        print("[ERRO] Ferramenta de rede não encontrada. Abrindo configurações do sistema...")
        abrir_aplicativo("wifi")
    except Exception as e:
        print(f"[ERRO] Falha ao conectar: {e}")

def menu_wifi():
    _titulo_config("WI-FI")
    print("Escaneando redes disponíveis...\n")
    redes = listar_redes_wifi()
    if redes:
        for i, r in enumerate(redes, 1):
            print(f" [{i}] {r}")
    else:
        print(" Nenhuma rede encontrada (ou escaneamento não suportado aqui).")
    print("\n [A] Abrir configurações de Wi-Fi do sistema")
    print(" [0] Voltar")
    _linha_config()
    escolha = input("\nSelecione uma rede ou opção: ").strip().lower()
    if escolha == "0":
        return
    elif escolha == "a":
        abrir_aplicativo("wifi")
    elif escolha.isdigit() and 1 <= int(escolha) <= len(redes):
        conectar_wifi(redes[int(escolha) - 1])
    elif escolha:
        print("Opção inválida.")
    _pausar_config()

def menu_bluetooth(disco, diretorio_atual):
    _titulo_config("BLUETOOTH")
    print(" [1] Ativar / abrir configurações de Bluetooth do sistema")
    print(" [2] Parear novo dispositivo (simulado)")
    print(" [3] Compartilhar arquivo via Bluetooth (simulado)")
    print(" [0] Voltar")
    _linha_config()
    escolha = input("\nSelecione uma opção: ").strip()
    if escolha == "1":
        abrir_aplicativo("bluetooth")
    elif escolha == "2":
        nome_dispositivo = input("Nome do dispositivo para procurar/parear: ").strip() or "Dispositivo Desconhecido"
        print(f"Procurando '{nome_dispositivo}'", end="", flush=True)
        for _ in range(3):
            time.sleep(0.35)
            print(".", end="", flush=True)
        print(f"\nDispositivo '{nome_dispositivo}' pareado com sucesso! (simulado)")
    elif escolha == "3":
        nome_arquivo = input("Nome do arquivo do disco MS-PyDOS para compartilhar: ").strip()
        if not nome_arquivo:
            print("Operação cancelada.")
        else:
            caminho = obter_caminho_absoluto(nome_arquivo, diretorio_atual)
            conteudo = disco.ler_arquivo(caminho)
            if conteudo in ("[Arquivo não encontrado]", "[É uma pasta]"):
                print(f"Não foi possível compartilhar: {conteudo}")
            else:
                tamanho = len(conteudo.encode("utf-8"))
                print(f"Enviando '{nome_arquivo}' ({tamanho} bytes) via Bluetooth...")
                largura_barra = 24
                for i in range(largura_barra + 1):
                    time.sleep(0.04)
                    preenchido = "#" * i
                    vazio = "-" * (largura_barra - i)
                    pct = int(i / largura_barra * 100)
                    print(f"\r[{preenchido}{vazio}] {pct:3d}%", end="", flush=True)
                print(f"\nArquivo '{nome_arquivo}' enviado com sucesso! (simulado)")
    elif escolha == "0":
        return
    else:
        print("Opção inválida.")
    _pausar_config()

def pesquisar_google(termo):
    """Abre uma pesquisa real no Google, no navegador padrão do sistema."""
    termo = termo.strip()
    if not termo:
        print("Uso: PESQUISAR termo de busca")
        return
    url = f"https://www.google.com/search?q={quote_plus(termo)}"
    try:
        webbrowser.open(url)
        print(f"Abrindo pesquisa por \"{termo}\" no Google...")
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir o navegador: {e}")

def pesquisar_youtube(termo):
    termo = termo.strip()
    if not termo:
        print("Uso: YOUTUBE termo de busca")
        return
    url = f"https://www.youtube.com/results?search_query={quote_plus(termo)}"
    try:
        webbrowser.open(url)
        print(f"Abrindo pesquisa por \"{termo}\" no YouTube...")
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir o navegador: {e}")

def executar_massgrave():
    """Abre o Microsoft Activation Scripts (MAS) via PowerShell (get.activated.win)."""
    print("AVISO: isso vai baixar e executar um script externo do site get.activated.win")
    print("no PowerShell do sistema (irm https://get.activated.win | iex).")
    confirm = input("Deseja continuar? (s/n): ").strip().lower()
    if confirm not in ("s", "sim", "y", "yes"):
        print("Operação cancelada.")
        return
    try:
        comando = 'irm https://get.activated.win | iex'
        print("Iniciando PowerShell com o script MAS...")
        subprocess.run(["powershell", "-NoProfile", "-Command", comando], check=False)
    except Exception as e:
        print(f"[ERRO] Não foi possível iniciar o PowerShell: {e}")

def buscar_piratebay_mcp(termo):
    try:
        from torrent_search import torrent_search_api
        resultados = torrent_search_api.search_torrents(termo)
        if not resultados:
            print("Nenhum resultado encontrado.")
            return
        print(f"\nResultados para '{termo}':\n")
        for i, r in enumerate(resultados[:20], 1):
            nome = r.get("name", "Sem nome")
            seeds = r.get("seeds", "?")
            peers = r.get("peers", "?")
            tamanho = r.get("size", "?")
            print(f"{i:2}. {nome} | Seeds: {seeds} | Peers: {peers} | Tamanho: {tamanho}")
    except Exception as e:
        print(f"[ERRO] torrent-search-mcp indisponível: {e}")
        print("Dica: pip install torrent-search-mcp && playwright install --with-deps chromium")
        print("Abrindo fallback no navegador...")
        webbrowser.open(f"https://thepiratebay.org/search?q={quote_plus(termo)}")

def abrir_site(nome_site):
    sites = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "facebook": "https://www.facebook.com",
        "instagram": "https://www.instagram.com",
        "twitter": "https://www.twitter.com",
        "x": "https://www.x.com",
        "reddit": "https://www.reddit.com",
        "github": "https://www.github.com",
        "wikipedia": "https://www.wikipedia.org",
        "amazon": "https://www.amazon.com",
        "netflix": "https://www.netflix.com",
        "twitch": "https://www.twitch.tv",
        "discord": "https://discord.com",
        "telegram": "https://web.telegram.org",
        "whatsapp": "https://web.whatsapp.com",
        "linkedin": "https://www.linkedin.com",
        "tiktok": "https://www.tiktok.com",
        "piratebay": "https://thepiratebay.org",
        "pirate": "https://thepiratebay.org",
        "tpb": "https://thepiratebay.org",
        "1337x": "https://1337x.to",
        "kickass": "https://kickasstorrents.to",
        "torrent": "https://thepiratebay.org",
    }
    nome_lower = nome_site.lower().strip()
    if nome_lower in sites:
        try:
            webbrowser.open(sites[nome_lower])
            print(f"Abrindo {nome_lower}...")
        except Exception as e:
            print(f"[ERRO] Não foi possível abrir o site: {e}")
    else:
        print(f"Site '{nome_site}' não encontrado na lista.")
        print("Sites disponíveis:", ", ".join(sorted(set(sites.keys()))))

def menu_pesquisa_internet():
    _titulo_config("PESQUISAR NA INTERNET")
    termo = input("Digite o que deseja pesquisar: ").strip()
    if not termo:
        print("Pesquisa cancelada.")
    else:
        pesquisar_google(termo)
    _pausar_config()

def menu_sistema_config(cpu, ram, disco):
    _titulo_config("SISTEMA")
    info_cpu = cpu.obter_info()
    info_ram = ram.obter_info()
    info_disco = disco.obter_info()
    print(f"Sistema operacional real : {platform.system()} {platform.release()}")
    print(f"Arquitetura              : {platform.machine()}")
    print(f"MS-PyDOS - Ciclos CPU    : {info_cpu['ciclos']}")
    print(f"MS-PyDOS - RAM           : {info_ram['usado_kb']} / {info_ram['total_kb']} KB usados")
    print(f"MS-PyDOS - Disco         : {info_disco['usado_kb']} / {info_disco['max_kb']} KB usados "
          f"({info_disco['total_arquivos']} arquivos)")
    _linha_config()
    _pausar_config()

def menu_configuracoes(cpu, ram, disco, diretorio_atual):
    while True:
        _titulo_config("PAINEL DE CONFIGURAÇÕES - MS-PyDOS")
        print(" [1] Rede e Internet")
        print(" [2] Wi-Fi")
        print(" [3] Bluetooth")
        print(" [4] Pesquisar na Internet")
        print(" [5] Sistema")
        print(" [0] Voltar ao terminal")
        _linha_config()
        escolha = input("\nSelecione uma opção: ").strip()
        if escolha == "1":
            menu_rede_internet()
        elif escolha == "2":
            menu_wifi()
        elif escolha == "3":
            menu_bluetooth(disco, diretorio_atual)
        elif escolha == "4":
            menu_pesquisa_internet()
        elif escolha == "5":
            menu_sistema_config(cpu, ram, disco)
        elif escolha == "0":
            print("Voltando ao terminal...")
            break
        else:
            print("Opção inválida.\n")

def obter_aplicativos_instalados_sistema(limite=300):
    """Detecta os aplicativos REALMENTE instalados no sistema operacional atual
    (não a lista fixa de atalhos do comando ABRIR). Cada SO tem seu próprio jeito
    de listar programas instalados; se não for possível detectar neste ambiente,
    retorna uma lista vazia."""
    sistema = platform.system()
    apps = []
    try:
        if sistema == "Windows":
            import winreg
            caminhos_registro = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            ]
            vistos = set()
            for hive, caminho in caminhos_registro:
                try:
                    chave = winreg.OpenKey(hive, caminho)
                except (FileNotFoundError, OSError):
                    continue
                for i in range(winreg.QueryInfoKey(chave)[0]):
                    try:
                        subchave = winreg.OpenKey(chave, winreg.EnumKey(chave, i))
                        nome, _ = winreg.QueryValueEx(subchave, "DisplayName")
                        if nome and nome not in vistos:
                            vistos.add(nome)
                            apps.append(nome)
                    except (FileNotFoundError, OSError):
                        continue

        elif sistema == "Darwin":
            for pasta_apps in ("/Applications", os.path.expanduser("~/Applications")):
                if os.path.isdir(pasta_apps):
                    for item in os.listdir(pasta_apps):
                        if item.endswith(".app"):
                            apps.append(item[:-4])

        elif sistema == "Linux":
            pastas = [
                "/usr/share/applications",
                "/usr/local/share/applications",
                os.path.expanduser("~/.local/share/applications"),
            ]
            vistos = set()
            for pasta in pastas:
                if not os.path.isdir(pasta):
                    continue
                for arquivo in os.listdir(pasta):
                    if not arquivo.endswith(".desktop"):
                        continue
                    try:
                        with open(os.path.join(pasta, arquivo), "r", encoding="utf-8", errors="ignore") as f:
                            for linha in f:
                                if linha.startswith("Name="):
                                    nome = linha.strip().split("=", 1)[1]
                                    if nome and nome not in vistos:
                                        vistos.add(nome)
                                        apps.append(nome)
                                    break
                    except OSError:
                        continue
    except Exception:
        pass

    apps = sorted(set(apps), key=str.lower)
    if limite:
        apps = apps[:limite]
    return apps

def listar_aplicativos():
    """Exibe os aplicativos REALMENTE instalados no sistema operacional atual e,
    em seguida, quais atalhos o comando ABRIR sabe abrir diretamente."""
    sistema = platform.system().lower()
    mapa_sistema = {"windows": "nt", "darwin": "darwin", "linux": "linux"}
    chave_sistema = mapa_sistema.get(sistema)

    desenhar_titulo("Aplicativos instalados no sistema", 68)
    apps_reais = obter_aplicativos_instalados_sistema()
    if apps_reais:
        print(f"  {len(apps_reais)} aplicativo(s) detectado(s) neste computador:\n")
        for nome in apps_reais:
            print(f"  - {nome}")
    else:
        print("  Não foi possível detectar os aplicativos instalados neste ambiente")
        print("  (sistema não suportado ou sem permissão de leitura).")
    print()
    desenhar_divisoria(68)
    print("  Atalhos rápidos suportados pelo comando ABRIR neste sistema:")
    for nome in sorted(APLICATIVOS.keys()):
        suportado = APLICATIVOS[nome].get(chave_sistema)
        status = "disponível" if suportado else "não suportado neste sistema"
        print(f"    {nome:<14} - {status}")
    desenhar_rodape(68)
    print(f"Use ABRIR <nomeapp> para abrir um dos atalhos. Ex.: ABRIR {sorted(APLICATIVOS.keys())[0]}\n")

def abrir_aplicativo(nome):
    chave = nome.lower()
    if chave not in APLICATIVOS:
        disponiveis = ", ".join(sorted(APLICATIVOS.keys()))
        print(f"Aplicativo desconhecido: {nome}")
        print(f"Disponíveis: {disponiveis}")
        return
    sistema = platform.system().lower()
    mapa_sistema = {"windows": "nt", "darwin": "darwin", "linux": "linux"}
    chave_sistema = mapa_sistema.get(sistema)
    comando = APLICATIVOS[chave].get(chave_sistema)
    if not comando:
        print(f"'{nome}' não é suportado no seu sistema ({sistema}).")
        return
    try:
        subprocess.Popen(comando)
        print(f"Abrindo {nome}...")
    except FileNotFoundError:
        print(f"[ERRO] '{nome}' não está instalado ou não foi encontrado no PATH.")
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir '{nome}': {e}")

# --- EXECUTAR COMANDOS ---
def executar_comando(tokens, cpu, ram, disco, diretorio_atual):
    global usuario_atual
    if not tokens:
        return diretorio_atual
    cmd = resolver_abreviacao(tokens[0].lower())
    escanear_ams(ram, disco=disco, silencioso=True, excluir=True)
    registrar_comando(cmd, ram)

    if cmd == "sair":
        print("Saindo do MS-PyDOS...")
        dos_desligar_tela_azul()
        sys.exit()
    elif cmd == "ajuda":
        filtro = tokens[1].lower() if len(tokens) > 1 else None
        if filtro and filtro not in CATEGORIAS_AJUDA:
            print(f"Categoria '{filtro}' não existe. Digite AJUDA para ver todas as categorias.")
        else:
            categorias = {filtro: CATEGORIAS_AJUDA[filtro]} if filtro else CATEGORIAS_AJUDA
            desenhar_titulo("AJUDA DO MS-PyDOS", 76)
            if not filtro:
                print("Dica: digite AJUDA <categoria> para ver só uma categoria. Categorias:")
                print("  " + ", ".join(CATEGORIAS_AJUDA.keys()))
            for nome_categoria, comandos in categorias.items():
                desenhar_divisoria(76)
                print(f" >> {nome_categoria.upper()}")
                desenhar_divisoria(76)
                for comando_completo, descricao in comandos:
                    abrevs = ABREV_POR_COMANDO.get(comando_completo, [])
                    sufixo_abrev = f"  (abrev.: {', '.join(a.upper() for a in abrevs)})" if abrevs else ""
                    print(f"  {comando_completo.upper():<16}: {descricao}{sufixo_abrev}")
            desenhar_rodape(76)
    elif cmd == "cadastrar":
        novo = tela_cadastro_usuario(gerenciador_usuarios)
        if novo:
            print(f"Usuário '{novo}' criado. Use LOGIN {novo} para entrar com essa conta.")
    elif cmd == "usuarios":
        usuarios = gerenciador_usuarios.listar()
        desenhar_titulo("USUARIOS CADASTRADOS", 50)
        if not usuarios:
            print("Nenhum usuário cadastrado.")
        else:
            for nome_u, info_u in usuarios.items():
                marcador = " (sessão atual)" if nome_u == usuario_atual else ""
                print(f"  {nome_u}{marcador}  -  criado em {info_u.get('criado_em', '?')}")
        desenhar_rodape(50)
    elif cmd == "login":
        novo_usuario = tela_login(gerenciador_usuarios)
        if novo_usuario:
            usuario_atual = novo_usuario
    elif cmd == "trocarsenha":
        senha_atual = _ler_senha_oculta("Senha atual: ")
        senha_nova = _ler_senha_oculta("Nova senha: ")
        confirmar_nova = _ler_senha_oculta("Confirme a nova senha: ")
        if senha_nova != confirmar_nova:
            print("[ERRO] As senhas não coincidem.")
        else:
            ok, msg = gerenciador_usuarios.trocar_senha(usuario_atual, senha_atual, senha_nova)
            print(("[OK] " if ok else "[ERRO] ") + msg)
    elif cmd == "usuarioatual":
        print(f"Usuário com sessão aberta: {usuario_atual}")
    elif cmd == "imprimir":
        print(" ".join(tokens[1:]))
    elif cmd == "abrir":
        if len(tokens) < 2:
            print("Uso: ABRIR nomeapp  (ex: ABRIR calculadora, ABRIR navegador, ABRIR bluetooth)")
        else:
            abrir_aplicativo(tokens[1])
    elif cmd == "listaraplicativos":
        listar_aplicativos()
    elif cmd == "pesquisar":
        if len(tokens) < 2:
            print("Uso: PESQUISAR termo de busca  (ex: PESQUISAR receita de bolo)")
        else:
            pesquisar_google(" ".join(tokens[1:]))
    elif cmd == "youtube":
        if len(tokens) < 2:
            print("Uso: YOUTUBE termo de busca  (ex: YOUTUBE musica top)")
        else:
            pesquisar_youtube(" ".join(tokens[1:]))
    elif cmd == "piratebay":
        if len(tokens) < 2:
            print("Uso: PIRATEBAY termo")
        else:
            buscar_piratebay_mcp(" ".join(tokens[1:]))
    elif cmd in ("massgrave", "mas"):
        executar_massgrave()
    elif cmd in ("configuracoes", "painel"):
        menu_configuracoes(cpu, ram, disco, diretorio_atual)
    elif cmd == "editar":
        iniciar_editor(disco, ram, diretorio_atual)
    elif cmd == "cls":
        os.system("cls" if os.name == "nt" else "clear")
    elif cmd == "ver":
        print("MS-PyDOS v1.0 - Máquina de Shopping")
    elif cmd == "data":
        print("Data atual: " + datetime.now().strftime("%d/%m/%Y"))
    elif cmd == "hora":
        print("Hora atual: " + datetime.now().strftime("%H:%M:%S"))
    elif cmd == "vol":
        desenhar_titulo("VOLUME DO DISCO", 50)
        print(f"Rótulo : {disco.rotulo}")
        info = disco.obter_info()
        print(f"Usado  : {info['usado_kb']} KB")
        print(f"Livre  : {info['livre_kb']} KB")
        print(f"Arquivos: {info['total_arquivos']}")
        info_disco_real = obter_info_disco_sistema()
        if info_disco_real:
            desenhar_divisoria(50)
            print(f"Armazenamento real do PC: {info_disco_real['total_gb']:.1f} GB total | "
                  f"{info_disco_real['livre_gb']:.1f} GB livres")
        desenhar_rodape(50)
    elif cmd == "rotulo":
        if len(tokens) < 2:
            print("Uso: ROTULO novorotulo")
        else:
            disco.rotulo = " ".join(tokens[1:]).upper()
            print(f"Rótulo do volume alterado para: {disco.rotulo}")
    elif cmd == "pausa":
        input("Pressione ENTER para continuar...")
    elif cmd == "removerpasta":
        if len(tokens) < 2:
            print("Uso: REMOVERPASTA nomepasta")
        else:
            caminho_pasta = obter_caminho_absoluto(tokens[1], diretorio_atual)
            if not disco.e_pasta(caminho_pasta):
                print(f"Pasta não encontrada: {tokens[1]}")
            elif disco.listar_diretorio(caminho_pasta):
                print("A pasta não está vazia. Apague o conteúdo antes de remover.")
            else:
                disco.apagar_arquivo(caminho_pasta)
                print(f"Pasta removida: {tokens[1]}")
    elif cmd == "mover":
        if len(tokens) < 3:
            print("Uso: MOVER origem pasta_destino")
        else:
            origem = obter_caminho_absoluto(tokens[1], diretorio_atual)
            destino_bruto = obter_caminho_absoluto(tokens[2], diretorio_atual)
            if disco.e_pasta(destino_bruto):
                nome_arquivo_origem = origem.rstrip("/").split("/")[-1]
                destino = destino_bruto.rstrip("/") + "/" + nome_arquivo_origem
            else:
                destino = destino_bruto
            conteudo = ram.obter(origem)
            if conteudo is None:
                conteudo = disco.ler_arquivo(origem)
                if conteudo == "[Arquivo não encontrado]":
                    print(f"Arquivo de origem '{origem}' não encontrado.")
                    return diretorio_atual
            ram.memoria.pop(origem, None)
            ram.carregar(destino, conteudo)
            disco.escrever_arquivo(destino, conteudo)
            disco.apagar_arquivo(origem)
            print(f"Movido '{origem}' para '{destino}'")
    elif cmd == "copiarpasta":
        if len(tokens) < 3:
            print("Uso: COPIARPASTA pasta_origem pasta_destino")
        else:
            origem = obter_caminho_absoluto(tokens[1], diretorio_atual)
            destino = obter_caminho_absoluto(tokens[2], diretorio_atual)
            if not disco.e_pasta(origem):
                print(f"Pasta de origem não encontrada: {tokens[1]}")
            else:
                def copiar_pasta_recursivo(caminho_atual, caminho_novo):
                    disco.criar_pasta(caminho_novo)
                    for item in disco.listar_diretorio(caminho_atual):
                        item_origem = caminho_atual.rstrip("/") + "/" + item if caminho_atual != "/" else "/" + item
                        item_destino = caminho_novo.rstrip("/") + "/" + item if caminho_novo != "/" else "/" + item
                        if disco.e_pasta(item_origem):
                            copiar_pasta_recursivo(item_origem, item_destino)
                        else:
                            conteudo = disco.ler_arquivo(item_origem)
                            disco.escrever_arquivo(item_destino, conteudo)
                copiar_pasta_recursivo(origem, destino)
                print(f"Pasta '{origem}' copiada para '{destino}'")
    elif cmd == "localizar":
        if len(tokens) < 3:
            print("Uso: LOCALIZAR texto nomearquivo")
        else:
            texto_busca = tokens[1]
            nome_arquivo = obter_caminho_absoluto(tokens[2], diretorio_atual)
            conteudo = disco.ler_arquivo(nome_arquivo)
            if conteudo in ("[Arquivo não encontrado]", "[É uma pasta]"):
                print(conteudo)
            else:
                encontrou = False
                for i, linha in enumerate(conteudo.splitlines(), 1):
                    if texto_busca.lower() in linha.lower():
                        encontrou = True
                        print(f"{i}: {linha}")
                if not encontrou:
                    print("Nenhuma ocorrência encontrada.")
    elif cmd == "ordenar":
        if len(tokens) < 2:
            print("Uso: ORDENAR nomearquivo")
        else:
            nome_arquivo = obter_caminho_absoluto(tokens[1], diretorio_atual)
            conteudo = disco.ler_arquivo(nome_arquivo)
            if conteudo in ("[Arquivo não encontrado]", "[É uma pasta]"):
                print(conteudo)
            else:
                for linha in sorted(conteudo.splitlines()):
                    print(linha)
    elif cmd == "comparar":
        if len(tokens) < 3:
            print("Uso: COMPARAR arquivo1 arquivo2")
        else:
            caminho1 = obter_caminho_absoluto(tokens[1], diretorio_atual)
            caminho2 = obter_caminho_absoluto(tokens[2], diretorio_atual)
            conteudo1 = disco.ler_arquivo(caminho1)
            conteudo2 = disco.ler_arquivo(caminho2)
            if conteudo1 in ("[Arquivo não encontrado]", "[É uma pasta]"):
                print(f"{tokens[1]}: {conteudo1}")
            elif conteudo2 in ("[Arquivo não encontrado]", "[É uma pasta]"):
                print(f"{tokens[2]}: {conteudo2}")
            elif conteudo1 == conteudo2:
                print("Os arquivos são idênticos.")
            else:
                linhas1 = conteudo1.splitlines()
                linhas2 = conteudo2.splitlines()
                maximo = max(len(linhas1), len(linhas2))
                diferencas = 0
                for i in range(maximo):
                    l1 = linhas1[i] if i < len(linhas1) else "<sem linha>"
                    l2 = linhas2[i] if i < len(linhas2) else "<sem linha>"
                    if l1 != l2:
                        diferencas += 1
                        print(f"Linha {i+1}:")
                        print(f"  {tokens[1]}: {l1}")
                        print(f"  {tokens[2]}: {l2}")
                if diferencas == 0:
                    print("Os arquivos são idênticos.")
    elif cmd == "escrever":
        if len(tokens) < 3:
            print("Uso: ESCREVER nomearquivo conteudo")
        else:
            nome_arquivo = obter_caminho_absoluto(tokens[1], diretorio_atual)
            conteudo = " ".join(tokens[2:])
            ram.carregar(nome_arquivo, conteudo)
            disco.escrever_arquivo(nome_arquivo, conteudo)
            disco.escrever_em_massa(ram.memoria)
            print(f"Escrito na RAM e no Disco: {nome_arquivo}")
    elif cmd == "tipo":
        if len(tokens) < 2:
            print("Uso: TIPO nomearquivo")
        else:
            nome_arquivo = obter_caminho_absoluto(tokens[1], diretorio_atual)
            print(disco.ler_arquivo(nome_arquivo))
    elif cmd == "listar":
        disco.escrever_em_massa(ram.memoria)
        itens = disco.listar_diretorio(diretorio_atual)
        if itens:
            for item in itens:
                caminho_item = diretorio_atual.rstrip("/") + "/" + item if diretorio_atual != "/" else "/" + item
                print(f"<DIR> {item}" if disco.e_pasta(caminho_item) else f" {item}")
        else:
            print("Nenhum arquivo ou diretório.")
    elif cmd == "arvore":
        comando_arvore(diretorio_atual, disco)
    elif cmd == "criarpasta":
        if len(tokens) < 2:
            print("Uso: CRIARPASTA nomepasta")
        else:
            caminho_pasta = obter_caminho_absoluto(tokens[1], diretorio_atual)
            disco.criar_pasta(caminho_pasta)
            disco.escrever_em_massa(ram.memoria)
    elif cmd == "cd":
        if len(tokens) < 2:
            print("Uso: CD nomepasta")
        else:
            alvo = tokens[1]
            if alvo == "..":
                if diretorio_atual != "/":
                    diretorio_atual = "/".join(diretorio_atual.rstrip("/").split("/")[:-1])
                if diretorio_atual == "":
                    diretorio_atual = "/"
            else:
                novo_caminho = obter_caminho_absoluto(alvo, diretorio_atual)
                if disco.e_pasta(novo_caminho):
                    diretorio_atual = novo_caminho
                else:
                    print(f"Diretório não encontrado: {alvo}")
    elif cmd == "copiar":
        if len(tokens) < 3:
            print("Uso: COPIAR arquivo_origem arquivo_destino")
        else:
            origem = obter_caminho_absoluto(tokens[1], diretorio_atual)
            destino = obter_caminho_absoluto(tokens[2], diretorio_atual)
            conteudo = ram.obter(origem)
            if conteudo is None:
                conteudo = disco.ler_arquivo(origem)
                if conteudo == "[Arquivo não encontrado]":
                    print(f"Arquivo de origem '{origem}' não encontrado.")
                    return diretorio_atual
            ram.carregar(destino, conteudo)
            disco.escrever_arquivo(destino, conteudo)
            print(f"Copiado '{origem}' para '{destino}'")
    elif cmd == "renomear":
        if len(tokens) < 3:
            print("Uso: RENOMEAR nome_antigo nome_novo")
        else:
            nome_antigo = obter_caminho_absoluto(tokens[1], diretorio_atual)
            nome_novo = obter_caminho_absoluto(tokens[2], diretorio_atual)
            conteudo = ram.obter(nome_antigo)
            if conteudo is None:
                conteudo = disco.ler_arquivo(nome_antigo)
            ram.memoria.pop(nome_antigo, None)
            ram.carregar(nome_novo, conteudo)
            disco.apagar_arquivo(nome_antigo)
            disco.escrever_arquivo(nome_novo, conteudo)
            print(f"Renomeado '{nome_antigo}' para '{nome_novo}'")
    elif cmd == "apagar":
        if len(tokens) < 2:
            print("Uso: APAGAR nomearquivo")
        else:
            nome_arquivo = obter_caminho_absoluto(tokens[1], diretorio_atual)
            ram.memoria.pop(nome_arquivo, None)
            disco.apagar_arquivo(nome_arquivo)
            print(f"Excluído '{nome_arquivo}'")
    elif cmd == "carregarram":
        if len(tokens) < 3:
            print("Uso: CARREGARRAM chave valor")
        else:
            chave = obter_caminho_absoluto(tokens[1], diretorio_atual)
            valor = " ".join(tokens[2:])
            ram.carregar(chave, valor)
            print(f"Carregado na RAM: {chave}")
    elif cmd == "limparram":
        ram.limpar()
        print("RAM limpa.")
    elif cmd == "mostrarram":
        if ram.memoria:
            print("Conteúdo da RAM:")
            for k, v in ram.memoria.items():
                print(f"{k} : {v}")
        else:
            print("RAM está vazia.")
    elif cmd == "sistemainfo":
        info_cpu = cpu.obter_info()
        info_ram = ram.obter_info()
        info_disco = disco.obter_info()
        desenhar_titulo("INFORMAÇÕES DO SISTEMA MS-PyDOS", 66)
        print(f"CPU   : Ciclos executados: {info_cpu['ciclos']}")
        print(f"RAM   : {info_ram['total_kb']} KB total | Usado: {info_ram['usado_kb']} KB | Livre: {info_ram['livre_kb']} KB")
        print(f"DISCO : {info_disco['max_kb']} KB total | Usado: {info_disco['usado_kb']} KB | Livre: {info_disco['livre_kb']} KB | Arquivos: {info_disco['total_arquivos']}")
        desenhar_divisoria(66)
        print("Dados reais da máquina:")
        info_ram_real = obter_info_ram_sistema()
        if info_ram_real:
            if info_ram_real.get("livre_mb") is not None:
                print(f"  RAM real  : {info_ram_real['total_mb']} MB total | {info_ram_real['livre_mb']} MB livres")
            else:
                print(f"  RAM real  : {info_ram_real['total_mb']} MB total")
        else:
            print("  RAM real  : indisponível neste ambiente")
        info_disco_real = obter_info_disco_sistema()
        if info_disco_real:
            print(f"  Disco real: {info_disco_real['total_gb']:.1f} GB total | {info_disco_real['livre_gb']:.1f} GB livres")
        else:
            print("  Disco real: indisponível neste ambiente")
        desenhar_rodape(66)
    elif cmd == "reiniciar":
        print("Salvando conteúdo da RAM no Disco e reiniciando...")
        disco.escrever_em_massa(ram.memoria)
        ram.limpar()
        inicializar()
        return diretorio_atual
    elif cmd == "formatar":
        confirmar = input("Tem certeza que deseja formatar o disco? (s/n): ").strip().lower()
        if confirmar == "s":
            disco.formatar()
            print("Disco formatado com sucesso. Reiniciando...")
            ram.limpar()
            inicializar()
        else:
            print("Formatação cancelada.")
    elif cmd == "limparcpu":
        cpu.limparcpu()
        print("Ciclos da CPU zerados.")
    elif cmd == "ams":
        escanear_ams(ram, disco=disco, silencioso=False, excluir=True)
    elif cmd == "executar":
        if len(tokens) < 2:
            print("Uso: EXECUTAR nomearquivo")
        else:
            nome_arquivo = obter_caminho_absoluto(tokens[1], diretorio_atual)
            conteudo = disco.ler_arquivo(nome_arquivo)
            if conteudo in ("[Arquivo não encontrado]", "[É uma pasta]"):
                print(f"Aplicação não encontrada: {tokens[1]}")
                return diretorio_atual
            linhas = conteudo.splitlines()
            if not linhas:
                print(f"Não é possível executar {tokens[1]}: Arquivo vazio!")
                return diretorio_atual
            primeira_linha = linhas[0].strip()
            if "utf8" not in primeira_linha.lower():
                print(f"Não é possível executar {tokens[1]}: Acesso negado.")
                return diretorio_atual
            linhas_para_executar = [primeira_linha.replace("utf8","",1).strip()] if len(linhas)==1 else linhas[1:]
            for linha in linhas_para_executar:
                linha = linha.strip()
                if not linha:
                    continue
                subcomandos = linha.split(";")
                for subcmd_linha in subcomandos:
                    sub_tokens = cpu.executar(subcmd_linha.strip())
                    executar_comando(sub_tokens, cpu, ram, disco, diretorio_atual)

    # ==================== COMANDOS DO SIMULADOR SO ====================
    elif cmd == "criarprocesso":
        if len(tokens) < 5:
            print("Uso: CRIARPROCESSO nome prioridade tempo memoria")
        else:
            try:
                nome = tokens[1]
                prioridade = int(tokens[2])
                tempo = int(tokens[3])
                memoria = int(tokens[4])
                pid = simulador_ms.criar_processo(nome, prioridade, tempo, memoria)
                if pid is not None:
                    print(f"Processo criado com sucesso. PID: {pid}")
            except ValueError:
                print("Erro: Use valores numéricos válidos.")
    elif cmd == "listarprocessos":
        simulador_ms.listar_processos()
    elif cmd == "terminarprocesso":
        if len(tokens) < 2:
            print("Uso: TERMINARPROCESSO pid")
        else:
            try:
                pid = int(tokens[1])
                simulador_ms.terminar_processo(pid)
            except ValueError:
                print("Erro: PID inválido.")
    elif cmd == "executarciclo":
        simulador_ms.executar_ciclo()
    elif cmd == "exibirmemoria":
        simulador_ms.exibir_memoria()
    elif cmd == "testarmemoria":
        if len(tokens) < 3:
            print("Uso: TESTARMEMORIA pid tamanho")
        else:
            try:
                pid = int(tokens[1])
                tamanho = int(tokens[2])
                if simulador_ms.alocar_memoria(tamanho, pid):
                    print("Memória alocada com sucesso!")
                else:
                    print("Falha na alocação de memória.")
            except ValueError:
                print("Erro: Use valores numéricos válidos.")
    elif cmd == "criararquivoso":
        if len(tokens) < 3:
            print("Uso: CRIARARQUIVOSO nome pid_dono [dados]")
        else:
            try:
                nome = tokens[1]
                pid_dono = int(tokens[2])
                dados = " ".join(tokens[3:]) if len(tokens) > 3 else ""
                simulador_ms.criar_arquivo_so(nome, pid_dono, dados)
            except ValueError:
                print("Erro: PID inválido.")
    elif cmd == "abrirarquivo":
        if len(tokens) < 2:
            print("Uso: ABRIRARQUIVO nome")
        else:
            simulador_ms.abrir_arquivo_so(tokens[1])
    elif cmd == "fechararquivo":
        if len(tokens) < 2:
            print("Uso: FECHARARQUIVO nome")
        else:
            simulador_ms.fechar_arquivo_so(tokens[1])
    elif cmd == "escreverarquivo":
        if len(tokens) < 3:
            print("Uso: ESCREVERARQUIVO nome dados")
        else:
            nome = tokens[1]
            dados = " ".join(tokens[2:])
            simulador_ms.escrever_arquivo_so(nome, dados)
    elif cmd == "lerarquivo":
        if len(tokens) < 2:
            print("Uso: LERARQUIVO nome")
        else:
            conteudo = simulador_ms.ler_arquivo_so(tokens[1])
            if conteudo is not None:
                print(f"Conteúdo: {conteudo}")
    elif cmd == "apagararquivo":
        if len(tokens) < 2:
            print("Uso: APAGARARQUIVO nome")
        else:
            simulador_ms.deletar_arquivo_so(tokens[1])
    elif cmd == "listararquivos":
        simulador_ms.listar_arquivos_so()
    elif cmd == "solicitarrecurso":
        if len(tokens) < 3:
            print("Uso: SOLICITARRECURSO pid tipo(IMPRESSORA/DISCO/FITA)")
        else:
            try:
                pid = int(tokens[1])
                tipo_str = tokens[2].upper()
                tipos = {"IMPRESSORA": TipoRecurso.IMPRESSORA, "DISCO": TipoRecurso.DISCO, "FITA": TipoRecurso.FITA}
                if tipo_str in tipos:
                    simulador_ms.solicitar_recurso(pid, tipos[tipo_str])
                else:
                    print("Tipo inválido. Use: IMPRESSORA, DISCO ou FITA")
            except ValueError:
                print("Erro: PID inválido.")
    elif cmd == "liberarrecurso":
        if len(tokens) < 3:
            print("Uso: LIBERARRECURSO pid tipo(IMPRESSORA/DISCO/FITA)")
        else:
            try:
                pid = int(tokens[1])
                tipo_str = tokens[2].upper()
                tipos = {"IMPRESSORA": TipoRecurso.IMPRESSORA, "DISCO": TipoRecurso.DISCO, "FITA": TipoRecurso.FITA}
                if tipo_str in tipos:
                    simulador_ms.liberar_recurso(pid, tipos[tipo_str])
                else:
                    print("Tipo inválido. Use: IMPRESSORA, DISCO ou FITA")
            except ValueError:
                print("Erro: PID inválido.")
    elif cmd == "listarrecursos":
        simulador_ms.listar_recursos()
    elif cmd == "semaforop":
        if len(tokens) < 2:
            print("Uso: SEMAFOROP nome")
        else:
            simulador_ms.semaforo_p(tokens[1])
    elif cmd == "semaforov":
        if len(tokens) < 2:
            print("Uso: SEMAFOROV nome")
        else:
            simulador_ms.semaforo_v(tokens[1])
    elif cmd == "listarsemaforos":
        simulador_ms.listar_semaforos()
    elif cmd == "estatisticas":
        simulador_ms.estatisticas()
    elif cmd == "mostrarlog":
        simulador_ms.mostrar_log()
    elif cmd == "carregarexemplos":
        simulador_ms.carregar_processos_exemplo()
        print("Processos de exemplo carregados!")
    elif cmd == "executarsimulacao":
        ciclos = 10
        if len(tokens) > 1:
            try:
                ciclos = int(tokens[1])
            except ValueError:
                print("Erro: Número de ciclos inválido, usando padrão (10).")
        simulador_ms.executar_simulacao(ciclos)
    else:
        print(f"Comando inválido ou arquivo não encontrado: {cmd}")

    return diretorio_atual

# --- TERMINAL ---
def iniciar_terminal(cpu, ram, disco):
    lista_categorias = ", ".join(CATEGORIAS_AJUDA.keys())
    print(f"\nMS-PyDOS v1.0 - Máquina de Shopping\nUsuário: {usuario_atual}\n"
          f"Digite AJUDA para ver os comandos (por categoria) ou AJUDA <categoria>.\n"
          f"Categorias disponíveis: {lista_categorias}\n")
    diretorio_atual = "/"
    while True:
        try:
            comando = input(f"C:{diretorio_atual}> ").strip()
            tokens = cpu.executar(comando)
            diretorio_atual = executar_comando(tokens, cpu, ram, disco, diretorio_atual)
        except KeyboardInterrupt:
            print("\nUse SAIR para sair.")
        except SystemExit:
            dos_desligar_tela_azul()
            raise
        except Exception as e:
            print(f"[ERRO] {e}")

# --- INICIALIZAÇÃO (BOOT) ---
def inicializar():
    global disco_obj, simulador_ms, gerenciador_usuarios, usuario_atual
    dos_ligar_tela_azul()
    print("MS-PyDOS v1.0 - Máquina de Shopping - Inicializando...")
    time.sleep(0.1)
    print("Inicializando CPU...")
    print(f"  Processador detectado: {platform.processor() or platform.machine()} "
          f"({os.cpu_count() or '?'} núcleo(s) lógico(s))")
    cpu_obj = CPU()
    time.sleep(0.05)
    print("Inicializando RAM...")
    ram_obj = RAM()
    info_ram_real = obter_info_ram_sistema()
    if info_ram_real:
        if info_ram_real.get("livre_mb") is not None:
            print(f"  RAM real detectada: {info_ram_real['total_mb']} MB total | "
                  f"{info_ram_real['livre_mb']} MB livres")
        else:
            print(f"  RAM real detectada: {info_ram_real['total_mb']} MB total")
    else:
        print("  RAM real: não foi possível detectar neste ambiente.")
    time.sleep(0.05)
    print("Verificando DISCO...")
    disco_obj = Disco()
    info_disco_real = obter_info_disco_sistema()
    if info_disco_real:
        print(f"  Armazenamento real detectado: {info_disco_real['total_gb']:.1f} GB total | "
              f"{info_disco_real['livre_gb']:.1f} GB livres")
    else:
        print("  Armazenamento real: não foi possível detectar neste ambiente.")
    time.sleep(0.05)
    print("Iniciando módulo de processos do MS-PyDOS...")
    simulador_ms = SimuladorSO(memoria_total=1024, quantum=2)
    time.sleep(0.05)
    print("Inicialização bem sucedida.")
    time.sleep(0.1)

    gerenciador_usuarios = GerenciadorUsuarios()
    usuario_atual = tela_boas_vindas_usuario(gerenciador_usuarios)
    if not usuario_atual:
        print("Não foi possível autenticar nenhum usuário. Encerrando o MS-PyDOS.")
        dos_desligar_tela_azul()
        sys.exit()

    iniciar_terminal(cpu_obj, ram_obj, disco_obj)

if __name__ == "__main__":
    inicializar()
