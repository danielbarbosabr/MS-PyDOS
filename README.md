<img width="1844" height="853" alt="image" src="https://github.com/user-attachments/assets/ca5d0328-dc17-4aaa-9a8d-4802741acf67" />

# ⚙️ MS-PyDOS

[![Status](https://img.shields.io/badge/status-concluído-brightgreen)](https://github.com/seu-usuario/MS-PyDOS)
[![Licença](https://img.shields.io/badge/licença-MIT-yellow)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.7%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Deployments](https://img.shields.io/badge/deployments-1-blue)](https://github.com/seu-usuario/MS-PyDOS/deployments)

![Terminal](https://img.shields.io/badge/Interface-Terminal-4EAA25?logo=gnometerminal&logoColor=white)
![POO](https://img.shields.io/badge/Paradigma-OO-9B59B6?logo=python&logoColor=white)
![Conceitos](https://img.shields.io/badge/Conceitos-SO-FF6F00?logo=linux&logoColor=white)

---

## <img src="https://api.iconify.design/bi/info-circle-fill.svg?color=%234FC3F7" width="20" height="20"> Sobre o Projeto

O **MS-PyDOS** é um **Simulador de Sistema Operacional** desenvolvido em Python com finalidade educacional. Ele foi criado como parte de um **Projeto Integrador** do curso de graduação, com o objetivo de demonstrar, na prática, os principais conceitos teóricos de Sistemas Operacionais.

O simulador funciona como um terminal interativo que replica o gerenciamento de recursos de um SO real, permitindo que o usuário:
- Gerencie **processos**, seus estados e prioridades.
- Execute o **escalonamento Round Robin** com um quantum definido.
- Controle a **memória** usando o algoritmo **First Fit**.
- Manipule um **sistema de arquivos** simplificado.
- Solicite e libere **recursos** (impressora, disco, fita).
- Utilize **semáforos** para demonstrar exclusão mútua.
- Acompanhe a simulação através de **logs** e **estatísticas** em tempo real.

O projeto não executa um sistema operacional real, mas sim uma **simulação fiel dos mecanismos internos**, ideal para aprendizado e demonstração de conceitos fundamentais.

---

## <img src="https://api.iconify.design/bi/rocket-takeoff-fill.svg?color=%234FC3F7" width="20" height="20"> Funcionalidades

### <img src="https://api.iconify.design/bi/cpu-fill.svg?color=%234FC3F7" width="18" height="18"> Gerenciamento de Processos
- Criação de processos com PID, nome, prioridade (1-10), tempo de CPU e memória alocada.
- Controle de estados: **NOVO**, **PRONTO**, **EXECUTANDO**, **BLOQUEADO**, **TERMINADO**.
- Armazenamento em **PCB (Process Control Block)**.
- Listagem detalhada de todos os processos ativos.
- Finalização manual de processos com liberação automática de recursos.

### <img src="https://api.iconify.design/bi/clock-fill.svg?color=%234FC3F7" width="18" height="18"> Escalonamento Round Robin
- Implementação do algoritmo **Round Robin** com quantum configurável (padrão: 2 unidades).
- Alternância automática entre processos na fila de prontos.
- Relógio lógico para controle de tempo de simulação.
- Processo atual identificado e controlado durante a execução.

### <img src="https://api.iconify.design/bi/memory.svg?color=%234FC3F7" width="18" height="18"> Gerenciamento de Memória
- Memória principal simulada de **1024 KB**, dividida em partições dinâmicas.
- Algoritmo de alocação **First Fit**.
- Painel de visualização com status de cada partição, endereços e utilização.
- Cálculo de memória utilizada, livre e taxa de ocupação.

### <img src="https://api.iconify.design/bi/folder-fill.svg?color=%234FC3F7" width="18" height="18"> Sistema de Arquivos
- Criação, abertura, fechamento, leitura e escrita de arquivos.
- Cada arquivo possui nome, tamanho, estado, PID dono, conteúdo e data de criação.
- Listagem de todos os arquivos do sistema.
- Fechamento automático de arquivos ao finalizar um processo.

### <img src="https://api.iconify.design/bi/printer-fill.svg?color=%234FC3F7" width="18" height="18"> Gerenciamento de Recursos e Sincronização
- Simulação de recursos de hardware: **Impressora, Disco e Fita**.
- Solicitação e liberação de recursos com controle de exclusão mútua.
- Implementação de **semáforos** com operações **P** (aquisição) e **V** (liberação).
- Painel para visualizar o estado de todos os recursos e semáforos.

### <img src="https://api.iconify.design/bi/terminal-fill.svg?color=%234FC3F7" width="18" height="18"> Interface de Usuário (Terminal)
- Menu principal intuitivo com acesso a todas as funcionalidades.
- Submenus para cada área de gerenciamento (Processos, Memória, Arquivos, Recursos).
- Entrada de dados validada com tratamento de erros.
- Navegação simples para simular a operação de um sistema real.

### <img src="https://api.iconify.design/bi/bar-chart-fill.svg?color=%234FC3F7" width="18" height="18"> Logs e Estatísticas
- **Log de eventos** completo com carimbo de tempo (clock da simulação).
- Estatísticas consolidadas: tempo total, processos criados/finalizados/ativos, memória utilizada, quantidade de arquivos.
- Simulação automática com criação de processos de exemplo e execução de ciclos.

---

## <img src="https://api.iconify.design/bi/cpu-fill.svg?color=%234FC3F7" width="20" height="20"> Tecnologias Utilizadas

| Camada | Tecnologia |
|--------|------------|
| **Linguagem** | Python 3.7+ |
| **Paradigma** | Programação Orientada a Objetos (POO) |
| **Estruturas de Dados** | Dataclasses, Listas, Dicionários, Enumerações |
| **Conceitos de SO** | PCB, Round Robin, First Fit, Semáforos, Estados de Processo |
| **Interface** | Terminal (CLI) com menus interativos |
| **Documentação** | Markdown (README) |

---

## <img src="https://api.iconify.design/bi/folder2-open.svg?color=%234FC3F7" width="20" height="20"> Estrutura do Projeto

A estrutura do projeto é **simples e autocontida**, com todo o código em um único arquivo para facilitar a execução e distribuição, conforme solicitado para o trabalho acadêmico.
