from dotenv import load_dotenv
import os
import sounddevice as sd
import numpy as np
import wave
import whisper
import json
import requests
import re

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configurações
DURATION = 10  # Tempo de gravação (segundos)
SAMPLERATE = 44100  # Taxa de amostragem
AUDIO_DIR = "audios"  # Pasta para arquivos de áudio
LEMBRETE_DIR = "lembretes"  # Pasta para arquivos JSON
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"  # Modelo da GROQ

# Criar diretórios se não existirem
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(LEMBRETE_DIR, exist_ok=True)

def get_timestamp():
    # Retorna timestamp formatado para uso em nomes de arquivo
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def record_audio(duration=DURATION, samplerate=SAMPLERATE):
    # Grava o áudio do microfone e salva como WAV
    timestamp = get_timestamp()
    filename = os.path.join(AUDIO_DIR, f"audio_{timestamp}.wav")
    
    print("Gravando...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype=np.int16)
    sd.wait()  # Aguarda a gravação terminar
    print("Gravação finalizada.")

    # Salvar áudio
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  
        wf.setframerate(samplerate)
        wf.writeframes(audio.tobytes())

    return filename


def transcribe_audio(filename):
    # Transcreve o áudio para texto usando Whisper
    model = whisper.load_model("small")
    result = model.transcribe(filename, language="pt")
    return result["text"]


def extract_info_with_groq(text):
    # Usa a API da GROQ para extrair informações da frase
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    prompt = f'''
    Extraia a data, horário e tarefa do seguinte lembrete:
    "{text}"

    💡 IMPORTANTE: Responda *somente* com JSON puro. Nada mais.

    Exemplo de saída:
    json
    {{
      "data": "06/03/2025",
      "hora": "11:00",
      "tarefa": "Estudar"
    }}
    
    '''
    data = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }

    response = requests.post(url, headers=headers, json=data)

    # Imprimir resposta completa para debug
    print("Resposta da API:", response.json())

    try:
        content = response.json()["choices"][0]["message"]["content"]
        
        # Extrai apenas o JSON usando regex
        match = re.search(r"\{.*\}", content, re.DOTALL)
        
        if match:
            return json.loads(match.group(0))  
        else:
            print("Erro: A resposta não contém um JSON válido:", content)
            return {"erro": "Falha ao processar resposta da API"}
    except KeyError:
        print("Erro: A API não retornou 'choices'. Resposta:", response.json())
        return {"erro": "Falha ao processar resposta da API"}


def save_to_json(info):
    # Salva os dados extraídos em um arquivo JSON
    timestamp = get_timestamp()
    filename = os.path.join(LEMBRETE_DIR, f"lembrete_{timestamp}.json")
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=4, ensure_ascii=False)
    print(f"Lembrete salvo em {filename}")


def detect_intent_with_groq(text):
    # Detecta a intenção do usuário usando a API da GROQ
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    prompt = f'''
    Analise a frase abaixo e determine se a intenção é CRIAR um novo lembrete ou BUSCAR lembretes existentes.
    
    Frase: "{text}"
    
    💡 IMPORTANTE: Responda *somente* com JSON puro no formato:
    {{
        "intencao": "criar" ou "buscar",
        "explicacao": "breve explicação do motivo"
    }}
    '''
    
    data = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }

    response = requests.post(url, headers=headers, json=data)
    
    try:
        content = response.json()["choices"][0]["message"]["content"]
        match = re.search(r"\{.*\}", content, re.DOTALL)
        
        if match:
            resultado = json.loads(match.group(0))
            print(f"Intenção detectada: {resultado['intencao']}")
            print(f"Explicação: {resultado['explicacao']}")
            return resultado["intencao"]
        else:
            print("Erro ao detectar intenção. Assumindo 'criar' como padrão.")
            return "criar"
    except Exception as e:
        print(f"Erro ao processar resposta da API: {e}")
        return "criar"

def buscar_lembretes():
    # Busca e retorna todos os lembretes salvos
    lembretes = []
    
    # Lista todos os arquivos JSON na pasta de lembretes
    for arquivo in os.listdir(LEMBRETE_DIR):
        if arquivo.endswith('.json'):
            caminho_arquivo = os.path.join(LEMBRETE_DIR, arquivo)
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                lembrete = json.load(f)
                lembretes.append(lembrete)
    
    return lembretes

def mostrar_lembretes(lembretes):
    # Mostra os lembretes de forma organizada
    if not lembretes:
        print("Nenhum lembrete encontrado!")
        return
    
    print("\n=== SEUS LEMBRETES ===")
    for i, lembrete in enumerate(lembretes, 1):
        print(f"\nLembrete {i}:")
        print(f"Data: {lembrete.get('data', 'Não especificada')}")
        print(f"Hora: {lembrete.get('hora', 'Não especificada')}")
        print(f"Tarefa: {lembrete.get('tarefa', 'Não especificada')}")
    print("\n====================")

# Execução do fluxo
audio_file = record_audio()
texto_transcrito = transcribe_audio(audio_file)
print("Texto transcrito:", texto_transcrito)

# Detecta a intenção do usuário usando IA
intencao = detect_intent_with_groq(texto_transcrito)

if intencao == "buscar":
    print("Buscando seus lembretes...")
    lembretes = buscar_lembretes()
    mostrar_lembretes(lembretes)
else:
    print("Criando novo lembrete...")
    informacoes = extract_info_with_groq(texto_transcrito)
    print("Informações extraídas:", informacoes)
    save_to_json(informacoes)