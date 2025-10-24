import speech_recognition as sr
import time
import os

CONFIG = {
    "language": "pt-BR",
    "pause_sensitivity_ms": 2500,  # Pausa após 2.5 segundos sem fala
    "roteiro_path": "roteiro.txt",
    "ativadores": ["bom dia", "boa tarde", "boa noite"],  # Comandos de ativação
    # Integração com WinPlus-IP (desativada temporariamente)
    # "winplus_ip": "192.168.1.100",
    # "winplus_port": 5000
}

def load_script_blocks(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    blocks = [line.strip() for line in text.split('\n') if line.strip()]
    return blocks

# --- ENVIAR COMANDO PARA WINPLUS-IP (DESATIVADO) --- #
def enviar_comando_winplus(comando):
    # Integração com WinPlus-IP será ativada quando IP e porta forem definidos
    pass

# --- DETECTAR TEXTO FALADO --- #
def reconhecer_texto(recognizer, microphone):
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        try:
            audio = recognizer.listen(source, timeout=2, phrase_time_limit=2)
        except sr.WaitTimeoutError:
            return ""
    try:
        return recognizer.recognize_google(audio, language=CONFIG["language"]).lower()
    except:
        return ""

# --- LOOP PRINCIPAL --- #
def main():
    print("INICIANDO TELEPROMPTER...\n")

    if not os.path.exists(CONFIG["roteiro_path"]):
        print(f"Arquivo '{CONFIG['roteiro_path']}' não encontrado.")
        return

    script_blocks = load_script_blocks(CONFIG["roteiro_path"])
    print(f" Roteiro carregado com {len(script_blocks)} blocos.\n")

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    iniciado = False
    current_index = 0
    bloco_em_pausa = False

    try:
        while current_index < len(script_blocks):
            if not iniciado:
                print("🎤 Aguardando comando de ativação: 'Bom dia', 'Boa tarde' ou 'Boa noite'...")
                texto = reconhecer_texto(recognizer, microphone)
                if texto in CONFIG["ativadores"]:
                    iniciado = True
                    enviar_comando_winplus("START_PROMPT")
                    print(f"Comando reconhecido: '{texto}'. Iniciando rolagem...\n")
                else:
                    time.sleep(0.1)
                continue

            # Se não estiver em pausa, exibe o bloco atual
            if not bloco_em_pausa:
                texto_atual = script_blocks[current_index]
                enviar_comando_winplus(f"DISPLAY_TEXT:{texto_atual}")
                print(f"\n{texto_atual}")
                bloco_exibido_em = time.time()

            # Aguarda leitura ou pausa
            while True:
                texto_falado = reconhecer_texto(recognizer, microphone)
                if texto_falado:
                    current_index += 1
                    bloco_em_pausa = False
                    break
                elif (time.time() - bloco_exibido_em) * 1000 > CONFIG["pause_sensitivity_ms"]:
                    enviar_comando_winplus("PAUSE_PROMPT")
                    print(" PAUSA DETECTADA. Aguardando retomada da fala...")
                    bloco_em_pausa = True
                    break
                time.sleep(0.05)

        enviar_comando_winplus("END_PROMPT")
        print("\n✅ Fim do roteiro atingido.")
    except KeyboardInterrupt:
        enviar_comando_winplus("PAUSE_PROMPT")
        print("\nTeleprompter encerrado pelo usuário.")

if __name__ == "__main__":
    main()
