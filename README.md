# 📺 Squad 29: Teleprompter por Reconhecimento de Voz

O **Teleprompter por Reconhecimento de Voz** é um MVP desenvolvido pela **Squad 29** para automatizar a rolagem do teleprompter durante transmissões e gravações.  
A aplicação usa **reconhecimento de voz em tempo real** para acompanhar o ritmo de leitura do apresentador e avançar o texto automaticamente, reduzindo a necessidade de um operador dedicado.

O sistema foi pensado para:
- 🤖 Reduzir falhas humanas  
- 🗣️ Dar mais fluidez e naturalidade à apresentação  
- 🎛️ Melhorar o trabalho da equipe técnica  
- 🔒 Funcionar **100% localmente**, usando o modelo offline **Vosk**

---

## 🚀 Tecnologias Utilizadas

- 🐍 **Python 3.10+**
- 🌐 **Flask** — Servidor web  
- 🔌 **Flask‑SocketIO** — Comunicação em tempo real  
- ⚡ **Eventlet** — Suporte para WebSockets  
- 🎤 **Vosk** — Reconhecimento de voz offline  
- 🎧 **PyAudio** — Captura de áudio  
- 🎨 **HTML + CSS + JavaScript** — Interface

---

## 📂 Repositório Oficial do Projeto

🔗 **GitHub:**  
https://github.com/codedbydaph/Projeto-Porto-Digital.git


---

# 1.3 — 📘 Passo a Passo para Execução do MVP

A seguir está o passo a passo completo para **recriar, instalar e executar** o MVP em qualquer computador Windows partindo de um ambiente totalmente limpo.

---

## 🧰 1. Requisitos

### ✔ Python 3.10+  
Baixe em: https://www.python.org/downloads  
> Marque a opção: **Add Python to PATH**

### ✔ Git  
Baixe em: https://git-scm.com/downloads  

---

## 📥 2. Clonar o Projeto

Abra o terminal ou Git Bash na pasta desejada e execute:

```bash
git clone https://github.com/codedbydaph/Projeto-Porto-Digital.git
cd Projeto-Porto-Digital
```

---

## 🗣️ 3. Baixar o Modelo de Voz (Vosk)

O modelo não está no repositório e deve ser baixado separadamente.

1. Acesse: https://alphacephei.com/vosk/models  
2. Baixe: **vosk-model-small-pt-0.3**  
3. Extraia o `.zip`  
4. Renomeie a pasta extraída para:

```
model
```

5. Mova essa pasta para dentro do diretório do projeto:

```
Projeto-Porto-Digital/model/
```

---

## 📁 Estrutura Final do Projeto

A estrutura deve ficar assim:

<pre>
Projeto-Porto-Digital/
├── app.py
├── model/
│   └── (arquivos do modelo vosk)
├── static/
│   ├── css/
│   ├── js/
│   └── img/
├── templates/
│   └── index.html
└── README.md
</pre>

---

## ⚙️ 4. Criar Ambiente Virtual

Dentro da pasta do projeto:

```bash
python -m venv venv
```

Ativar ambiente virtual (Windows):

```bash
.env\Scriptsctivate
```

---

## 📚 5. Instalar Dependências

### ✔ Instalando PyAudio corretamente (Windows)

```bash
pip install pipwin
pipwin install pyaudio
```

### ✔ Instalar o restante das dependências

```bash
pip install flask flask-socketio eventlet vosk
```

---

## ▶️ 6. Executar o Teleprompter

Com o ambiente virtual ativado, execute:

```bash
python app.py
```

O sistema solicitará a senha:

```
dmsousa1
```

Se tudo estiver correto, o servidor ficará disponível em:

```
http://127.0.0.1:5500
```

---

## 🎬 7. Como Usar

1. Abra o navegador  
2. Acesse o endereço acima  
3. Cole ou escreva o roteiro desejado  
4. Comece a ler em voz alta  
5. A rolagem acontecerá automaticamente 📜✨

Quando o terminal mostrar:

```
--- NO AR: Monitorando X linhas ---
```

Significa que o microfone está ativo 🎙️

---

## 🧩 Arquitetura do Sistema  
*(Adicione o arquivo arquitetura.png em static/img/ para aparecer)*

<p align="center">
  <img src="static/img/arquitetura.png" width="650" alt="Fluxo do Sistema">
</p>

Fluxo simplificado:

1. 🎙️ Captura de áudio pelo microfone  
2. 🧠 Áudio enviado para o modelo Vosk (offline)  
3. 🛰️ Flask-SocketIO processa e envia atualizações  
4. 🌐 Interface web recebe comandos e rola o texto automaticamente  

---

## 🛠️ 8. Possíveis Melhorias Futuras

- Captura de áudio via navegador  
- Deploy remoto para uso multiusuário  
- Painel de controle para operadores  
- Ajustes automáticos de velocidade com IA  

---

## 👥 Autores

Projeto desenvolvido pela **Squad 29**:

- Anelise Birk
- Ana Clara Lélis
- Ana Luiza Galati
- Ana Luisa Moreira
- Arthur Braga
- Arthur Ramalho
- Célio Dantas Jr.
- Daphine Milani
- Diego Marcelo
  
---

> Este README foi estruturado para atender completamente ao item **1.3** da avaliação, garantindo replicação total do MVP em ambiente novo.


