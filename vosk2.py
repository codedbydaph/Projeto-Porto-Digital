import sys
import queue
import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer

q = queue.Queue()

def callback(indata, frames, time, status):
    """Callback do microfone"""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def main():
    # Configurações
    SAMPLERATE = 16000  # taxa de amostragem padrão
    MODEL_LANG = "pt"   # idioma do modelo (ex: "en-us", "pt", etc.)
    
    print("🔊 Inicializando modelo...")
    model = Model(lang=MODEL_LANG)
    rec = KaldiRecognizer(model, SAMPLERATE)

    # Inicia o stream de áudio
    with sd.RawInputStream(samplerate=SAMPLERATE, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("\n🎤 Fale algo... (Ctrl+C para sair)\n")
        partial_text = ""

        try:
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    # Quando uma frase for concluída
                    result = json.loads(rec.Result())
                    if "text" in result:
                        # Apaga linha anterior e mostra resultado final
                        print("\r" + " " * len(partial_text), end="\r")
                        print("✅ Texto final:", result["text"])
                        partial_text = ""
                else:
                    # Atualiza texto parcial em tempo real
                    partial = json.loads(rec.PartialResult())
                    if "partial" in partial:
                        text = partial["partial"]
                        if text != partial_text:
                            # Sobrescreve linha anterior
                            print("\r" + text + " " * (len(partial_text) - len(text)), end="")
                            sys.stdout.flush()
                            partial_text = text
        except KeyboardInterrupt:
            print("\n🛑 Encerrado pelo usuário.")
            print("Último resultado:", rec.FinalResult())

if __name__ == "__main__":
    main()
