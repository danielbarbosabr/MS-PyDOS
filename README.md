# MS-PyDOS

Simulador de sistema operacional escrito em Python (terminal interativo), com:
comandos em português, gerenciamento de processos, memória, sistema de arquivos,
recursos compartilhados, semáforos, log, estatísticas e uma área de pesquisa
(Google, YouTube, Pirate Bay e ativador MAS).

O arquivo principal do aplicativo é **`MS-PyDOS.py`** (contém todo o código do MS-PyDOS).

## Como funciona (Instalar x Iniciar)

Os instaladores têm um menu com 3 opções:

- **[1] Instalar** → verifica o Python (reutiliza se já existir, ou instala
  automaticamente via `winget`/instalador oficial no Windows ou `apt`/`dnf`/
  `pacman`/`zypper` no Linux), cria o ambiente virtual (`venv`), prepara as
  dependências, cria os atalhos e **já abre o MS-PyDOS automaticamente** ao
  terminar.
- **[2] Iniciar** → apenas abre o MS-PyDOS usando o Python do `venv` que o
  "Instalar" já preparou. Não baixa nem instala nada. Se ainda não tiver
  instalado, avisa para rodar a opção [1] primeiro.
- **[3] Sair**

Ou seja: da primeira vez use **Instalar** (ele cuida de tudo, inclusive do
Python, e abre o app sozinho). Depois, use **Iniciar** para abrir rápido, ou o
atalho do Menu Iniciar / Área de Trabalho / `.desktop`. Nenhuma execução depende
do `python`/`python3` estar no PATH: sempre usa o interpretador dentro do
`venv` (ex.: `venv\Scripts\python.exe` ou `venv/bin/python`).

## Arquivo único para os dois sistemas

`MS-PyDOS` é um launcher **universal** (um só arquivo serve para Windows e Linux):

- **Windows**: renomeie/copie para `MS-PyDOS.bat` e de duplo clique.
- **Linux**: rode `bash MS-PyDOS` (ou `sh MS-PyDOS`).

Ele detecta o sistema e chama o instalador nativo correto
(`MS-PyDOS.Windows.bat` ou `MS-PyDOS.Linux.sh`).

## Instalação automática

Não é necessário instalar o Python manualmente. Basta rodar o instalador:
### Windows

Clique duas vezes em `MS-PyDOS.Windows.bat` (ou rode no Prompt como usuário normal).
Ele vai:
1. Detectar se o Python já existe; se não, instala silenciosamente (prefere
   `winget`, com fallback para o instalador oficial).
2. Criar um ambiente virtual (`venv`) e preparar as dependências.
3. Criar atalhos no **Menu Iniciar** e na **Área de Trabalho** (apontando
   direto para `venv\Scripts\python.exe`).
4. **Abrir o MS-PyDOS automaticamente** ao concluir.

Depois, abra o **MS-PyDOS** pelo atalho ou pela opção [2] INICIAR, como um
aplicativo normal.

### Linux
No terminal, na pasta do projeto:
```bash
bash MS-PyDOS.Linux.sh
```
Ele detecta a distribuição (`apt`/`dnf`/`pacman`/`zypper`), instala o Python 3
se preciso, cria o `venv` e cria um arquivo `.desktop`
no menu de aplicativos.

## Como usar
- Digite `AJUDA` para ver os comandos (por categoria).
- Categoria `pesquisar`: `PESQUISAR`, `YOUTUBE`, `PIRATEBAY`, `MASSGRAVE`.
- Para sair: `SAIR`.

## Gerar executável (opcional)
Para o usuário final não precisar saber que é Python, instale o `pyinstaller`
(dentro do `venv`: `venv\Scripts\pip install pyinstaller` no Windows ou
`./venv/bin/pip install pyinstaller` no Linux) e rode:
```bash
# Windows
venv\Scripts\pyinstaller --onefile --console MS-PyDOS.py
# Linux
./venv/bin/pyinstaller --onefile MS-PyDOS.py
```
O binário ficará em `dist/`.

## Observações
- O instalador **não apaga** arquivos, configurações ou dados do usuário.
- Se o Python já estiver instalado, nenhuma instalação extra é feita.
- Todos os caminhos são relativos; o app funciona em qualquer máquina.
