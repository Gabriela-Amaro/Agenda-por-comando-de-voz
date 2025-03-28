# Agenda de  lembretes por comando de voz
Sistema de agendamento de lembrete por comando de voz

### Pré-requisitos
- Python
```bash
sudo apt install python
```
- PortAudio
```bash
sudo apt install portaudio
```

## Primeiros passos

#### Clonar e entrar no repositório
```bash
git clone git@github.com:Gabriela-Amaro/Agenda-por-comando-de-voz.git && cd Agenda-por-comando-de-voz
```

#### Criar e ativar um ambiente virtual
```bash
python -m venv .venv && source .venv/bin/activate
```

#### Instalar as dependências
```bash
pip install -r requirements.txt
```

#### Criar o arquivo .env e configurar as variáveis de ambiente
```bash
touch .env && echo "GROQ_API_KEY=" >> .env
```
Agora abra o arquivo .env e insira a sua chave da API groq

[Crie sua chave aqui](http://console.groq.com/)
