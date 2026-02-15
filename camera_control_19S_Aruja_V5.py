# --- Importações Essenciais ---
import time, os, sys, re
from datetime import datetime, time as time_obj
import requests
from PIL import Image, ImageOps, ImageStat
import io
from pymodbus.client import ModbusTcpClient

# --- Constantes e Configurações Globais ---
NOME_ARQUIVO_CONFIG = "config_pista_19S_Aruja.txt"
# ### ALTERADO ### Agora os nomes das pastas são apenas os nomes base
LOG_DIRECTORY_BASE = "logs_qualidade_camera"
DIRETORIO_IMAGENS_ALERTA_BASE = "imagens_com_alerta"
DIRETORIO_IMAGENS_CROPADAS_BASE = "imagens_cropadas_debug"
config = {}

# --- Funções ---

def encontrar_caminho_recurso(caminho_relativo):
    """
    Obtém o caminho absoluto para um recurso, funcionando de forma confiável
    tanto para scripts .py quanto para executáveis criados pelo PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        # Se for um executável, o caminho base é o diretório do próprio executável
        base_path = os.path.dirname(sys.executable)
    else:
        # Se for um script .py normal, o caminho base é o diretório do script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, caminho_relativo)


# ### FUNÇÃO CORRIGIDA PARA USAR CAMINHOS ABSOLUTOS ###
def log_message(message, nome_pista="script"):
    """Escreve uma mensagem no arquivo de log, garantindo que a pasta esteja no local correto."""
    try:
        # Constrói o caminho absoluto para o diretório de logs
        caminho_base = encontrar_caminho_recurso('')
        log_directory_path = os.path.join(caminho_base, LOG_DIRECTORY_BASE)

        os.makedirs(log_directory_path, exist_ok=True)
        log_file_name = f"{nome_pista}_{datetime.now().strftime('%Y-%m-%d')}.txt"
        log_file_path = os.path.join(log_directory_path, log_file_name)
        log_line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n"
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(log_line)
    except IOError as e:
        print(f"ERRO CRÍTICO no log: {e}")


def carregar_configuracoes(caminho_arquivo_txt):
    # (Esta função não precisa de alterações, pois ela já recebe o caminho completo)
    try:
        # ... (seu código de carregar_configuracoes permanece aqui) ...
        # Removi openpyxl pois você está usando .txt
        temp_config = {}
        with open(caminho_arquivo_txt, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.split('=', 1)
                    temp_config[key.strip()] = value.strip()

        config['NOME_PISTA'] = temp_config['NOME_PISTA']
        config['CAMERA_IP'] = temp_config['CAMERA_IP']
        config['CLP_IP'] = temp_config['CLP_IP']
        h, m = map(int, temp_config['HORA_ENCERRAMENTO'].split(':'))
        config['HORA_ENCERRAMENTO'] = time_obj(h, m)
        config['COORDENADAS_CROP'] = (int(temp_config['CROP_X1']), int(temp_config['CROP_Y1']),
                                      int(temp_config['CROP_X2']), int(temp_config['CROP_Y2']))
        config['PERFIL_NORMAL'] = {'shutter': int(temp_config['PERFIL_NORMAL_SHUTTER']),
                                   'gamma': int(temp_config['PERFIL_NORMAL_GAMMA'])}
        config['PERFIL_SOL_MEDIO'] = {'shutter': int(temp_config['PERFIL_SOL_MEDIO_SHUTTER']),
                                      'gamma': int(temp_config['PERFIL_SOL_MEDIO_GAMMA'])}
        config['PERFIL_SOL_FORTE'] = {'shutter': int(temp_config['PERFIL_SOL_FORTE_SHUTTER']),
                                      'gamma': int(temp_config['PERFIL_SOL_FORTE_GAMMA'])}
        config['CONTADOR_PARA_ESCALAR'] = int(temp_config['CONTADOR_PARA_ESCALAR'])
        config['LIMIAR_ESTOURO_ALERTA_INICIAL'] = float(temp_config['LIMIAR_ESTOURO_ALERTA_INICIAL'])
        config['LIMIAR_BRILHO_MEDIO_SOL_MEDIO'] = int(temp_config['LIMIAR_BRILHO_MEDIO_SOL_MEDIO'])
        config['LIMIAR_GANHO_SOL_MEDIO'] = int(temp_config['LIMIAR_GANHO_SOL_MEDIO'])
        config['LIMIAR_BRILHO_MEDIO_SOL_FORTE'] = int(temp_config['LIMIAR_BRILHO_MEDIO_SOL_FORTE'])
        config['LIMIAR_GANHO_SOL_FORTE'] = int(temp_config['LIMIAR_GANHO_SOL_FORTE'])
        config['LIMIAR_ESTOURO_ESCALADA_MEDIA'] = float(temp_config['LIMIAR_ESTOURO_ESCALADA_MEDIA'])
        config['CONTADOR_PARA_DESESCALAR'] = int(temp_config['CONTADOR_PARA_DESESCALAR'])
        config['LIMIAR_ESTOURO_OK'] = float(temp_config['LIMIAR_ESTOURO_OK'])
        config['LIMIAR_BRILHO_MEDIO_PARA_NORMAL'] = int(temp_config['LIMIAR_BRILHO_MEDIO_PARA_NORMAL'])
        config['LIMIAR_BRILHO_MEDIO_PARA_MEDIO'] = int(temp_config['LIMIAR_BRILHO_MEDIO_PARA_MEDIO'])
        config['NOME_PARAM_GANHO_ATUAL'] = temp_config['NOME_PARAM_GANHO_ATUAL']
        config['LIMIAR_BRILHO_PIXEL_ESTOURADO'] = int(temp_config['LIMIAR_BRILHO_PIXEL_ESTOURADO'])
        config['SALVAR_IMAGEM_NO_ALERTA'] = temp_config['SALVAR_IMAGEM_NO_ALERTA'].lower() == 'true'
        config['DIRETORIO_IMAGENS_ALERTA'] = temp_config['DIRETORIO_IMAGENS_ALERTA']
        config['SALVAR_IMAGEM_CROPADA_DEBUG'] = temp_config['SALVAR_IMAGEM_CROPADA_DEBUG'].lower() == 'true'
        config['DIRETORIO_IMAGENS_CROPADAS'] = temp_config['DIRETORIO_IMAGENS_CROPADAS']
        config['CLP_PORT'] = 502
        config['ENDERECO_BARREIRA_ENTRADA'] = 216

        print("--- Configurações carregadas do arquivo .txt ---")
        for key, value in config.items(): print(f"  {key}: {value}")
        print("---------------------------------------")
        log_message("Configurações carregadas.", config['NOME_PISTA'])
        return True
    except Exception as e:
        print(f"[ERRO FATAL] Falha ao ler ou processar o arquivo de configuração: {e}")
        log_message(f"[ERRO FATAL] Falha ao ler ou processar o arquivo de configuração: {e}")
        return False


# ### FUNÇÃO CORRIGIDA PARA USAR CAMINHOS ABSOLUTOS ###
def analisar_qualidade_imagem_camera(ip_camera):
    url_last_frame = f"http://{ip_camera}/api/lastframe.cgi"
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] --- Análise de Imagem ---")
    log_message(f"[ANÁLISE] Buscando último frame.", config['NOME_PISTA'])

    # Constrói os caminhos absolutos uma vez
    caminho_base = encontrar_caminho_recurso('')
    diretorio_imagens_path = os.path.join(caminho_base,
                                          config.get('DIRETORIO_IMAGENS_ALERTA', DIRETORIO_IMAGENS_ALERTA_BASE))
    diretorio_crop_path = os.path.join(caminho_base,
                                       config.get('DIRETORIO_IMAGENS_CROPADAS', DIRETORIO_IMAGENS_CROPADAS_BASE))

    try:
        response = requests.get(url_last_frame, timeout=5)
        response.raise_for_status()
        image_data = response.content
        with Image.open(io.BytesIO(image_data)) as img:
            img_cropada = img.crop(config['COORDENADAS_CROP'])
            if config.get('SALVAR_IMAGEM_CROPADA_DEBUG', False):
                try:
                    os.makedirs(diretorio_crop_path, exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nome_arquivo = f"crop_{ts}.jpg"
                    caminho_arquivo = os.path.join(diretorio_crop_path, nome_arquivo)
                    img_cropada.save(caminho_arquivo)
                except Exception as e:
                    log_message(f"[ERRO DEBUG] {e}", config.get('NOME_PISTA'))

            img_cinza = ImageOps.grayscale(img_cropada)
            brilho_medio = ImageStat.Stat(img_cinza).mean[0]
            pixels_estourados = sum(1 for p in img_cinza.getdata() if p > config['LIMIAR_BRILHO_PIXEL_ESTOURADO'])
            percentual_estourado = (pixels_estourados / (img_cropada.width * img_cropada.height)) * 100
            diagnostico = f"Estouro: {percentual_estourado:.2f}%, Brilho Médio (na ROI): {brilho_medio:.2f}"
            print(f"[DIAGNÓSTICO] {diagnostico}")
            log_message(f"[DIAGNÓSTICO] {diagnostico}", config['NOME_PISTA'])

            if percentual_estourado > config['LIMIAR_ESTOURO_ALERTA_INICIAL'] and config.get('SALVAR_IMAGEM_NO_ALERTA',
                                                                                             False):
                try:
                    os.makedirs(diretorio_imagens_path, exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nome_arquivo = f"alerta_{ts}_{percentual_estourado:.2f}p.jpg"
                    caminho_arquivo = os.path.join(diretorio_imagens_path, nome_arquivo)
                    with open(caminho_arquivo, "wb") as f:
                        f.write(image_data)
                except Exception as e:
                    log_message(f"[ERRO DEBUG] {e}", config.get('NOME_PISTA'))

            return {"estouro": percentual_estourado, "brilho_medio": brilho_medio}
    except Exception as e:
        log_message(f"[ERRO ANÁLISE] {e}", config['NOME_PISTA'])
        return None


# (O resto do script: obter_ganho_atual, ajustar_camera e main permanecem IDÊNTICOS à sua versão)
def obter_ganho_atual():
    ip = config['CAMERA_IP']
    url_ganho = f"http://{ip}/api/config.cgi?{config['NOME_PARAM_GANHO_ATUAL']}"
    print(f"[INFO GANHO] Buscando ganho atual...")
    log_message(f"[INFO GANHO] Buscando ganho atual...", config.get('NOME_PISTA'))
    try:
        response = requests.get(url_ganho, timeout=5)
        if response.status_code == 200:
            match = re.search(r'(\d+)', response.text.strip())
            if match:
                ganho = int(match.group(1))
                print(f"[INFO GANHO] Resposta: '{response.text.strip()}'. Ganho extraído: {ganho}")
                log_message(f"[INFO GANHO] Resposta: '{response.text.strip()}'. Ganho extraído: {ganho}",
                            config.get('NOME_PISTA'))
                return ganho
        return None
    except Exception:
        return None


def ajustar_camera(perfil):
    ip = config['CAMERA_IP']
    perfil_map = {'normal': config['PERFIL_NORMAL'], 'sol_medio': config['PERFIL_SOL_MEDIO'],
                  'sol_forte': config['PERFIL_SOL_FORTE']}
    if perfil not in perfil_map: return False
    config_perfil = perfil_map[perfil]
    valor_shutter, valor_gamma = config_perfil['shutter'], config_perfil['gamma']
    print(f"Ajustando câmera para o perfil '{perfil.upper()}' (Shutter: {valor_shutter}, Gamma: {valor_gamma})...")
    log_message(f"[AÇÃO] Ajustando para perfil '{perfil.upper()}'", config['NOME_PISTA'])
    comando_string = f"ShutterMaximo={valor_shutter}&ValorGammaDif={valor_gamma}"
    url_comando = f"http://{ip}/api/config.cgi?{comando_string}"
    try:
        response = requests.get(url_comando, timeout=10)
        return response.status_code == 200
    except Exception:
        return False


def main():
    caminho_config = encontrar_caminho_recurso(NOME_ARQUIVO_CONFIG)
    if not carregar_configuracoes(caminho_config):
        time.sleep(10);
        return

    nome_pista = config['NOME_PISTA']
    log_message("--- SESSÃO DE MONITORAMENTO INICIADA ---", nome_pista)
    estado_atual, contador_para_escalar, contador_para_desescalar = "normal", 0, 0
    ajustar_camera('normal')
    client = ModbusTcpClient(config['CLP_IP'], port=config['CLP_PORT'])
    while not client.connect(): time.sleep(10)
    log_message("Conexão com CLP estabelecida.", nome_pista)
    prev_barreira_status = False
    print("Monitorando a barreira ótica...")
    try:
        while True:
            if datetime.now().time() > config['HORA_ENCERRAMENTO']:
                print(f"Horário de encerramento atingido.")
                log_message("Horário de encerramento atingido.", nome_pista)
                break
            try:
                rr = client.read_coils(address=config['ENDERECO_BARREIRA_ENTRADA'], count=1)
                if rr.isError():
                    rr = client.read_discrete_inputs(address=config['ENDERECO_BARREIRA_ENTRADA'], count=1)
                    if rr.isError(): raise Exception("Erro Modbus.")
                current_barreira_status = rr.bits[0]
                if current_barreira_status and not prev_barreira_status:
                    log_message("[GATILHO]", nome_pista)
                    metricas = analisar_qualidade_imagem_camera(config['CAMERA_IP'])
                    ganho_atual = obter_ganho_atual()
                    if metricas is None or ganho_atual is None: continue
                    estouro = metricas["estouro"];
                    brilho_medio = metricas["brilho_medio"]
                    if estado_atual == 'normal':
                        cond_estouro = estouro > config['LIMIAR_ESTOURO_ALERTA_INICIAL']
                        cond_brilho_forte = brilho_medio > config['LIMIAR_BRILHO_MEDIO_SOL_FORTE']
                        cond_brilho_medio = brilho_medio > config['LIMIAR_BRILHO_MEDIO_SOL_MEDIO']
                        cond_ganho_forte = ganho_atual < config['LIMIAR_GANHO_SOL_FORTE']
                        cond_ganho_medio = ganho_atual < config['LIMIAR_GANHO_SOL_MEDIO']
                        if (cond_estouro and cond_brilho_forte and cond_ganho_forte) or \
                                (cond_estouro and cond_brilho_medio and cond_ganho_medio):
                            contador_para_escalar += 1
                            log_message(
                                f"Alerta VÁLIDO (E:{estouro:.1f}, B:{brilho_medio:.1f}, G:{ganho_atual}). Contagem: {contador_para_escalar}",
                                nome_pista)
                            if contador_para_escalar >= config['CONTADOR_PARA_ESCALAR']:
                                novo_estado = 'sol_forte' if cond_brilho_forte else 'sol_medio'
                                if ajustar_camera(novo_estado): estado_atual = novo_estado
                                contador_para_escalar, contador_para_desescalar = 0, 0
                        else:
                            contador_para_escalar = 0
                    elif estado_atual == 'sol_medio':
                        if estouro > config['LIMIAR_ESTOURO_ESCALADA_MEDIA']:
                            contador_para_escalar += 1
                            if contador_para_escalar >= config['CONTADOR_PARA_ESCALAR']:
                                if ajustar_camera('sol_forte'): estado_atual = 'sol_forte'
                                contador_para_escalar, contador_para_desescalar = 0, 0
                        else:
                            contador_para_escalar = 0
                        if estouro < config['LIMIAR_ESTOURO_OK'] and brilho_medio < config[
                            'LIMIAR_BRILHO_MEDIO_PARA_NORMAL']:
                            contador_para_desescalar += 1
                            if contador_para_desescalar >= config['CONTADOR_PARA_DESESCALAR']:
                                if ajustar_camera('normal'): estado_atual = 'normal'
                                contador_para_escalar, contador_para_desescalar = 0, 0
                        else:
                            contador_para_desescalar = 0
                    elif estado_atual == 'sol_forte':
                        cond_retorno_normal = estouro < config['LIMIAR_ESTOURO_OK'] and brilho_medio < config[
                            'LIMIAR_BRILHO_MEDIO_PARA_NORMAL']
                        cond_retorno_medio = estouro < config['LIMIAR_ESTOURO_OK'] and brilho_medio < config[
                            'LIMIAR_BRILHO_MEDIO_PARA_MEDIO']
                        if cond_retorno_normal or cond_retorno_medio:
                            contador_para_desescalar += 1
                            if contador_para_desescalar >= config['CONTADOR_PARA_DESESCALAR']:
                                novo_estado = 'normal' if cond_retorno_normal else 'sol_medio'
                                if ajustar_camera(novo_estado): estado_atual = novo_estado
                                contador_para_escalar, contador_para_desescalar = 0, 0
                        else:
                            contador_para_desescalar = 0
                    log_message(
                        f"[STATUS] Contadores (E/DE): {contador_para_escalar}/{contador_para_desescalar}. Estado: {estado_atual.upper()}",
                        nome_pista)
                    print(
                        f"[STATUS] Contadores (E/DE): {contador_para_escalar}/{contador_para_desescalar}. Estado: {estado_atual.upper()}")
                prev_barreira_status = current_barreira_status
            except Exception as e:
                log_message(f"[ERRO CLP] {e}", nome_pista)
                client.close();
                time.sleep(10)
                while not client.connect(): time.sleep(10)
                log_message("Reconexão com CLP estabelecida.", nome_pista)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nScript interrompido pelo usuário.")
    finally:
        ajustar_camera('normal')
        log_message("Script encerrado. Câmera configurada para o modo 'normal'.", nome_pista)
        if client.is_socket_open(): client.close()
        log_message("--- SESSÃO DE MONITORAMENTO FINALIZADA ---", nome_pista)


if __name__ == "__main__":
    main()