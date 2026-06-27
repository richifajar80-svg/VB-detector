import streamlit as st
import urllib.request
import json
import re
from youtube_transcript_api import YouTubeTranscriptApi

# Set konfigurasi halaman
st.set_page_config(page_title="FTBL7 Labs", page_icon="⚡", layout="wide")

# CSS Kustom Premium
st.markdown("""
    <style>
    .stApp { background-color: #0B0F19; color: #F3F4F6; }
    .moment-box { background: linear-gradient(145deg, #1E293B, #0F172A); padding: 20px; border-radius: 16px; border: 1px solid #334155; margin-bottom: 20px; }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea { background-color: #1F2937 !important; color: #FFFFFF !important; border: 1px solid #374151 !important; border-radius: 30px !important; }
    div.stButton > button:first-child { background-color: #2563EB !important; color: #FFFFFF !important; border-radius: 30px !important; font-weight: 700; border: none !important; padding: 10px 20px !important; }
    </style>
""", unsafe_allow_html=True)

# Session State
if "saved_url" not in st.session_state: st.session_state.saved_url = None
if "clips_data" not in st.session_state: st.session_state.clips_data = None
if "show_manual_input" not in st.session_state: st.session_state.show_manual_input = False

gemini_key = st.secrets.get("GEMINI_API_KEY", None)

def get_video_id(url):
    match = re.search(r'(?:v=|\/shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None

def fetch_youtube_data_api(video_id):
    try:
        bypass_url = f"https://api.subtitles.me/api/transcript?v={video_id}"
        with urllib.request.urlopen(bypass_url, timeout=10) as res:
            data = json.loads(res.read().decode())
            if "transcript" in data:
                return "Video", "\n".join([f"[{int(float(i['start']))}] {i['text']}" for i in data["transcript"]])
    except:
        return "Video", None

def analyze_with_gemini(api_key, input_data, mode="detect"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    if mode == "detect":
        prompt = f"""Analisis transkrip ini dan berikan 5 klip viral. Berikan HANYA JSON Array mentah tanpa penjelasan lain.
        [ {{"rank":1, "title":"...", "timestamp_seconds":120, "reason":"...", "hooks":["hook1","hook2","hook3"]}} ]
        Transkrip: {input_data[:200000]}"""
    else:
        prompt = f"""Riset tren sentimen sepak bola untuk topik: "{input_data}". 
        Berikan HANYA JSON Array mentah:
        [ {{"topik": "...", "sentimen": "Positif/Negatif/Netral", "saran_konten": "..."}} ]"""
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode())
            raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
            
            # --- FILTER ANTI-GAGAL ---
            # Mencari lokasi [ dan ] untuk mengambil bagian JSON saja
            start = raw_text.find('[')
            end = raw_text.rfind(']') + 1
            if start != -1 and end != -1:
                clean_json = raw_text[start:end]
                return json.loads(clean_json)
            return None
    except Exception as e:
        st.error(f"Debug Eror: {e}") # Ini akan memunculkan eror asli di layar untuk mempermudah diagnosa
        return None

# --- SIDEBAR & NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["Clip Detector", "Trend & Sentiment"])

if menu == "Clip Detector":
    st.title("🔬 FTBL7 Labs - Clip Detector")
    api_key = st.text_input("Gemini API Key", type="password")
    url = st.text_input("YouTube URL:")
    
    if st.button("DETEKSI MOMEN VIRAL"):
        v_id = get_video_id(url)
        if v_id:
            with st.spinner("Menganalisis..."):
                _, trans = fetch_youtube_data_api(v_id)
                if trans:
                    data = analyze_with_gemini(api_key, trans, "detect")
                    st.session_state.clips_data = data
                else:
                    st.warning("Otomatis diblokir, silakan tempel transkrip manual.")
                    st.session_state.show_manual_input = True

    if st.session_state.get('clips_data'):
        for clip in st.session_state.clips_data:
            with st.container():
                st.markdown(f"<div class='moment-box'><h3>🔥 {clip['title']}</h3><p>{clip['reason']}</p>", unsafe_allow_html=True)
                cols = st.columns(3)
                for i, hook in enumerate(clip['hooks']):
                    cols[i].success(f"Hook {i+1}: {hook}")

elif menu == "Trend & Sentiment":
    st.title("📊 Trend & Sentiment Lab")
    api_key = st.text_input("Gemini API Key", type="password")
    
    # Input Keyword untuk riset spesifik
    keyword = st.text_input("Masukkan Keyword (Opsional):", placeholder="Contoh: Timnas Indonesia, Coach Justin...")
    
    if st.button("Update Trend"):
        if not api_key:
            st.error("Masukkan API Key terlebih dahulu!")
        else:
            with st.spinner(f"Menganalisis tren untuk: {keyword if keyword else 'Sepak Bola Indonesia'}..."):
                # Mengirim keyword ke dalam fungsi analyze_with_gemini
                data = analyze_with_gemini(api_key, keyword, "sentiment")
                if data:
                    st.success(f"Hasil Analisis untuk: {keyword if keyword else 'Tren Sepak Bola Indonesia'}")
                    st.table(data)
                else:
                    st.error("Gagal menarik data. Coba cek API Key atau coba lagi.")