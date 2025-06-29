import sys, os, subprocess, requests, time, socket, threading

# Token do bot e URL base
TOKEN = '7610954512:AAFX1g8OZQ7vsOWg7R4fQoh7_OPhQmft4NU'
strURL = f'https://api.telegram.org/bot{TOKEN}'
ultimo_update_id = 0  

# Configuração do servidor
HOST = '192.168.1.20'
PORT_BOT = 5001              # Porta para comunicação com o bot
PORT_CLIENTE = 5002          # Porta para comunicação com os clientes (agentes)
PORT_COMUNICACAO_BOT = 5003  # Porta separada para comunicação do bot com o servidor

# Cada entrada terá os dados: host, ip, usuário, tempo_online e o socket do cliente.
clientes_conectados = {}

# Define o caminho correto para o arquivo de bloqueio
if os.name == 'nt':  # Windows
    LOCK_DIR = 'C:\\temp'
    LOCK_FILE = os.path.join(LOCK_DIR, 'server.lock')
else:  # Linux
    LOCK_DIR = '/tmp'
    LOCK_FILE = os.path.join(LOCK_DIR, 'server.lock')

def verificar_instancia():
    """Impede que mais de uma instância do cliente seja executada."""
    try:
        if not os.path.exists(LOCK_DIR):
            os.makedirs(LOCK_DIR)
        if os.path.exists(LOCK_FILE):
            print("⚠️ O servidor já está em execução!")
            sys.exit()
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"❌ Erro ao criar arquivo de bloqueio: {e}")
        sys.exit()

def remover_arquivo_bloqueio():
    """Remove o arquivo de bloqueio e encerra o programa corretamente."""
    print("\n⏹️ Servidor encerrado pelo usuário.")
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
    sys.exit()

def obter_mensagens():
    global ultimo_update_id
    parametros = {'timeout': 5, 'offset': ultimo_update_id}
    getRequisicao = requests.get(strURL + '/getUpdates', params=parametros)

    if getRequisicao.status_code != 200:
        sys.exit('\nERRO : Erro na requisição...\n')

    return getRequisicao.json()

def enviar_resposta(chat_id, mensagem):
    dictDados = {'chat_id': chat_id, 'text': mensagem}
    requests.post(strURL + '/sendMessage', data=dictDados)

def processar_comandos():
    global ultimo_update_id
    while True:
        jsonRetorno = obter_mensagens()
        
        if jsonRetorno['result']:
            for update in jsonRetorno['result']:
                if 'message' in update:
                    mensagem = update['message']
                    chat_id = mensagem['chat']['id']
                    texto = mensagem.get('text', '')

                    print(f"📨 Mensagem recebida: {texto}")

                    if texto == '/start':
                        resposta = ("🤖 Bem-vindo ao AgenteHardware! \n\n"
                                    "Sou um sistema cliente-servidor desenvolvido em Python. Minha função é gerenciar múltiplos clientes que me enviam informações sobre hardware, usuários e histórico do sistema.\n\n"
                                    "Para ver os comandos disponíveis, digite /help. Caso já saiba o comando desejado, basta enviá-lo e estarei pronto para responder!")
                    elif texto == '/help':
                        resposta = ("📲 Comandos disponíveis:\n\n"
                                    "• /listar_agentes - Lista todos os agentes online, mostrando IP, nome do host, usuário logado e tempo de conexão.\n"
                                    "• /info_hardware - Solicita informações de hardware dos agentes (CPU, memória, disco, SO).\n"
                                    "• /programas_instalados - Retorna a lista de programas instalados nos dispositivos (Windows e Linux).\n"
                                    "• /historico_navegacao - Obtém o histórico de navegação dos principais navegadores (Chrome, Firefox, Edge, Opera, Safari).\n"
                                    "• /info_usuario - Mostra informações detalhadas do usuário logado (UID, grupos, diretório home, shell padrão, etc.).\n"
                                    "• /encerrar - Encerra a comunicação com o bot.")
                    elif texto == '/encerrar':
                        resposta = "Até logo! Você pode enviar uma mensagem a qualquer momento que estarei pronto para ajudar."
                    elif texto.startswith(('/listar_agentes', '/info_hardware', '/programas_instalados', '/historico_navegacao', '/info_usuario')):
                        resposta = enviar_para_servidor(texto)
                    else:
                        resposta = "❓ Comando não reconhecido. Tente /start ou /help."
                    
                    enviar_resposta(chat_id, resposta)
                    ultimo_update_id = update['update_id'] + 1
        
        time.sleep(0.5)  # Evita sobrecarga na API do Telegram

def enviar_para_servidor(comando):
    """ O bot envia um comando para o servidor na porta de comunicação e aguarda a resposta. """
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((HOST, PORT_COMUNICACAO_BOT))
        cliente.send(comando.encode())
        resposta = cliente.recv(4096).decode()
        cliente.close()
        return resposta
    except Exception as e:
        return f"❌ Erro na conexão com o servidor: {e}"

def remover_cliente(endereco):
    """ Remove um cliente da lista de clientes conectados. """
    if endereco in clientes_conectados:
        del clientes_conectados[endereco]
        print(f"🔌 Cliente {endereco} desconectado e removido da lista.")

def lidar_com_cliente(cliente_socket, endereco_cliente):
    """Lida com um cliente conectado: recebe seus dados iniciais e armazena o socket para comunicação futura."""
    try:
        print(f"🖥️ Cliente conectado: {endereco_cliente}")
        dados_recebidos = cliente_socket.recv(1024).decode()
        host, ip, usuario = dados_recebidos.split(',')
        clientes_conectados[endereco_cliente] = {
            "host": host,
            "ip": ip,
            "usuario": usuario,
            "tempo_online": time.time(),
            "socket": cliente_socket
        }
        print(f"📥 Cliente registrado: {host} ({ip}) - Usuário: {usuario}")

        # Loop de heartbeat para monitorar a conexão sem consumir dados.
        while True:
            time.sleep(1)
            try:
                # Define um timeout curto para o heartbeat.
                cliente_socket.settimeout(20)
                # O uso de MSG_PEEK permite verificar se há dados sem removê-los do buffer.
                data = cliente_socket.recv(1, socket.MSG_PEEK)
                if not data:
                    print(f"Cliente {endereco_cliente} desconectado (MSG_PEEK retornou vazio).")
                    break
            except socket.timeout:
                # Se ocorrer timeout, não há dados prontos, mas a conexão provavelmente está ativa.
                continue
            except Exception as e:
                print(f"Erro ao verificar conexão do cliente {endereco_cliente}: {e}")
                break

    except Exception as e:
        print(f"❌ Erro com o cliente {endereco_cliente}: {e}")
    finally:
        remover_cliente(endereco_cliente)
        cliente_socket.close()

def aceitar_conexoes_clientes():
    """ Aceita múltiplas conexões de clientes (agentes). """
    servidor_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_cliente.bind((HOST, PORT_CLIENTE))
    servidor_cliente.listen(5)
    print(f"🖥️ Servidor (Clientes) iniciado em {HOST}:{PORT_CLIENTE}")

    while True:
        cliente_socket, endereco_cliente = servidor_cliente.accept()
        threading.Thread(target=lidar_com_cliente, args=(cliente_socket, endereco_cliente)).start()

def aceitar_conexoes_bot():
    """
    Aceita conexões do bot para receber comandos.
    - Se o comando for /listar_agentes, utiliza os dados armazenados.
    - Se for um dos outros comandos (/info_hardware, /programas_instalados, /historico_navegacao, /info_usuario),
      o servidor repassa o comando a cada cliente e agrega as respostas.
    """
    servidor_comunicacao_bot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_comunicacao_bot.bind((HOST, PORT_COMUNICACAO_BOT))
    servidor_comunicacao_bot.listen(1)
    print(f"🤖 Servidor (Comunicacao Bot) iniciado em {HOST}:{PORT_COMUNICACAO_BOT}")

    while True:
        bot_socket, endereco_bot = servidor_comunicacao_bot.accept()
        print(f"✅ Bot conectado para comunicação: {endereco_bot}")

        try:
            comando = bot_socket.recv(1024).decode().strip()
            print(f"📨 Comando recebido do bot: {comando}")

            if comando == '/listar_agentes':
                if clientes_conectados:
                    resposta = "\n".join([
                        f"🔹 {dados['host']} ({dados['ip']}) - Usuário: {dados['usuario']} - Online há {divmod(int(time.time() - dados['tempo_online']), 60)[0]}m{divmod(int(time.time() - dados['tempo_online']), 60)[1]}s"
                        for dados in clientes_conectados.values()
                    ])
                else:
                    resposta = "Nenhum agente conectado."
                bot_socket.send(resposta.encode())
                print("✅ Resposta enviada para o bot com sucesso!")

            elif comando in ['/info_hardware', '/programas_instalados', '/historico_navegacao', '/info_usuario']:
                respostas = []
                for endereco, dados in clientes_conectados.items():
                    client_socket = dados.get("socket")
                    if client_socket:
                        try:
                            client_socket.send(comando.encode())
                            resposta_cliente = client_socket.recv(4096).decode()
                            respostas.append(f"🔹 {dados['host']} ({dados['ip']}):\n{resposta_cliente}")
                        except Exception as e:
                            respostas.append(f"🔹 {dados['host']} ({dados['ip']}): Erro ao obter resposta ({e})")
                resposta = "\n\n".join(respostas) if respostas else "Nenhum agente disponível para responder."
                bot_socket.send(resposta.encode())

            else:
                resposta = "Comando não reconhecido."
                bot_socket.send(resposta.encode())
        
        except Exception as e:
            print(f"❌ Erro na comunicação com o bot: {e}")
        finally:
            bot_socket.close()
            print("🔌 Conexão com bot encerrada.")

def main():
    threading.Thread(target=aceitar_conexoes_clientes, daemon=True).start()
    threading.Thread(target=aceitar_conexoes_bot, daemon=True).start()
    threading.Thread(target=processar_comandos, daemon=True).start()
    print("🔄 Servidor rodando... Pressione Ctrl+C para encerrar.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        remover_arquivo_bloqueio()

if __name__ == "__main__":
    verificar_instancia()
    main()