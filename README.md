# Teleprompter por Reconhecimento de Voz — SQUAD 29

O Teleprompter por Reconhecimento de Voz é um MVP desenvolvido pela **Squad 29** com o objetivo de automatizar a rolagem do teleprompter, eliminando a necessidade de um operador dedicado durante transmissões e gravações.  
A solução utiliza reconhecimento de voz em tempo real para ajustar a rolagem do texto conforme o ritmo do apresentador, proporcionando maior fluidez, naturalidade e precisão.

O sistema foi projetado para reduzir falhas humanas, melhorar a experiência do apresentador e otimizar o trabalho da equipe técnica. Toda a aplicação funciona localmente, utilizando o modelo offline **Vosk**, garantindo estabilidade e desempenho adequado para ambientes de estúdio.

---

# 1. Link dos Arquivos do MVP

## **1.1 — Código-fonte do Projeto**
https://github.com/SEU-USUARIO/NOME-DO-REPOSITORIO  
*(substitua pelo link real do repositório no GitHub)*

---

## **1.2 — Versão Online ou Executável do MVP**

O sistema roda localmente devido ao uso de áudio em tempo real.

Após a instalação (passos abaixo), execute:

```bash
python app.py
``` 

A interface estará disponível em:  
**http://127.0.0.1:5500**

---

# 1.3 — Passo a Passo de Instalação e Execução

A seguir está o guia completo para rodar o MVP do zero em um computador **Windows**, mesmo sem conhecimento técnico prévio.

---

## 1. Pré-requisitos

### ✔ Python 3.10 ou superior  
Baixe em: https://www.python.org/downloads  

⚠ Durante a instalação, marque a opção:  
**Add Python to PATH**

---

### ✔ Git  
Baixe em: https://git-scm.com/downloads  

Siga o instalador clicando em **Next** até finalizar.

---

## 2. Baixando o Projeto

1. Crie uma pasta no seu computador.  
2. Clique com o botão direito dentro da pasta → **Open Git Bash here**.  
3. Execute o comando:

```bash
git clone https://github.com/SEU-USUARIO/NOME-DO-REPOSITORIO.git
```

Acesse o diretório do projeto:

cd NOME-DO-REPOSITORIO

## 3. Baixando o Modelo de Voz (Obrigatório)

O modelo de reconhecimento de voz não é armazenado no GitHub e precisa ser baixado manualmente.

1. Acesse: https://alphacephei.com/vosk/models  
2. Procure por **Portuguese**  
3. Baixe o modelo: **vosk-model-small-pt-0.3**  
4. Extraia o arquivo `.zip`  
5. Renomeie a pasta extraída para:


6. Mova essa pasta `model` para dentro da pasta do projeto, ao lado do arquivo `app.py`.

A estrutura final deve ficar parecida com isto:

/NOME-DO-REPOSITORIO
├── app.py # Arquivo principal da aplicação
├── model/ # Modelo Vosk (reconhecimento de voz)
│ └── ...
├── static/ # Arquivos estáticos (CSS, JS, imagens)
│ ├── css/
│ ├── js/
│ └── img/
├── templates/ # Arquivos HTML
│ └── index.html
└── README.md # Documentação do projeto

## 4. Instalando as Dependências

Com o terminal aberto dentro da pasta do projeto:

### Criar ambiente virtual

```bash
python -m venv venv
```

### Ativar o ambiente virtual (Windows)

```bash
.\venv\Scripts\activate
```

Se der certo, o terminal passará a mostrar algo como:
```bash
(venv) C:\caminho\para\seu\projeto>
```


### Instalar PyAudio corretamente (Windows)

```bash
pip install pipwin
pipwin install pyaudio
```

### Instalar as demais bibliotecas
```bash
pip install flask flask-socketio eventlet vosk
``` 

## 5. Rodando o Teleprompter

Com o ambiente virtual ainda ativado, execute:

```bash
python app.py
```

O sistema solicitará uma senha. Use:
```nginx
dmsousa1
```

Se tudo estiver correto, o terminal exibirá algo como:
```nginx
Servidor Rodando: http://127.0.0.1:5500
```

## 6. Usando o Teleprompter

Abra seu navegador (Chrome, Edge, etc.).

Acesse o endereço: http://127.0.0.1:5500

Insira ou cole o roteiro desejado na interface.

Observe o terminal: quando aparecer a mensagem:

--- NO AR: Monitorando X linhas ---

Significa que o microfone está ativo.

A partir daí, você pode começar a ler o texto em voz alta.  
**O teleprompter fará a rolagem automaticamente conforme a sua fala.**


