[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/FIFVwXUS)
[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=17959693&assignment_repo_type=AssignmentRepo)


  # Projeto Agente Hardware

O Projeto Agente Hardware é um sistema completo de monitoramento em rede baseado em Python, composto por três componentes principais: um Servidor, múltiplos Clientes (Agentes) e um Bot no Telegram. O sistema foi desenvolvido para coletar e gerenciar informações detalhadas de dispositivos, possibilitando o monitoramento remoto de hardware, softwares instalados, histórico de navegação e dados do usuário logado.

## Objetivo do Projeto :

Este projeto implementa uma arquitetura cliente-servidor onde:

• Clientes (Agentes): São instalados em dispositivos remotos e responsáveis por coletar informações do sistema e enviá-las ao servidor.

• Servidor: Gerencia múltiplas conexões simultâneas de agentes, repassa comandos recebidos via bot para os clientes, agrega as respostas dos clientes e repassa para o bot.

• Bot no Telegram: Atua como interface para que o usuário envie comandos e receba respostas, facilitando o monitoramento remoto por meio da API do Telegram.

## Arquitetura
A arquitetura do sistema é composta pelos seguintes módulos interligados:

• 🧑‍💻 Cliente (Agente):

  • Conexão e Registro: Ao iniciar, o agente se conecta ao servidor e envia informações iniciais (nome do host, IP e usuário logado).
  
  • Coleta de Dados: Monitora e coleta informações do hardware, lista de programas instalados, histórico dos navegadores e dados do usuário.
 
  • Execução de Comandos: Responde a comandos enviados pelo servidor, executando as funções solicitadas.
 
  • Controle de Instância: Utiliza arquivos de bloqueio para garantir que apenas uma instância seja executada por máquina.

• 🗄️ Servidor:

  • Gerenciamento de Conexões: Aceita conexões simultâneas dos agentes e mantém um registro atualizado de cada dispositivo conectado.
 
  • Processamento de Comandos: Recebe comandos enviados pelo bot do Telegram, encaminha para os agentes e agrega as respostas.
  
  • Comunicação com o Bot: Utiliza uma porta dedicada para comunicação com o bot, permitindo a troca de mensagens em tempo real.

• 🤖 Bot no Telegram:

  • Interface de Usuário: Permite que o usuário envie comandos e visualize as respostas do sistema.
 
  • Integração com a API do Telegram: Realiza o polling de mensagens, processa os comandos e envia respostas de volta ao usuário.


• Diagrama de Arquitetura (Exemplo):


![arquitetura do meu bot](https://github.com/user-attachments/assets/adeb0891-0c46-4de0-81b9-610f41aeb449)


# :calling: Protocolo de Comandos
O usuário interage com o sistema através do bot do Telegram, utilizando os seguintes comandos:

• /listar_agentes
Lista todos os agentes online, mostrando o nome do host, IP, usuário logado e o tempo de conexão de cada um.

• /info_hardware
Solicita aos agentes informações sobre o hardware, incluindo CPU, memória, disco e sistema operacional.

• /programas_instalados
Retorna a lista de programas instalados nos dispositivos, com suporte para Windows e Linux.

• /historico_navegacao
Obtém os históricos de navegação dos principais navegadores (Chrome, Firefox, Edge, Opera e Safari) dos agentes.

• /info_usuario
Exibe informações detalhadas do usuário logado no agente, como UID, grupos, diretório home e shell padrão (em Linux) ou informações de grupos (em Windows).

# ⚙️ Tecnologias Utilizadas

• Python:
Linguagem principal utilizada no desenvolvimento do cliente, servidor e bot.

• Sockets TCP:
Comunicação em rede entre o servidor e os agentes, permitindo conexões simultâneas e troca de dados em tempo real.

• API do Telegram:
Para a interação do bot com os usuários, possibilitando o envio e recebimento de mensagens.

• Bibliotecas Padrão:
Utilização de módulos como socket, threading, subprocess, requests, entre outros, para implementar funcionalidades essenciais.

# Status do Projeto
Projeto Concluído e em Pleno Funcionamento

Todas as funcionalidades propostas foram implementadas e testadas:

• Conexão cliente-servidor com suporte a múltiplos agentes.

• Coleta o envio de informações detalhadas sobre hardware, programas instalados, histórico de navegação e dados do usuário.

• Integração completa com o bot do Telegram para envio e recepção de comandos.

• Gerenciamento robusto de conexões e prevenção de múltiplas instâncias de execução.

# Uso e Execução
## Servidor
1. Execute o script Botserver.py para iniciar o servidor.

2. O servidor abre as portas necessárias para comunicação com os agentes e com o bot do Telegram.

3. Arquivos de bloqueio são criados para evitar execuções múltiplas.

## Cliente (Agente)
1. Execute o script Cliente.py em cada máquina que se deseja monitorar.

2. O agente se conecta automaticamente ao servidor, enviando seus dados (host, IP e usuário) e aguardando comandos.

3. Caso a conexão seja perdida, o agente tenta reconectar periodicamente.

## Bot no Telegram
1. Utilize o bot (AgenteHardware_bot) no Telegram para enviar comandos.

2. Os comandos devem seguir o protocolo descrito acima para que o sistema responda adequadamente.

3. As respostas serão agregadas pelo servidor e enviadas de volta ao usuário via bot.



# 📌 Observações

• O sistema proporciona monitoramento contínuo dos dispositivos.

• Os arquivos de bloqueio implementados no cliente e servidor garantem a execução única e evitam conflitos.

• O projeto foi desenvolvido de forma modular, permitindo futuras expansões e melhorias.

• Sugestões, colaborações e feedback são bem-vindos!
