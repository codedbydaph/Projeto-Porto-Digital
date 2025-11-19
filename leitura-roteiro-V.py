import sys
import queue
import sounddevice as sd
import json
import unicodedata
import difflib
from vosk import Model, KaldiRecognizer

# -------------------------------
#  Funções auxiliares
# -------------------------------

def normalize(text):
    """Remove acentos e coloca em lowercase para comparação justa."""
    if not text:
        return ""
    text = text.lower()
    text = ''.join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    return text.strip()

def match_route_line(spoken, script_lines, current_line):
    """
    Compara a fala apenas com as linhas do roteiro ainda não ditas.
    Retorna o índice da linha correspondente ou None.
    """
    spoken_n = normalize(spoken)

    best_index = None
    best_score = 0.0

    # Só compara com as linhas ainda não faladas
    for i in range(current_line, len(script_lines)):
        line_n = normalize(script_lines[i])

        score = difflib.SequenceMatcher(None, spoken_n, line_n).ratio()

        if score > best_score:
            best_score = score
            best_index = i

    # Exige um mínimo de similaridade
    if best_score >= 0.60:
        return best_index

    return None



# -------------------------------
#  Callback do microfone
# -------------------------------

q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))


# -------------------------------
#  Programa Principal
# -------------------------------

def main():
    SAMPLERATE = 16000
    MODEL_LANG = "pt"

    # -------------------
    # LÊ O ROTEIRO DO ARQUIVO
    # -------------------
    ROTEIRO_ARQUIVO = "roteiro.txt"

    try:
        with open(ROTEIRO_ARQUIVO, "r", encoding="utf-8") as f:
            script = [linha.strip() for linha in f.readlines() if linha.strip()]
    except FileNotFoundError:
        print(f"\nERRO: Arquivo '{ROTEIRO_ARQUIVO}' não encontrado.\n")
        return

    if not script:
        print("\nERRO: O arquivo de roteiro está vazio\n")
        return

    current_line = 0

    print("Carregando modelo...")
    model = Model(lang=MODEL_LANG)
    rec = KaldiRecognizer(model, SAMPLERATE)

    # Mostra a primeira linha do roteiro
    print("\nROTEIRO INICIADO")
    print("➡️ Linha atual:", script[current_line], "\n")

    with sd.RawInputStream(samplerate=SAMPLERATE, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):

        print("Fale para sincronizar com o roteiro... (Ctrl+C para sair)\n")

        partial_text = ""

        try:
            while True:
                data = q.get()

                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    spoken = result.get("text", "")

                    # Limpa linha parcial exibida
                    print("\r" + " " * len(partial_text), end="\r")

                    if spoken:
                        print(f"Reconhecido: {spoken}")

                        matched_index = match_route_line(spoken, script, current_line)

                        if matched_index is not None:
                            # Avança para a linha correspondente
                            current_line = matched_index
                            print("\nLinha reconhecida!")

                            if current_line + 1 < len(script):
                                current_line += 1
                                print("👉 Próxima Linha: ", script[current_line], "\n")
                            else:
                                print("Roteiro finalizado!\n")
                                sys.exit()

                    partial_text = ""

                else:
                    # Mostra texto parcial em uma única linha
                    partial = json.loads(rec.PartialResult())
                    text = partial.get("partial", "")

                    if text != partial_text:
                        print("\r" + text + " " * (len(partial_text) - len(text)), end="")
                        sys.stdout.flush()
                        partial_text = text

        except KeyboardInterrupt:
            print("\n Encerrado pelo usuário.")


if __name__ == "__main__":
    main()
