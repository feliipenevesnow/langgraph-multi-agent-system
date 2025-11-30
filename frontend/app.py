import streamlit as st
import requests
import uuid
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Banco Ágil", page_icon="🏦", layout="wide")

typing_css = """
<style>
.typing-indicator {
    display: inline-flex;
    align-items: center;
    column-gap: 3px;
}
.typing-text {
    font-size: 14px;
    color: #333;
    margin-right: 5px;
    animation: blink 1.4s infinite both;
}
.dot {
    height: 6px;
    width: 6px;
    background-color: #bbb;
    border-radius: 50%;
    opacity: 0.6;
    animation: blink 1.4s infinite both;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes blink {
    0% { opacity: 0.1; }
    20% { opacity: 1; }
    100% { opacity: 0.1; }
}

[data-testid="stChatMessageAvatar"] img {
    transform: scale(2.5);
    object-position: top center;
}
</style>
"""
st.markdown(typing_css, unsafe_allow_html=True)

def stream_data(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.05)

def init_chat():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    st.session_state.chat_history = []
    
    with st.spinner("Iniciando atendimento..."):
        try:
            response = requests.post(
                f"{API_URL}/chat", 
                json={"message": "Olá", "session_id": st.session_state.session_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                welcome_msg = data.get("response", "Olá! Bem-vindo ao Banco Ágil.")
                st.session_state.chat_history.append({"role": "assistant", "content": welcome_msg})
            else:
                 st.session_state.chat_history.append({"role": "assistant", "content": "Olá! (Erro ao conectar com o agente)"})
            
        except requests.exceptions.ConnectionError:
            st.session_state.chat_history.append({"role": "assistant", "content": "Olá! (Sistema indisponível no momento)"})

LOGO_PATH = "img/logo.png"
AVATAR_PATH = "img/atendente.png"

def reset_session():
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.chat_history = []

with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width="stretch")
    else:
        st.title("Banco Ágil")
    
    st.markdown("---")
    
    st.markdown("### Como podemos ajudar?")
    st.markdown("Nossa equipe está pronta para ajudar com:")
    st.markdown("- 💳 **Crédito**")
    st.markdown("- 💱 **Câmbio**")
    st.markdown("- ℹ️ **Informações**")
    
    st.button("Limpar Conversa", on_click=reset_session)

st.title("💬 Atendimento Banco Ágil")
st.caption("Conectado ao Suporte Online")

if "chat_history" not in st.session_state or not st.session_state.chat_history:
    init_chat()


for i, message in enumerate(st.session_state.chat_history):
    is_assistant = message["role"] == "assistant"
    avatar = AVATAR_PATH if is_assistant else "👤"
    name_label = "Atendente" if is_assistant else "Você"
    
    with st.container(key=f"msg_{i}"):
        with st.chat_message(message["role"], avatar=avatar):
            st.caption(name_label)
            st.markdown(message["content"])


prompt = st.chat_input("Digite sua mensagem...")

if prompt:
    
    with st.chat_message("user", avatar="👤"):
        st.caption("Você")
        st.markdown(prompt)
    
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    
    with st.chat_message("assistant", avatar=AVATAR_PATH):
            st.caption("Atendente")
            
            typing_placeholder = st.empty()
            typing_placeholder.markdown(
                """
                <div class="typing-indicator">
                    <span class="typing-text">Digitando</span>
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            try:
                response = requests.post(
                    f"{API_URL}/chat", 
                    json={"message": prompt, "session_id": st.session_state.session_id}
                )
                
                typing_placeholder.empty()
                
                if response.status_code == 200:
                    data = response.json()
                    bot_response = data.get("response", "Sem resposta do sistema.")
                    
                    st.write_stream(stream_data(bot_response))
                    st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
                    
                else:
                    error_msg = f"Erro no Sistema: {response.status_code}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
    
            except requests.exceptions.ConnectionError:
                typing_placeholder.empty()
                error_msg = "🚨 Falha na conexão! O sistema está indisponível."
                st.error(error_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
