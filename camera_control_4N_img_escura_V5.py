# --- Importações Essenciais ---
import time, os, sys, re
from datetime import datetime, time as time_obj
import requests
from PIL import Image, ImageOps, ImageStat
import io
from pymodbus.client import ModbusTcpClient

# --- Constantes e Configurações Globais ---
NOME_ARQUIVO_CONFIG = "config_pista_img_escura_4N.txt"
# ### ALTERADO ### Agora são apenas os nomes base das pastas
LOG_DIRECTORY_BASE = "logs_qualidade_camera"
DIRETORIO_IMAGENS_ALERTA_BASE = "imagens_escuras_alerta"
DIRETORIO_IMAGENS_CROPADAS_BASE = "imagens_cropadas_debug"
config = {}

# (O resto das constantes permanece o mesmo)
CONTADOR_PARA_ATIVAR_BAIXA_LUZ = 4
CONTADOR_PARA_DESATIVAR_BAIXA_LUZ = 8
SALVAR_IMAGEM_NO_ALERTA = True  # Estes serão sobrescritos pelo .txt se existirem
SALVAR_IMAGEM_CROPADA_DEBUG = True


# --- Funções ---

def encontrar_caminho_recurso(caminho_relativo):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
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
        # Imprime o erro no console, já que não pode escrever no log
        print(f"ERRO CRÍTICO no log: {e}")


# ### FUNÇÃO ATUALIZADA PARA LER FLAGS DE DEBUG DO TXT ###
def carregar_configuracoes(caminho_arquivo_txt):
    try:
        temp_config = {}
        with open(caminho_arquivo_txt, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    chave, valor = line.split('=', 1)
                    temp_config[chave.strip()] = valor.strip()

        # ... (código de leitura dos perfis e limiares)
        config['NOME_PISTA'] = temp_config['NOME_PISTA']
        config['CAMERA_IP'] = temp_config['CAMERA_IP']
        config['CLP_IP'] = temp_config['CLP_IP']
        config['COORDENADAS_CROP'] = (int(temp_config['CROP_X1']), int(temp_config['CROP_Y1']),
                                      int(temp_config['CROP_X2']), int(temp_config['CROP_Y2']))
        config['PERFIL_NORMAL'] = {'saturacao': int(temp_config['PERFIL_NORMAL_SATURACAO']),
                                   'gamma': int(temp_config['PERFIL_NORMAL_GAMMA']),
                                   'saturacao_diurno': int(temp_config['PERFIL_NORMAL_SATURACAODIURNO'])}
        config['PERFIL_BAIXA_LUZ'] = {'saturacao': int(temp_config['PERFIL_BAIXA_LUZ_SATURACAO']),
                                      'gamma': int(temp_config['PERFIL_BAIXA_LUZ_GAMMA']),
                                      'saturacao_diurno': int(temp_config['PERFIL_BAIXA_LUZ_SATURACAODIURNO'])}
        config['LIMIAR_BRILHO_ESCURECEU'] = int(temp_config['LIMIAR_BRILHO_ESCURECEU'])
        config['LIMIAR_BRILHO_CLAREOU'] = int(temp_config['LIMIAR_BRILHO_CLAREOU'])
        horario_str = temp_config['HORA_ENCERRAMENTO']
        h, m = map(int, horario_str.split(':'))
        config['HORA_ENCERRAMENTO'] = time_obj(h, m)
        config['CLP_PORT'] = 502
        config['ENDERECO_BARREIRA_ENTRADA'] = 216

        # Leitura dos flags de debug do .txt
        config['SALVAR_IMAGEM_NO_ALERTA'] = temp_config.get('SALVAR_IMAGEM_NO_ALERTA', 'True').lower() == 'true'
        config['SALVAR_IMAGEM_CROPADA_DEBUG'] = temp_config.get('SALVAR_IMAGEM_CROPADA_DEBUG', 'True').lower() == 'true'

        if config['LIMIAR_BRILHO_ESCURECEU'] >= config['LIMIAR_BRILHO_CLAREOU']:
            raise ValueError("Erro de Lógica: LIMIAR_BRILHO_ESCURECEU deve ser MENOR que LIMIAR_BRILHO_CLAREOU.")

        print("--- Configurações carregadas do .txt ---")
        for key, value in config.items(): print(f"  {key}: {value}")
        print("---------------------------------------")
        log_message("Configurações carregadas.", config['NOME_PISTA'])
        return True
    except Exception as e:
        print(f"[ERRO FATAL] Falha ao ler o arquivo de configuração: {e}")
        log_message(f"[ERRO FATAL] Falha ao ler o arquivo de configuração: {e}")
        return False


def ajustar_camera(perfil):
    # (código sem alterações)
    ip = config['CAMERA_IP']
    perfil_map = {'normal': config['PERFIL_NORMAL'], 'baixa_luz': config['PERFIL_BAIXA_LUZ']}
    if perfil not in perfil_map: return False
    config_perfil = perfil_map[perfil]
    valor_saturacao = config_perfil.get('saturacao')
    valor_gamma = config_perfil.get('gamma')
    valor_saturacao_diurno = config_perfil.get('saturacao_diurno')
    param_saturacao = "Saturacao"
    param_gamma = "ValorGammaDif"
    param_saturacao_diurno = "SaturacaoDiurno"
    print(
        f"Ajustando câmera para o perfil '{perfil.upper()}' (Saturacao: {valor_saturacao}, Gamma: {valor_gamma}, SaturacaoDiurno: {valor_saturacao_diurno})...")
    log_message(f"[AÇÃO] Ajustando para perfil '{perfil.upper()}'", config.get('NOME_PISTA'))
    comando_string = f"{param_saturacao}={valor_saturacao}&{param_gamma}={valor_gamma}&{param_saturacao_diurno}={valor_saturacao_diurno}"
    url_comando = f"http://{ip}/api/config.cgi?{comando_string}"
    try:
        response = requests.get(url_comando, timeout=10)
        return response.status_code == 200
    except Exception:
        return False


# ### FUNÇÃO CORRIGIDA PARA USAR CAMINHOS ABSOLUTOS ###
def analisar_qualidade_imagem_camera(ip_camera):
    url_last_frame = f"http://{ip_camera}/api/lastframe.cgi"
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] --- Análise de Imagem ---")
    log_message(f"[ANÁLISE] Buscando último frame.", config.get('NOME_PISTA'))

    # Constrói os caminhos absolutos para as pastas de imagem
    caminho_base = encontrar_caminho_recurso('')
    diretorio_imagens_path = os.path.join(caminho_base, DIRETORIO_IMAGENS_ALERTA_BASE)
    diretorio_crop_path = os.path.join(caminho_base, DIRETORIO_IMAGENS_CROPADAS_BASE)

    try:
        response = requests.get(url_last_frame, timeout=5)
        response.raise_for_status()
        image_data = response.content
        with Image.open(io.BytesIO(image_data)) as img:
            img_cropada = img.crop(config['COORDENADAS_CROP'])

            if config.get('SALVAR_IMAGEM_CROPADA_DEBUG'):
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
            diagnostico = f"Brilho Médio (na ROI): {brilho_medio:.2f}"
            print(f"[DIAGNÓSTICO] {diagnostico}")
            log_message(f"[DIAGNÓSTICO] {diagnostico}", config.get('NOME_PISTA'))

            if brilho_medio < config['LIMIAR_BRILHO_ESCURECEU'] and config.get('SALVAR_IMAGEM_NO_ALERTA'):
                try:
                    os.makedirs(diretorio_imagens_path, exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nome_arquivo = f"alerta_escuro_{ts}_brilho_{brilho_medio:.0f}.jpg"
                    caminho_arquivo = os.path.join(diretorio_imagens_path, nome_arquivo)
                    with open(caminho_arquivo, "wb") as f:
                        f.write(image_data)
                except Exception:
                    pass

            return {"brilho_medio": brilho_medio}
    except Exception as e:
        log_message(f"[ERRO ANÁLISE] {e}", config.get('NOME_PISTA'))
        return None


def main():
    # (código do main sem alterações)
    caminho_config_txt = encontrar_caminho_recurso(NOME_ARQUIVO_CONFIG)
    if not carregar_configuracoes(caminho_config_txt):
        time.sleep(10);
        return

    nome_pista = config.get('NOME_PISTA')
    log_message("--- SESSÃO DE MONITORAMENTO (MODO IMAGEM ESCURA) INICIADA ---", nome_pista)
    estado_atual, contador_baixa_luz, contador_luz_normal = "normal", 0, 0
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
                    if metricas is None: continue
                    brilho_medio = metricas["brilho_medio"]
                    if brilho_medio < config['LIMIAR_BRILHO_ESCURECEU']:
                        contador_baixa_luz += 1
                        contador_luz_normal = 0
                    elif brilho_medio > config['LIMIAR_BRILHO_CLAREOU']:
                        contador_luz_normal += 1
                        contador_baixa_luz = 0
                    else:
                        contador_baixa_luz, contador_luz_normal = 0, 0
                        log_message(f"Leitura em 'zona limbo' (Brilho {brilho_medio:.2f}).", nome_pista)
                    if estado_atual == 'normal' and contador_baixa_luz >= CONTADOR_PARA_ATIVAR_BAIXA_LUZ:
                        log_message("Ativando perfil de BAIXA LUZ.", nome_pista)
                        if ajustar_camera('baixa_luz'): estado_atual = 'baixa_luz'
                        contador_baixa_luz, contador_luz_normal = 0, 0
                    elif estado_atual == 'baixa_luz' and contador_luz_normal >= CONTADOR_PARA_DESATIVAR_BAIXA_LUZ:
                        log_message("Retornando ao perfil NORMAL.", nome_pista)
                        if ajustar_camera('normal'): estado_atual = 'normal'
                        contador_baixa_luz, contador_luz_normal = 0, 0
                    print(
                        f"[STATUS] Contadores (BaixaLuz/Normal): {contador_baixa_luz}/{contador_luz_normal}. Estado: {estado_atual.upper()}")
                    log_message(
                        f"[STATUS] Contadores (BL/N): {contador_baixa_luz}/{contador_luz_normal}. Estado: {estado_atual.upper()}",
                        nome_pista)
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
        log_message("Script encerrado.", nome_pista)
        if client.is_socket_open(): client.close()
        log_message("--- SESSÃO FINALIZADA ---", nome_pista)


if __name__ == "__main__":
    main()