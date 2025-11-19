import os
import sys
import json
import pyaudio
import logging
import unicodedata
import re
from difflib import SequenceMatcher
from vosk import Model, KaldiRecognizer

# --- CONFIGURAÇÕES ---
CONFIG = {
    "model_path": "model",          
    "roteiro_path": "roteiro.txt",  
    "similarity_threshold": 0.60,   
    "jump_threshold": 0.85,         
    "lookahead_lines": 5,           
    "min_len_trigger": 4,           
    "winplus_ip": "127.0.0.1",      
    "winplus_port": 21000           
}

# --- CORES E ESTILOS PARA O TERMINAL ---
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    # Fundo colorido para destaque
    BG_CYAN = "\033[46m"
    BG_YELLOW = "\033[43m"
    BLACK = "\033[30m" # Texto preto para usar com fundo claro

# --- LOGGING ---
# Ajustei para mostrar apenas a mensagem limpa, sem data/hora poluindo o visual do teste
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)

# --- UTILS DE TEXTO ---
class TextUtils:
    @staticmethod
    def normalize(text: str) -> str:
        if not text: return ""
        text = text.lower().strip()
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def similarity(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    @staticmethod
    def check_match(spoken_raw: str, script_line: str, threshold: float) -> bool:
        norm_spoken = TextUtils.normalize(spoken_raw)
        norm_script = TextUtils.normalize(script_line)

        if len(norm_spoken) < CONFIG["min_len_trigger"]:
            return False
            
        # 1. Match Exato de Início
        if norm_script.startswith(norm_spoken) and len(norm_spoken) > 5:
            return True
            
        # 2. Contido na linha
        if len(norm_spoken) > 10 and norm_spoken in norm_script:
            return True
        
        # 3. Recuperação de Improviso (Olha o final da fala)
        if len(norm_spoken) > len(norm_script):
            suffix_spoken = norm_spoken[-(len(norm_script) + 5):]
            if TextUtils.similarity(suffix_spoken, norm_script) >= threshold:
                return True
            if norm_script in suffix_spoken:
                return True

        # 4. Similaridade Padrão
        script_snippet = norm_script[:len(norm_spoken) + 5] 
        if TextUtils.similarity(norm_spoken, script_snippet) >= threshold:
            return True

        return False

# --- CONTROLLER VISUAL DO WINPLUS ---
class WinPlusController:
    @staticmethod
    def scroll_next():
        # Simples indicação de rolagem
        logging.info(f"{Colors.GREEN}⬇️  Rolando texto...{Colors.RESET}")

    @staticmethod
    def jump_to_line(line_index, full_text):
        # DESTAQUE VISUAL FORTE AQUI
        print("\n" + "="*60)
        print(f"{Colors.BG_YELLOW}{Colors.BLACK}{Colors.BOLD} ⚠️  SALTO DETECTADO! REPOSICIONANDO PROMPTER... {Colors.RESET}")
        print(f"{Colors.BG_CYAN}{Colors.BLACK} ▶️  NOVA LINHA ATUAL: {full_text} {Colors.RESET}")
        print("="*60 + "\n")

# --- ENGINE ---
class TeleprompterEngine:
    def __init__(self):
        self.script_lines = []
        self.current_index = 0
        self.load_script()
        self.init_vosk()

    def load_script(self):
        if not os.path.exists(CONFIG["roteiro_path"]):
            logging.error("Arquivo roteiro.txt não encontrado.")
            sys.exit(1)
        with open(CONFIG["roteiro_path"], "r", encoding="utf-8") as f:
            self.script_lines = [line.strip() for line in f.readlines() if line.strip()]
        print(f"{Colors.BOLD}Roteiro carregado: {len(self.script_lines)} linhas.{Colors.RESET}")

    def init_vosk(self):
        if not os.path.exists(CONFIG["model_path"]):
            logging.error(f"Modelo não encontrado em '{CONFIG['model_path']}'.")
            sys.exit(1)
        
        print(f"{Colors.BLUE}Carregando modelo de voz...{Colors.RESET}")
        try:
            model = Model(CONFIG["model_path"])
            self.recognizer = KaldiRecognizer(model, 16000)
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
            self.stream.start_stream()
            print(f"{Colors.GREEN}{Colors.BOLD}🎙️  MICROFONE ATIVO. Pode começar a leitura.{Colors.RESET}\n")
        except Exception as e:
            logging.error(f"Erro de áudio: {e}")
            sys.exit(1)

    def print_current_target(self):
        """Mostra qual linha o sistema está esperando ouvir"""
        if self.current_index < len(self.script_lines):
            # Imprime em Azul Ciano para o operador saber onde está
            print(f"{Colors.CYAN}➡️  Aguardando: {Colors.BOLD}'{self.script_lines[self.current_index]}'{Colors.RESET}")

    def process_audio(self):
        self.print_current_target()
        
        while self.current_index < len(self.script_lines):
            try:
                data = self.stream.read(2048, exception_on_overflow=False)
            except IOError:
                continue
            
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "")
                if text: self.evaluate_text(text, is_partial=False)
            else:
                partial_result = json.loads(self.recognizer.PartialResult())
                partial_text = partial_result.get("partial", "")
                if partial_text: self.evaluate_text(partial_text, is_partial=True)

        print(f"\n{Colors.GREEN}{Colors.BOLD}🏁 ROTEIRO FINALIZADO!{Colors.RESET}")

    def evaluate_text(self, input_text, is_partial):
        if len(input_text) < CONFIG["min_len_trigger"]:
            return
        
        if self.current_index >= len(self.script_lines):
            return

        target_line = self.script_lines[self.current_index]
        
        # --- 1. LINHA ATUAL ---
        if TextUtils.check_match(input_text, target_line, threshold=CONFIG["similarity_threshold"]):
            logging.info(f"✅ Lido: '{target_line}'")
            self.advance_script(steps=1)
            self.recognizer.Reset()
            return

        # --- 2. PULO DE LINHA ---
        if not is_partial or len(input_text) > 15:
            max_lookahead = min(len(self.script_lines), self.current_index + CONFIG["lookahead_lines"])
            
            for offset in range(1, max_lookahead - self.current_index):
                future_index = self.current_index + offset
                future_line = self.script_lines[future_index]
                
                if TextUtils.check_match(input_text, future_line, threshold=CONFIG["jump_threshold"]):
                    # Chama o controlador visual passando a linha completa
                    WinPlusController.jump_to_line(future_index, future_line)
                    
                    self.current_index = future_index + 1 
                    
                    # Mostra a próxima linha após o salto
                    self.print_current_target()

                    self.recognizer.Reset()
                    return

    def advance_script(self, steps=1):
        WinPlusController.scroll_next()
        self.current_index += steps
        self.print_current_target()

    def cleanup(self):
        if hasattr(self, 'stream'): 
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'p'): 
            self.p.terminate()

if __name__ == "__main__":
    engine = TeleprompterEngine()
    try:
        engine.process_audio()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Encerrando aplicação...{Colors.RESET}")
        engine.cleanup()