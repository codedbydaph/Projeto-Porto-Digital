import pyaudio
import websocket
import json
import threading
import time
import sys
import shutil
from urllib.parse import urlencode
from datetime import datetime

# --- Configurações ---
YOUR_API_KEY = "81422daf5a8242e887b8eed313e1682d"  # Mudar para a sua chave do assembly

CONNECTION_PARAMS = {
    "sample_rate": 16000,
    "format_turns": True, 
    "language": "multi", # para entender frases sem ser em inglês
}
API_ENDPOINT_BASE_URL = "wss://streaming.assemblyai.com/v3/ws"
API_ENDPOINT = f"{API_ENDPOINT_BASE_URL}?{urlencode(CONNECTION_PARAMS)}"

# Configurações de audio
FRAMES_PER_BUFFER = 800  # quantidade de frames processados por vez
SAMPLE_RATE = CONNECTION_PARAMS["sample_rate"]
CHANNELS = 1
FORMAT = pyaudio.paInt16

# Variaveis globais para a transmissão de audio e o websocket
audio = None
stream = None
ws_app = None
audio_thread = None
stop_event = threading.Event()  # Para sinalizar a parada de captura de audio

# --- Eventos do Websocket ---

def on_open(ws):
    """Chamado quando a conexão com o Websocket é feita."""
    print("conexão com WebSocket aberta.")
    print(f"Conectado a: {API_ENDPOINT}")

    # Começa a enviar o audio em um caminha diferente
    def stream_audio():
        global stream
        while not stop_event.is_set():
            try:
                audio_data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)

                # Envia o conteudo do audio como um codigo binario
                ws.send(audio_data, websocket.ABNF.OPCODE_BINARY)
            except Exception as e:
                print(f"Erro ao transmitir o audio: {e}")
                break
        print("Transmisão de audio interrompida.")

    global audio_thread
    audio_thread = threading.Thread(target=stream_audio)
    audio_thread.daemon = (
        True  # Permite que o caminho princial pare mesmo que esse ainda esteja sendo executado
    )
    audio_thread.start()

def get_term_width():
    """Retorna a largura atual do terminal"""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 70

def truncate_to_width(text, width):
    """Trunca o texto para caber na largura do terminal"""
    if len(text) > width:
        return text[:width - 3] + " "
    return text

def on_message(ws, message):
    """Função que mostra o texto parcial e formatado, quando disponivel"""
    final_text = ""          # acumula transcrições finais
    last_partial_length = 0  # comprimento do último parcial (para limpeza da linha)
    prefix = "🟡 Parcial: "

    try:
        data = json.loads(message)
        msg_type = data.get('type')

        if msg_type == "Begin":
            session_id = data.get('id')
            expires_at = data.get('expires_at')
            print(f"\nComeço da seção: ID={session_id}, Expira as={datetime.fromtimestamp(expires_at)}")
            print("Fale no microfone.")
        elif msg_type == "Turn":
            transcript = data.get('transcript', '') or ''
            formatted = data.get('turn_is_formatted', False)

            term_width = get_term_width()
            max_len = term_width - len(prefix)  # espaço restante para o parcial
            
            if formatted:
                term_width = get_term_width()
                lines_to_clear = (last_partial_length // term_width) + 1

                for _ in range(lines_to_clear):
                    sys.stdout.write('\r' + ' ' * term_width + '\r')
                sys.stdout.flush()

                print(transcript)
                final_text += transcript + " "
                last_partial_length = 0
            else:
                # Garante que o parcial não ultrapasse a largura do terminal
                safe_transcript = truncate_to_width(transcript, max_len)
                indice_safe = len(safe_transcript)
                max_indice = indice_safe + max_len
                # Limpa a linha do parcial anterior e imprime o novo
                sys.stdout.write("\r" + " " * (len(prefix) + last_partial_length) + "\r")
                sys.stdout.write(prefix + safe_transcript)
                last_partial_length = len(safe_transcript)

                # Verifica se tem mais transcrição além da linha para exibi-la corretamente
                if len(transcript) > len(safe_transcript):
                    rest_transcript = transcript[indice_safe:max_indice]
                    sys.stdout.write("\r" + " " * (len(prefix) + last_partial_length) + "\r")
                    sys.stdout.write(prefix + rest_transcript)
                    last_partial_length = len(rest_transcript)
                sys.stdout.flush()
                
        elif msg_type == "Termination":
            audio_duration = data.get('audio_duration_seconds', 0)
            session_duration = data.get('session_duration_seconds', 0)
            print(f"\nSeção encerrada: Duração de audio={audio_duration}s, Duração da seção={session_duration}s")
    except json.JSONDecodeError as e:
        print(f"Error decoding message: {e}")
    except Exception as e:
        print(f"Error handling message: {e}")

def on_error(ws, error):
    """Chamado quando ocorre um erro com o Websocket."""
    print(f"\nWebSocket Erro: {error}")
    stop_event.set()


def on_close(ws, close_status_code, close_msg):
    """Chamado quando a conexão com o Websocket é fechada"""
    print(f"\nWebSocket Disconectado: Status={close_status_code}, Msg={close_msg}")

    # Garante que o audio seja liberado
    global stream, audio
    stop_event.set()  # Sinaliza a finalização da captura de audio caso ainda esteja ocorrendo

    if stream:
        if stream.is_active():
            stream.stop_stream()
        stream.close()
        stream = None
    if audio:
        audio.terminate()
        audio = None
    if audio_thread and audio_thread.is_alive():
        audio_thread.join(timeout=1.0)

# --- Execusão principal ---
def run():
    global audio, stream, ws_app

    # Inicializa PyAudio
    audio = pyaudio.PyAudio()

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

    # Cria WebSocketApp
    ws_app = websocket.WebSocketApp(
        API_ENDPOINT,
        header={"Authorization": YOUR_API_KEY},
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    # Roda WebSocketApp em uma caminho diferente permitindo que o caminho principal receba interrupção do teclado
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

        # Fecha a conexão com o WebSocket
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
