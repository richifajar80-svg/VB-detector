import streamlit as st
import urllib.request
import json
import re
from youtube_transcript_api import YouTubeTranscriptApi

st.set_page_config(page_title="FTBL7 Labs", page_icon="⚡", layout="wide")

# --- CSS PREMIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0F19; color: #F3F4F6; }
    .moment-box { background: linear-gradient(145deg, #1E293B, #0F172A); padding: 20px; border-radius: 16px; border: 1px solid #334155; margin-bottom: 20px; }
    .hook-btn { color: #38BDF8; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI UTAMA ---
def get_video_id(url):
    match = re.search(r'(?:v=|\/shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None

def analyze_with_gemini(api_key, transcript, mode="detect"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # Prompt Dinamis: Deteksi Klip + Hook Generator
    if mode == "detect":
        prompt = f"""Analisis transkrip ini dan berikan 5 klip viral. Untuk setiap klip, buatkan 3 opsi hook: (1) Kontroversial, (2) Emosional, (3) Pertanyaan.
        Format JSON: {{"clips": [{{"rank":1, "title":"...", "timestamp":120, "reason":"...", "hooks":["hook1","hook2","hook3"]}}]}}
        Transkrip: {transcript[:200000]}"""
    else:
        prompt = "Analisis sentimen sepak bola Indonesia terkini. Berikan daftar 5 topik terhangat, sentimen (Positif/Negatif), dan saran konten untuk FTBL7talk."

    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode())
            text = res_data['candidates'][0]['content']['parts'][0]['text'].strip("`json \n")
            return json.loads(text)
    except: return None

# --- SIDEBAR MENU ---
menu = st.sidebar.radio("Navigation", ["🔥 Clip Detector", "📊 Trend & Sentiment"])

if menu == "🔥 Clip Detector":
    st.title("🔬 FTBL7 Labs - Clip Detector")
    api_key = st.text_input("Gemini API Key", type="password")
    url = st.text_input("YouTube URL:")
    
    if st.button("DETEKSI"):
        v_id = get_video_id(url)
        if v_id:
            with st.spinner("Menganalisis..."):
                _, trans = fetch_youtube_data_api(v_id) # Gunakan fungsi fetch Anda
                data = analyze_with_gemini(api_key, trans, "detect")
                st.session_state.clips = data['clips']
        
    if 'clips' in st.session_state:
        for clip in st.session_state.clips:
            with st.container():
                st.markdown(f"<div class='moment-box'><h3>{clip['title']}</h3><p>{clip['reason']}</p>", unsafe_allow_html=True)
                cols = st.columns(3)
                for i, hook in enumerate(clip['hooks']):
                    cols[i].success(f"Hook {i+1}: {hook}")

elif menu == "📊 Trend & Sentiment":
    st.title("📊 Trend & Sentiment Lab")
    api_key = st.text_input("Gemini API Key", type="password")
    if st.button("Update Trend"):
        data = analyze_with_gemini(api_key, "Trend", "sentiment")
        st.write(data)

# Fungsi fetch_youtube_data_api bisa ditaruh di sini
def fetch_youtube_data_api(v_id):
    # Gunakan logika bypass yang kita buat sebelumnya
    return "Video", "Transkrip..."