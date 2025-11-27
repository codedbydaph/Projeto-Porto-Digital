import eventlet
eventlet.monkey_patch() 

import hashlib
import getpass
import sys
import time
import os
import json
import pyaudio
import unicodedata
import re  
from difflib import SequenceMatcher
from flask import Flask, render_template
from flask_socketio import SocketIO
from vosk import Model, KaldiRecognizer

# --- 🔒 TRAVA DE SEGURANÇA ---
__AUTHOR__ = "Diego Marcelo & Ana Luísa - SQUAD 29"
# -----------------------------

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BG_CYAN = "\033[46m"
    BLACK = "\033[30m"

def check_security():
    os.system('cls' if os.name == 'nt' else 'clear')
    try:
        if globals().get("__AUTHOR__") != "Diego Marcelo & Ana Luísa - SQUAD 29":
            raise ValueError("Integrity Check Failed")
    except:
        print("Erro de integridade.")
        sys.exit(1)

    print("\n" + "="*60)
    print(f"{Colors.BG_CYAN}{Colors.BLACK}{Colors.BOLD}  TELEPROMPTER BROADCAST ENGINE - SQUAD 29  {Colors.RESET}")
    print(f"{Colors.CYAN}  Devs: {__AUTHOR__} {Colors.RESET}")
    print("="*60 + "\n")
    
    HASH_CORRETO = "e00f431df8983277f69ba15687f74d40bf1231aec47ed13394085aa1f3d85340"

    tentativas = 3
    while tentativas > 0:
        try:
            senha = getpass.getpass(f"Senha de Acesso ({tentativas}x): ")
        except:
            senha = input(f"Senha de Acesso ({tentativas}x): ")
            
        if hashlib.sha256(senha.encode()).hexdigest() == HASH_CORRETO:
            print(f"\n{Colors.GREEN}✔ Sistema Armado.{Colors.RESET}\n")
            time.sleep(1)
            return
        else:
            print(f"{Colors.RED}Senha incorreta.{Colors.RESET}")
            tentativas -= 1
    sys.exit(1)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'squad29_final_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', ping_timeout=60)

# --- CONFIGURAÇÕES ---
CONFIG = {
    "model_path": "model",
    "roteiro_path": "roteiro.txt",
    
    # LEITURA SEQUENCIAL
    "similarity_threshold": 0.55,   
    
    # SALTOS GLOBAIS
    "min_chars_for_jump": 20,       
    "jump_threshold_strict": 0.92, 
    "jump_threshold_loose": 0.85,   
    
    "min_len_trigger": 3
}

class TextUtils:
    @staticmethod
    def normalize(text):
        if not text: return ""
        text = text.lower().strip()
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def similarity(a, b):
        return SequenceMatcher(None, a, b).ratio()

    @staticmethod
    def check_match_normal(spoken, line, thresh):
        """Comparação Flexível + RECUPERAÇÃO DE IMPROVISO"""
        n_spoken = TextUtils.normalize(spoken)
        n_line = TextUtils.normalize(line)
        
        if len(n_spoken) < CONFIG["min_len_trigger"]: return False
        
        # 1. Match Direto
        if n_line.startswith(n_spoken) and len(n_spoken) > 5: return True
        if len(n_spoken) > 10 and n_spoken in n_line: return True
        
        snippet = n_line[:len(n_spoken) + 5]
        if TextUtils.similarity(n_spoken, snippet) >= thresh: return True

        # --- RECUPERAÇÃO DE IMPROVISO (AQUI ESTÁ A MÁGICA) ---
        # Se falou muito mais que a linha, ignora o começo (improviso) e olha o fim
        if len(n_spoken) > len(n_line):
            suffix = n_spoken[-(len(n_line) + 5):] # Pega só o final
            
            # Verifica se o roteiro está nesse final
            if n_line in suffix: return True
            if TextUtils.similarity(suffix, n_line) >= thresh: return True
        # -----------------------------------------------------

        return False

    @staticmethod
    def check_match_dynamic(spoken, line):
        """Comparação Rígida para Saltos + Recuperação"""
        n_spoken = TextUtils.normalize(spoken)
        n_line = TextUtils.normalize(line)
        
        if len(n_spoken) < CONFIG["min_chars_for_jump"]: return False
        
        threshold = CONFIG["jump_threshold_strict"] if len(n_spoken) < 40 else CONFIG["jump_threshold_loose"]
        
        # Comparação normal de início
        snippet_len = min(len(n_spoken), len(n_line))
        spoken_start = n_spoken[:snippet_len]
        line_start = n_line[:snippet_len]
        if TextUtils.similarity(spoken_start, line_start) >= threshold: return True

        # Recuperação de Improviso também nos saltos
        if len(n_spoken) > len(n_line) + 5:
             suffix = n_spoken[-(len(n_line) + 5):]
             if TextUtils.similarity(suffix, n_line) >= threshold: return True

        return False

class TeleprompterEngine:
    def __init__(self):
        self.script_lines = []
        self.current_index = 0
        self.running = False
        self.audio_thread = None
        self.load_script()

    def load_script(self):
        if os.path.exists(CONFIG["roteiro_path"]):
            with open(CONFIG["roteiro_path"], "r", encoding="utf-8") as f:
                self.script_lines = [l.strip() for l in f.readlines() if l.strip()]
        else:
            self.script_lines = ["ERRO: Roteiro não encontrado"]

    def start_engine(self):
        if self.audio_thread: return
        self.running = True
        self.audio_thread = socketio.start_background_task(self.process_audio_loop)

    def process_audio_loop(self):
        print(f"{Colors.GREEN}--- ENGINE ONLINE (VARREDURA GLOBAL + IMPROVISO) ---{Colors.RESET}")
        if not os.path.exists(CONFIG["model_path"]): return

        model = Model(CONFIG["model_path"])
        recognizer = KaldiRecognizer(model, 16000)
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
            stream.start_stream()
            
            # Limpeza inicial ÚNICA (para não ter que falar duas vezes)
            stream.read(4096, exception_on_overflow=False)
            recognizer.Reset() 
            
            print(f"--- MICROFONE ABERTO ---")

            while self.running:
                socketio.sleep(0.001)
                try:
                    data = stream.read(4096, exception_on_overflow=False)
                    
                    # Se for frase completa
                    if recognizer.AcceptWaveform(data):
                        res = json.loads(recognizer.Result())
                        txt = res.get("text", "")
                        if txt and self.evaluate(txt, False): 
                            recognizer.Reset()
                    
                    # Se for parcial
                    else:
                        part = json.loads(recognizer.PartialResult())
                        txt = part.get("partial", "")
                        if txt and self.evaluate(txt, True): 
                            recognizer.Reset()
                            
                except Exception:
                    continue
        finally:
            p.terminate()

    def send(self, idx, type, txt):
        self.current_index = idx
        socketio.emit('cmd', {'index': idx, 'type': type, 'text': txt})
        print(f"--> [{type.upper()}] Indo para linha {idx+1}")

    def evaluate(self, text, partial):
        total_lines = len(self.script_lines)
        if self.current_index >= total_lines: return False
        
        # --- 1. REGRA DE OURO (Retorno à Linha 1) ---
        if total_lines > 0:
            # Usa check_match_normal que agora tem recuperação de improviso
            if TextUtils.check_match_normal(text, self.script_lines[0], CONFIG["similarity_threshold"]):
                if self.current_index > 2: 
                    self.send(0, 'back', self.script_lines[0])
                    return True

        # --- 2. LEITURA SEQUENCIAL (Linha Atual) ---
        curr = self.script_lines[self.current_index]
        if TextUtils.check_match_normal(text, curr, CONFIG["similarity_threshold"]):
            
            # CONTROLE DE RITMO
            if len(curr) < 45:
                time.sleep(1.2) 

            self.send(self.current_index + 1, 'next', curr)
            return True

        # --- 3. VARREDURA GLOBAL (Pulos e Voltas Livres) ---
        if len(text) > CONFIG["min_chars_for_jump"]:
            
            for i in range(total_lines):
                if i == self.current_index: continue
                
                # Usa check_match_dynamic que também tem recuperação de improviso
                if TextUtils.check_match_dynamic(text, self.script_lines[i]):
                    direction = 'jump' if i > self.current_index else 'back'
                    self.send(i + 1, direction, self.script_lines[i])
                    return True

        return False

engine = TeleprompterEngine()

@app.route('/')
def index():
    return render_template('index.html', script=engine.script_lines)

@socketio.on('connect')
def handle_connect():
    print('CLIENTE CONECTADO')
    socketio.emit('cmd', {'index': engine.current_index, 'type': 'sync', 'text': ''})
    engine.start_engine()

if __name__ == '__main__':
    check_security()
    print(f"Servidor: http://127.0.0.1:5500")
    socketio.run(app, debug=True, port=5500)