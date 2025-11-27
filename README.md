# Jornada de Desenvolvimento: Teleprompter Broadcast Engine

Este documento detalha o processo de engenharia, os desafios técnicos enfrentados e as soluções arquiteturais implementadas durante o desenvolvimento do **Teleprompter SQUAD 29**.

O projeto evoluiu de um script de reconhecimento de voz simples para algo profissional e robusto, capaz de operar em ambiente de transmissão ao vivo.

---

## 1. Arquitetura do Sistema

O sistema opera em uma arquitetura híbrida **Python (Backend) + Web (Frontend)**, utilizando comunicação **Full-Duplex** via WebSockets para garantir latência zero.

* **Core (Cérebro):** Python 3.13+ processando áudio bruto via `PyAudio`.
* **AI (Reconhecimento):** Modelo `Vosk` (Offline/Edge Computing) para privacidade e velocidade.
* **Comunicação:** `Flask-SocketIO` criando um túnel entre o servidor e o navegador.
* **Interface:** HTML5/CSS3 e JavaScript com manipulação de DOM reativa.

---

## 2. Desafios Técnicos e Soluções (Troubleshooting)

Durante o desenvolvimento, enfrentamos diversos obstáculos técnicos. Abaixo, detalho os principais erros e como foram corrigidos.

### Fase 1: Captura de Áudio e Dependências
* **O Problema:** A instalação da biblioteca `PyAudio` no Windows falhava consistentemente devido à falta de compiladores C++ (`Microsoft Visual C++ 14.0 is required`).
* **A Solução:** Implementamos o uso do `pipwin`, um gerenciador de pacotes que baixa binários pré-compilados (wheels) específicos para Windows, contornando a necessidade de compilação local.

### Fase 2: Conexão WebSocket (O "Erro de Thread")
* **O Problema:** Ao integrar a interface Web, o servidor Flask travava ou não respondia quando o loop de reconhecimento de voz iniciava. O uso da biblioteca `eventlet` causava conflitos de soquete no Windows, gerando o erro `WebSocket is closed before the connection is established`.
* **A Solução:**
    1.  Migramos o modo assíncrono do SocketIO para `async_mode='threading'`.
    2.  Implementamos o gerenciamento de threads via `socketio.start_background_task()`.
    3.  Adicionamos pausas estratégicas (`time.sleep(0.001)`) dentro do loop infinito de áudio para evitar o congelamento da CPU (CPU Starvation) e permitir que o Flask processasse requisições HTTP.

### Fase 3: Lógica de Rolagem (Falsos Positivos)
* **O Problema:** O sistema detectava "pulos" incorretos. Frases curtas como "Bom dia" faziam o prompter pular para qualquer lugar do texto que contivesse essas palavras.
* **A Solução: Lógica de Threshold Dinâmico.**
    * Criamos regras distintas baseadas no tamanho da frase falada.
    * **Frases Curtas (< 40 chars):** Exigem 95% de precisão (Rigor Máximo).
    * **Frases Longas (> 40 chars):** Exigem 80% de precisão (Permite erros de dicção).
    * **Trava de Segurança:** O sistema ignora tentativas de salto com menos de 20 caracteres.

### Fase 4: O Bug da "Primeira Frase"
* **O Problema:** O apresentador precisava ler a primeira frase duas vezes para o sistema "acordar".
* **A Causa:** O código limpava o buffer de áudio (`recognizer.Reset()`) agressivamente logo após abrir o microfone, descartando os primeiros segundos de fala.
* **A Solução:** Removemos a limpeza cíclica e implementamos uma limpeza única na inicialização da stream, garantindo que o sistema esteja ouvindo desde o milissegundo zero.

---

## 3. Evolução do Algoritmo de Match

A parte mais complexa do projeto foi desenvolver o algoritmo que decide **se o que foi dito corresponde ao roteiro**.

### Versão 1.0 (Básica)
* Usava apenas `if palavra in frase`.
* **Falha:** Se o apresentador dissesse "Hoje temos *muitas* notícias" e o roteiro fosse "Hoje temos notícias", o sistema falhava.

### Versão 2.0 (Fuzzy Logic)
* Implementamos `SequenceMatcher` da biblioteca `difflib`.
* Passamos a calcular uma porcentagem de similaridade (0.0 a 1.0).
* **Falha:** Não lidava bem com improvisos longos antes da frase chave.

### Versão 3.0 (Broadcast Standard - Atual)
* **Janelas de Busca (Sliding Window):** O sistema analisa a linha atual, 25 linhas à frente (Lookahead) e 20 linhas para trás (Lookbehind).
* **Recuperação de Sufixo:** Se o apresentador improvisar um parágrafo inteiro, o algoritmo ignora o início da fala e analisa apenas os últimos segundos para tentar "pescar" a frase de retomada do roteiro.
* **Busca Global:** Se uma frase muito longa e única é dita, o sistema quebra a janela e varre o roteiro inteiro para realizar saltos longos (ex: do início para o fim do jornal).

---

## 4. UX/UI: Aspecto de Televisão

A interface foi projetada para simular equipamentos profissionais de estúdio ($5.000+).

* **Smooth Scrolling:** Substituímos a rolagem padrão por transições CSS de `0.6s` e lógica JavaScript com delay calculado. Isso cria o efeito "manteiga" (suave), evitando que o texto pule bruscamente e confunda o leitor.
* **Pacing Artificial:** Implementamos um atraso proposital de 1.2s para frases curtas no Backend. Isso dá tempo para o apresentador respirar e finalizar a entonação antes da próxima linha subir.
* **Feedback Visual:** Alertas coloridos (Amarelo para Saltos, Roxo para Retrocessos) informam a equipe técnica sobre o comportamento do piloto automático.

---

## 5. Segurança e Integridade

Para garantir a autoria e controle de execução em ambientes compartilhados:

1.  **Hash SHA-256:** A senha de produção não é armazenada em texto plano. O sistema compara o Hash da entrada, prevenindo engenharia reversa simples.
2.  **Anti-Tamper:** Uma verificação de integridade checa. Se modificada, o sistema entra em modo de falha e encerra a execução.

---

### Desenvolvimento

Desenvolvido por **Diego Marcelo & Ana Luísa - SQUAD 29**.