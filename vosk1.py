import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# Caminho do modelo
MODEL_PATH = "model-br"

# Inicializa o modelo e o reconhecedor
print("🔄 Carregando modelo...")
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)

# Fila para comunicação entre o callback e o loop principal
audio_queue = queue.Queue()

def callback(indata, frames, time, status):
    """Função chamada automaticamente a cada novo bloco de áudio."""
    if status:
        print(f"[Aviso] {status}", flush=True)
    # Adiciona os dados de áudio na fila
    audio_queue.put(bytes(indata))

def main():
    print("🎤 Reconhecimento iniciado! Fale algo (Ctrl+C para parar)\n")

    # Cria o stream de entrada do microfone
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback, latency='low'):
        while True:
            data = audio_queue.get()  # aguarda áudio do callback
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                if text:
                    print(f"Texto final: {text}")
                    with open("transcricao.txt", "a", encoding="utf-8") as f:
                        f.write(text + "\n")
            else:
                partial = json.loads(recognizer.PartialResult())
                partial_text = partial.get("partial", "")
                if partial_text:
                    print(f"Transcrição parcial: {partial_text}", end="\r")

try:
    main()
except KeyboardInterrupt:
    print("\nReconhecimento encerrado pelo usuário.")

