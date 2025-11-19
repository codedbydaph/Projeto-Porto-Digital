import pyaudio
import websocket
import json
import threading
import time
import sys
import shutil
import unicodedata
import re
from urllib.parse import urlencode
from datetime import datetime
from difflib import SequenceMatcher

# --- Configurações ---
YOUR_API_KEY = "***"  # Mudar para a sua chave do assembly

CONNECTION_PARAMS = {
    "sample_rate": 16000,
    "format_turns": True,
    "language": "multi",
}
API_ENDPOINT_BASE_URL = "wss://streaming.assemblyai.com/v3/ws"
API_ENDPOINT = f"{API_ENDPOINT_BASE_URL}?{urlencode(CONNECTION_PARAMS)}"

# Configurações de audio
FRAMES_PER_BUFFER = 800
SAMPLE_RATE = CONNECTION_PARAMS["sample_rate"]
CHANNELS = 1
FORMAT = pyaudio.paInt16

# Variaveis globais para a transmissão de audio e o websocket
audio = None
stream = None
ws_app = None
audio_thread = None
stop_event = threading.Event()

# --- utilitários de terminal ---
def get_term_width():
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 70

def clear_partial_line():
    """Limpa a linha atual do terminal (útil antes de imprimir final)."""
    width = get_term_width()
    sys.stdout.write("\r" + " " * width + "\r")
    sys.stdout.flush()

def truncate_to_width(text, width):
    if len(text) > width:
        return text[:width - 3] + "..."
    return text

# --- normalize / fuzzy helpers ---
def normalize(s: str) -> str:
    """Lowercase, remove acentos, pontuação extra e múltiplos espaços."""
    if s is None:
        return ""
    s = s.lower().strip()
    # remove accents
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    # remove punctuation except spaces and alphanumerics
    s = re.sub(r"[^0-9a-z\s]", "", s)
    # collapse spaces
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def similarity(a: str, b: str) -> float:
    """Return similarity ratio between two strings (0..1)."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

# --- Controle do roteiro ---
roteiro_linhas = []
current_line = 0

def carregar_roteiro():
    global roteiro_linhas
    with open("roteiro.txt", "r", encoding="utf-8") as f:
        roteiro_linhas = [linha.strip() for linha in f.readlines() if linha.strip()]

def mostrar_linha_atual():
    global current_line, roteiro_linhas
    if current_line < len(roteiro_linhas):
        print(f"\n➡️ Próxima linha: {roteiro_linhas[current_line]}")

# --- estado da exibição de parciais ---
final_text = ""            # acumula transcrições finais (opcional)
last_partial_length = 0    # comprimento do último parcial mostrado (uso para limpar)
last_shown_partial = ""    # texto do parcial que está sendo mostrado (não o evento 'transcript')

prefix = "🟡 Parcial: "

# --- lógica de decisão de match ---
def is_partial_match(partial: str, expected: str) -> bool:
    """
    Decide se o parcial indica que estamos falando o começo da linha esperada.
    Critérios:
      - normalized expected startswith normalized partial (firme)
      - OR normalized partial is a substring of expected (menos firme)
      - OR similarity >= 0.55 (tolerância)
    """
    if not partial:
        return False
    np = normalize(partial)
    ne = normalize(expected)
    if not np or not ne:
        return False
    if ne.startswith(np):
        return True
    if np in ne:
        return True
    if similarity(np, ne) >= 0.55:
        return True
    return False

def is_final_match(final_text_candidate: str, expected: str) -> bool:
    """
    Decide se o texto final corresponde à linha esperada.
    Critérios:
      - equality after normalize OR similarity >= 0.86
    """
    nf = normalize(final_text_candidate)
    ne = normalize(expected)
    if not nf or not ne:
        return False
    if nf == ne:
        return True
    if similarity(nf, ne) >= 0.86:
        return True
    return False

# --- Eventos do Websocket ---
def on_open(ws):
    print("conexão com WebSocket aberta.")
    print(f"Conectado a: {API_ENDPOINT}")

    def stream_audio():
        global stream
        while not stop_event.is_set():
            try:
                audio_data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                ws.send(audio_data, websocket.ABNF.OPCODE_BINARY)
            except Exception as e:
                print(f"Erro ao transmitir o audio: {e}")
                break
        print("Transmissão de audio interrompida.")

    global audio_thread
    audio_thread = threading.Thread(target=stream_audio)
    audio_thread.daemon = True
    audio_thread.start()

def on_message(ws, message):
    """
    Handler principal para mensagens do AssemblyAI.
    Trabalha com o roteiro: avança apenas quando a linha for confirmada.
    """
    global final_text, last_partial_length, last_shown_partial
    global current_line, roteiro_linhas

    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        return

    msg_type = data.get("type")

    if msg_type == "Begin":
        session_id = data.get('id')
        expires_at = data.get('expires_at')
        print(f"\nComeço da seção: ID={session_id}, Expira as={datetime.fromtimestamp(expires_at)}")
        print("Fale no microfone.")
        return

    if msg_type == "Termination":
        audio_duration = data.get('audio_duration_seconds', 0)
        session_duration = data.get('session_duration_seconds', 0)
        print(f"\nSeção encerrada: Duração de audio={audio_duration}s, Duração da seção={session_duration}s")
        return

    if msg_type != "Turn":
        return

    transcript = data.get('transcript', '') or ""
    formatted = data.get('turn_is_formatted', False)
    
    # há linha atual a ser lida
    expected = roteiro_linhas[current_line]

    # --- processamento de final (texto confirmado) ---
    if formatted:
        # limpa parcial visível e imprime o final
        clear_partial_line()

        # Mostra final
        print(f"\n🟢 Final: {transcript}")

        # tenta casar com a linha atual; se casar, avança.
        if is_final_match(transcript, expected):
            print(f"✔️ Linha reconhecida: {expected}\n")
            current_line += 1
            final_text += transcript + " "
            if current_line >= len(roteiro_linhas):
                print("\nRoteiro concluido, finalizando operação")
                stop_event.set()

                if ws_app and ws_app.sock and ws_app.sock.connected:
                    try:
                        terminate_message = {"type": "Terminate"}
                        print(f"Sending termination message: {json.dumps(terminate_message)}")
                        ws_app.send(json.dumps(terminate_message))
                        time.sleep(5)
                    except Exception as e:
                        print(f"Error sending termination message: {e}")
                    if stream and stream.is_active():
                        stream.stop_stream()
                    if stream:
                        stream.close()
                    if audio:
                        audio.terminate()
                    print("Limpeza completa. Saindo.")

            # mostra a próxima linha se houver
            if current_line < len(roteiro_linhas):
                print(f"➡️ Próxima linha: {roteiro_linhas[current_line]}")
            last_shown_partial = ""
            last_partial_length = 0
            return
        else:
            # Se não casou com a linha atual, testar se casa com alguma linha futura (pular)
            for i in range(current_line + 1, len(roteiro_linhas)):
                if is_final_match(transcript, roteiro_linhas[i]):
                    print(f"⚠️ Linha pulada! Indo para: {roteiro_linhas[i]}")
                    current_line = i + 1
                    final_text += transcript + " "
                    if current_line < len(roteiro_linhas):
                        print(f"➡️ Próxima linha: {roteiro_linhas[current_line]}")
                    last_shown_partial = ""
                    last_partial_length = 0
                    return

        # se não casou com nenhuma linha, apenas acumula (ou ignore)
        final_text += transcript + " "
        last_shown_partial = ""
        last_partial_length = 0
        return

    # --- processamento de parcial (texto em tempo real) ---
    # mostramos parcial no prefixo, mas tentamos decidir se já corresponde ao início da linha
    term_width = get_term_width()
    max_len = max(term_width - len(prefix) - 2, 10)
    safe = truncate_to_width(transcript, max_len)

    # Exibe parcial (sempre)
    sys.stdout.write("\r" + prefix + safe + " " * (max(0, last_partial_length - len(safe))))
    sys.stdout.flush()
    last_shown_partial = safe
    last_partial_length = len(safe)

   

def on_error(ws, error):
    print(f"\nWebSocket Erro: {error}")
    stop_event.set()

def on_close(ws, close_status_code, close_msg):
    print(f"\nWebSocket Disconectado: Status={close_status_code}, Msg={close_msg}")
    global stream, audio
    stop_event.set()

    if stream:
        if stream.is_active():
            stream.stop_stream()
        stream.close()
    if audio:
        audio.terminate()
    if audio_thread and audio_thread.is_alive():
        audio_thread.join(timeout=1.0)

# --- Execusão principal ---
def run():
    global audio, stream, ws_app

    # Inicializa PyAudio
    audio = pyaudio.PyAudio()

    carregar_roteiro()
    mostrar_linha_atual()

    # Abre o microfone
    try:
        stream = audio.open(
            input=True,
            frames_per_buffer=FRAMES_PER_BUFFER,
            channels=CHANNELS,
            format=FORMAT,
            rate=SAMPLE_RATE,
        )
        print("Microfone aberto com sucesso.")
        print("Precione Ctrl+C para parar.")
    except Exception as e:
        print(f"Erro ao abrir a transmissão: {e}")
        if audio:
            audio.terminate()
        return

    ws_app = websocket.WebSocketApp(
        API_ENDPOINT,
        header={"Authorization": YOUR_API_KEY},
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    ws_thread = threading.Thread(target=ws_app.run_forever)
    ws_thread.daemon = True
    ws_thread.start()

    try:
        while ws_thread.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nCtrl+C recebido. Parando...")
        stop_event.set()

        if ws_app and ws_app.sock and ws_app.sock.connected:
            try:
                terminate_message = {"type": "Terminate"}
                print(f"Sending termination message: {json.dumps(terminate_message)}")
                ws_app.send(json.dumps(terminate_message))
                time.sleep(5)
            except Exception as e:
                print(f"Error sending termination message: {e}")

        if ws_app:
            ws_app.close()

        ws_thread.join(timeout=2.0)

    except Exception as e:
        print(f"\nUm erro inesperado ocorreu: {e}")
        stop_event.set()
        if ws_app:
            ws_app.close()
        ws_thread.join(timeout=2.0)

    finally:
        if stream and stream.is_active():
            stream.stop_stream()
        if stream:
            stream.close()
        if audio:
            audio.terminate()
        print("Limpeza completa. Saindo.")

if __name__ == "__main__":
    run()
