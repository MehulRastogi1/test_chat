import os
import random
import streamlit as st
from groq import Groq
from ddgs import DDGS
import pandas as pd
import speech_recognition as sr
from deep_translator import GoogleTranslator
import edge_tts
import asyncio
import base64        
from streamlit_mic_recorder import mic_recorder
import tempfile

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Chat Assistant",
    page_icon="🤖",
    layout="wide"
)

#==================== FUNCTION ==========================
# ------------------- VOICE INPUT FUNCTION -------------------
def voice_input_to_prompt(audio):

    temp_path = None

    try:
        raw = audio.get("bytes")

        # agar bytes base64 me aaye
        if isinstance(raw, str):
            raw = base64.b64decode(raw)

        # temp file create
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
        temp_path = tf.name
        tf.write(raw)
        tf.close()

        # Groq Whisper STT
        transcription = client.audio.transcriptions.create(
            file=(temp_path, open(temp_path, "rb").read()),
            model="whisper-large-v3",
            response_format="json",
            language="hi"
        )

        text = transcription.text

        translated = GoogleTranslator(
            source="auto",
            target="en"
        ).translate(text)

        st.success(f"🗣 You said: {text}")
        st.info(f"🌍 English: {translated}")

        st.session_state.voice_prompt = translated
        return translated

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
        return None

# -------- WEB SEARCH --------
def search_web(query, results=5):

    output = []

    try:
        with DDGS() as ddgs:

            for r in ddgs.text(query, max_results=results):

                title = r["title"]
                body = r["body"]
                link = r["href"]

                output.append(f"{title}\n{body}\n{link}")

    except:
        return "Web search failed."

    return "\n\n".join(output)



# ---------------- SESSION STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None
    

if "regen" not in st.session_state:
    st.session_state.regen = False

if "voice_prompt" not in st.session_state:
    st.session_state.voice_prompt = None
    st.session_state.last_response=None

if "voice" not in st.session_state:
    st.session_state.voice = False

# ---------------- CUSTOM CSS (UI / COLORS ONLY) ----------------
st.markdown(
    """
    <style>
    /* Overall app background: very light, warm gradient */
    .stApp {
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        color-scheme: light;
    }

    /* Main container: centered, comfortable width */
    .main .block-container {
        max-width: 1100px;
        padding-top: 18px;
        padding-left: 28px;
        padding-right: 28px;
        padding-bottom: 28px;
        margin: 0 auto;
    }

    /* Sidebar: soft, friendly blue with subtle shadow */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f6f9ff 0%, #eef6ff 100%);
        border-right: 1px solid rgba(18,58,107,0.06);
        padding: 18px 16px 24px 16px;
        box-shadow: 0 2px 8px rgba(15, 30, 60, 0.03);
    }

    /* Sidebar title and labels color */
    [data-testid="stSidebar"] .css-1d391kg h1,
    [data-testid="stSidebar"] .css-1d391kg h2,
    [data-testid="stSidebar"] .css-1d391kg h3,
    [data-testid="stSidebar"] .css-1d391kg label {
        color: #0f3a66;
    }

    /* Tidy the sidebar widgets spacing */
    [data-testid="stSidebar"] .stButton, 
    [data-testid="stSidebar"] .stRadio, 
    [data-testid="stSidebar"] .stSelectbox {
        margin-top: 8px;
        margin-bottom: 8px;
    }

    /* App title: centered and prominent */
    .css-18e3th9 h1, .css-1v3fvcr h1 {
        text-align: center;
        color: #0f3a66;
        font-weight: 700;
        margin-bottom: 6px;
    }

    /* Subtitle / small text color */
    .css-1v0mbdj, .css-1v0mbdj p {
        color: #2b4a6f;
    }

    /* Chat message container: rounded, airy */
    .stChatMessage {
        border-radius: 14px;
        padding: 12px 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 0 rgba(16,24,40,0.03);
        font-size: 15px;
        line-height: 1.5;
        max-width: 88%;
        word-wrap: break-word;
    }

    /* User messages: soft cyan bubble aligned right */
    .stChatMessage[data-testid="stChatMessage-user"] {
        background: linear-gradient(180deg, #e9fbff 0%, #e6f7ff 100%);
        border: 1px solid #bfeeff;
        color: #08324a;
        margin-left: auto;
        margin-right: 6px;
    }

    /* Assistant messages: warm cream bubble aligned left */
    .stChatMessage[data-testid="stChatMessage-assistant"] {
        background: linear-gradient(180deg, #fffdf6 0%, #fff9e6 100%);
        border: 1px solid #ffe9a8;
        color: #3b2f00;
        margin-right: auto;
        margin-left: 6px;
    }

    /* System / other messages: subtle gray */
    .stChatMessage[data-testid="stChatMessage-system"] {
        background: #f6f7fb;
        border: 1px solid #e6e9f2;
        color: #2b3a55;
        margin-left: 6px;
        margin-right: 6px;
    }

    /* Chat input styling: rounded, clear */
    .stChatInput textarea, .stChatInput input {
        border-radius: 10px;
        border: 1px solid #d6e6ff;
        padding: 10px 12px;
        background: #ffffff;
        color: #0b2b45;
        box-shadow: none;
    }

    /* Placeholder caret color for input */
    .stChatInput textarea::placeholder, .stChatInput input::placeholder {
        color: #7a9bb8;
    }

    /* Primary buttons: friendly blue */
    .stButton>button {
        background-color: #0b79d0;
        color: #ffffff;
        border-radius: 8px;
        padding: 8px 14px;
        border: none;
        font-weight: 600;
        box-shadow: 0 2px 6px rgba(11,121,208,0.12);
    }
    .stButton>button:hover {
        background-color: #0961a8;
        color: #ffffff;
    }

    /* Danger / clear button: subtle red outline */
    [data-testid="stSidebar"] .stButton>button:has(svg[aria-hidden="true"]) {
        background-color: #fff6f6;
        color: #a12b2b;
        border: 1px solid rgba(161,43,43,0.08);
        box-shadow: none;
    }

    /* Regenerate button: slightly different accent */
    button[kind="primary"][title="regen_btn"], .stButton>button[aria-label="🔄 Regenerate"] {
        background-color: #16a34a;
    }

    /* Fix file uploader text display */
.stFileUploader [data-testid="stFileUploadLabel"] {
    position: relative;   /* remove overlay issues */
    z-index: 2;
    color: #0b2b45;      /* visible text color */
    font-weight: 500;
}

/* Optional: make container slightly taller so name fits */
.stFileUploader > div {
    min-height: 50px;    /* ensure text fits */
}

    /* Sidebar separators */
    [data-testid="stSidebar"] hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, rgba(18,58,107,0.06), rgba(18,58,107,0.02));
        margin: 12px 0;
    }

    /* Links color */
    a {
        color: #0b79d0;
    }

    

    /* Slight spacing improvement for chat area */
    .css-1lcbmhc.e1fqkh3o3 {
        gap: 14px;
    }

    /* Responsive tweaks */
    @media (max-width: 900px) {
        .main .block-container {
            padding-left: 12px;
            padding-right: 12px;
        }
        .stChatMessage {
            font-size: 14px;
            max-width: 96%;
        }
        [data-testid="stSidebar"] {
            padding-left: 12px;
            padding-right: 12px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ---------------- API KEY ----------------
#api_key = os.getenv("GROQ_API_KEY")
api_key = st.secrets["GROQ_API_KEY"]

client = None
if api_key:
    client = Groq(api_key=api_key)

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ AI Settings")

mode = st.sidebar.radio(
    "Select AI Mode",
    ["FAST", "THINK HARD","CODER"]
)

# ---------------- AI SETTINGS ----------------
with st.sidebar.expander("⚙️ Model Settings", expanded=True):
       
    # -------- MODE CONFIG --------
    mode_configs = {
        "FAST": {
            "model": "llama-3.1-8b-instant",
            "temperature": 0.3,
            "max_tokens": 300,
            "system_prompt": "Give short and direct answers."
        },
        "THINK HARD": {
            "model": "qwen/qwen3-32b",
            "temperature": 0.2,
            "max_tokens": 1500,
            "system_prompt": "Think step by step and solve complex problems."
        },
        "CODER": {
            "model": "llama-3.3-70b-versatile",
            "temperature": 0.2,
            "max_tokens": 1200,
            "system_prompt": "You are an expert programmer. Write clean, correct and optimized code."
        }
    }

    config = mode_configs[mode]
    
    # -------- MODEL SELECT --------
    model = st.selectbox(
        "Model",
        [
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "qwen/qwen3-32b",
            
        ],
        index=0 if config["model"] == "llama-3.1-8b-instant"
        else 1 if config["model"] == "llama-3.3-70b-versatile"
        else 2 if config["model"] == "qwen/qwen3-32b"
        else 3
    )

    # -------- MAX TOKENS SLIDER --------
    max_tokens = st.slider(
        "Max Tokens",
        100,
        4096,
        config["max_tokens"]
    )

temperature = config["temperature"]
web_mode = st.sidebar.toggle("🌐 Internet Access")

# -------- FILE UPLOAD --------
uploaded_file = st.sidebar.file_uploader(
    "📂 Upload file (CSV / TXT)",
    type=["csv","txt"]
)

file_text = ""

if uploaded_file:

    try:

        if uploaded_file.type == "text/csv":

            df = pd.read_csv(uploaded_file)
            file_text = df.to_string()

        elif uploaded_file.type == "text/plain":

            file_text = uploaded_file.read().decode("utf-8")

    except:
        file_text = "Failed to read file."


# ---------------- VOICE SETTINGS ----------------
if "voice_settings" not in st.session_state:
    st.session_state.voice_settings = {
        "rate": "Normal",      # default
        "volume": 1.0,
        "voice": None
    }
    st.session_state.last_response = None

with st.sidebar.expander("🔊 Voice Settings"):
   # Fixed rate options instead of slider
    rate_choice = st.selectbox(
        "Speech Rate",
        [ "Normal","High", "Slow"]
    )
    st.session_state.voice_settings["rate"] = rate_choice
    voice_choice = st.selectbox(
        "Voice",
        [
            "Default",
            "English Male",
            "English Female",
            
            "Hindi Female"
        ]
    )
    st.session_state.voice_settings["voice"] = voice_choice






st.sidebar.markdown("---")

# if "audio" not in st.session_state:
#     st.session_state.audio=None
#     st.session_state.audio_click=False

# ------------------- SIDEBAR BUTTONS SIDE BY SIDE -------------------
col1, col2 = st.sidebar.columns([1, 1])  # two equal-width columns

# -------- Clear Chat Button --------
with col1:
    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        st.session_state.last_prompt = None
        st.session_state.voice_prompt = None
        st.rerun()

# -------- Voice Input Button --------
# with col2:
#     if st.button("🎤Voice I/O") or st.session_state.audio_click:
#         st.session_state.audio_click=True
#         if not st.session_state.audio:
#             st.session_state.audio = mic_recorder(
#                     start_prompt="🎤 Start recording",
#                     stop_prompt="⏹ Stop recording",
#                     just_once=True
#                 )
#         if st.session_state.audio:
#             result = voice_input_to_prompt(st.session_state.audio)
#             st.session_state.audio=None
#             st.session_state.audio_click=False
#             if result:
#                 st.session_state.voice = True
#                 st.rerun()  # auto-run AI response


with col2:

    audio = mic_recorder(
        start_prompt="🎤 Start recording",
        stop_prompt="⏹ Stop recording",
        just_once=True
    )

    if audio:
        # st.write(audio)
        result = voice_input_to_prompt(audio)
        if result:
            st.session_state.voice = True
            st.rerun()

# ---------------- TITLE ----------------
st.title("🤖 AI Chat Assistant")


# ---------------- DISPLAY HISTORY ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- USER INPUT ----------------
prompt = st.chat_input("Ask anything...")


# ---------- NORMAL USER MESSAGE ----------
if prompt and not st.session_state.regen:

    st.session_state.last_prompt = prompt

    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

if st.session_state.voice:
    prompt = st.session_state.voice_prompt
    st.session_state.last_prompt = prompt
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    st.session_state.voice=False
    st.session_state.voice_prompt=None

# ---------- REGENERATE ----------
if st.session_state.regen:

    prompt = st.session_state.last_prompt

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        st.session_state.messages.pop()

    st.session_state.regen = False

# ---------- GENERATE ----------
if prompt:

    CONTEXT_LIMIT = 10

    context_messages = [
        {"role": "system", "content": config["system_prompt"]}
    ] + st.session_state.messages[-CONTEXT_LIMIT:]

    # -------- FILE CONTEXT --------
    if file_text:

        context_messages[0]["content"] += (
            "\n\nUse the following file content to answer the user question.\n\n"
            + file_text[:12000]
        )

    # -------- WEB SEARCH --------
    if web_mode: 

        with st.spinner("🌐 Searching internet..."):
            search_results = search_web(prompt)

        context_messages[0]["content"] += (
            "\n\nUse the following web search results if helpful.\n\n"
            + search_results
        )
    
    # -------- RANDOMNESS BOOST --------
    temp = temperature

    if prompt == st.session_state.last_prompt:
        temp = min(temperature + random.uniform(0.2, 0.5), 1.5)

    # ---------- GENERATE ASSISTANT RESPONSE ----------
    if client:
        with st.chat_message("assistant"):

            placeholder = st.empty()
            full_response = ""

            stream = client.chat.completions.create(
                model=model,
                messages=context_messages,
                temperature=temp,
                max_tokens=max_tokens,
                stream=True
            )

            finish_reason = None

            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                full_response += content
                finish_reason = chunk.choices[0].finish_reason
                placeholder.markdown(full_response + "▌")

            continue_count = 0
            MAX_CONTINUE = 3

            while finish_reason == "length" and continue_count < MAX_CONTINUE:
                continue_count += 1
                continuation_messages = context_messages + [{
                    "role": "assistant",
                    "content": full_response[-2000:]
                }]

                stream = client.chat.completions.create(
                    model=model,
                    messages=continuation_messages,
                    temperature=temp,
                    max_tokens=max_tokens,
                    stream=True
                )

                for chunk in stream:
                    content = chunk.choices[0].delta.content or ""
                    full_response += content
                    finish_reason = chunk.choices[0].finish_reason
                    placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)
            st.session_state.last_response=full_response
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response
        })

# ---------------- BUTTONS SIDE BY SIDE ----------------
if st.session_state.last_prompt and st.session_state.last_response:

    c1, c2, c3, c4, c5 = st.columns([4, 4, 1.3, 1.3, 1.5])

    # -------- Speak Button --------
    with c3:
        if st.button("🔊 Speak"):
            
            # Voice mapping
            voice_map = {
                "Default": "en-US-AriaNeural",
                "English Male": "en-US-GuyNeural",
                "English Female": "en-US-AriaNeural",
                
                "Hindi Female": "hi-IN-SwaraNeural"
            }
            selected_voice = voice_map.get(st.session_state.voice_settings["voice"], "en-US-AriaNeural")

            # Rate conversion: edge-tts uses percentage (default 0%)
            # Slider 80–300 -> rate -50% to +50% roughly
            # Rate mapping to edge-tts percentage
            rate_map = {
                            "High": "+90%",    # fast speech
                            "Normal": "+1%",   # normal speed (0% kabhi invalid hota hai)
                            "Slow": "-30%"   # slower speech
                        }
            selected_rate_percent = rate_map.get(st.session_state.voice_settings["rate"], "1%")

            tts_file = "temp_response.mp3"

            async def generate_tts(text, filename, voice, rate):
                communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
                await communicate.save(filename)

            asyncio.run(generate_tts(
                st.session_state.last_response,
                tts_file,
                selected_voice,
                selected_rate_percent
            ))

            with open(tts_file, "rb") as f:
                audio_bytes = f.read()

            b64 = base64.b64encode(audio_bytes).decode()

            st.markdown(
                f"""
                <audio autoplay controls>
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """,
                unsafe_allow_html=True
            )

    # -------- Regenerate Button --------
    with c4:
        if st.button("🔄Regrte", key="regen_btn"):
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
                st.session_state.messages.pop()

            st.session_state.regen = True
            st.rerun()


