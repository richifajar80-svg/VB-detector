import streamlit as st
import urllib.request
import json
import re
from youtube_transcript_api import YouTubeTranscriptApi

# Set konfigurasi halaman
st.set_page_config(page_title="VB-Detector | @ftbl7talk", page_icon="⚽", layout="centered")

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #FFFFFF; }
    div.stButton > button:first-child {
        background-color: #1E40AF; color: white; border-radius: 8px;
        width: 100%; font-weight: bold; border: none; padding: 12px;
    }
    .moment-box {
        background-color: #F8FAFC; border-left: 5px solid #1E40AF;
        padding: 15px; border-radius: 0 8px 8px 0; margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Engine API Key
if "GEMINI_API_KEY" in st.secrets:
    gemini_key = st.secrets["GEMINI_API_KEY"]
else:
    gemini_key = None

# Session State Initializer
if "saved_url" not in st.session_state: st.session_state.saved_url = None
if "start_time" not in st.session_state: st.session_state.start_time = 0
if "clips_data" not in st.session_state: st.session_state.clips_data = None

def get_video_id(url):
    url = url.strip()
    patterns = [
        r'(?:v=|\/v\/|embed\/|\/shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?youtu\.be\/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_youtube_data(video_id):
    title = "Video Konten Bola"
    # 1. Ambil Judul via NoEmbed (Aman & Ringan)
    try:
        info_url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}"
        with urllib.request.urlopen(info_url) as res:
            info = json.loads(res.read().decode())
            title = info.get("title", "Video Konten Bola")
    except:
        pass

    # 2. Ambil Transkrip Langsung Menggunakan Library Resmi Python
    try:
        # Mencoba mengambil transkrip bahasa Indonesia ('id') atau bahasa Inggris ('en')
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['id', 'en'])
        full_text = "\n".join([f"[{int(float(i['start']))}] {i['text']}" for i in transcript_list])
        return title, full_text
    except Exception as e:
        return title, None

def analyze_with_gemini_dynamic(api_key, transcript_text):
    if not transcript_text: return None
    full_scanned_transcript = transcript_text[:220000]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    Kamu adalah AI Clip Detector untuk channel YouTube Shorts @ftbl7talk. Tugasmu menganalisis transkrip video dan menentukan 5 klip paling potensial viral, diranking dari yang paling kuat.
    
    Konteks channel:
    - Konten: klip dari Coach Justin (Justinus Lhaksana), analis sepak bola Indonesia yang dikenal blak-blakan dan kontroversial.
    - Audiens: pria Indonesia, 25–34 tahun, mobile aktif.
    - Trigger terkuat: pernyataan kontroversial Coach Justin, topik Timnas Indonesia, naturalisasi, reaksi emosional tokoh terkenal.

    Kriteria pemilihan klip:
    - Durasi ideal 30–90 detik per klip.
    - Harus mengandung pernyataan mengejutkan, kontroversial, panas, atau emosional tinggi.
    - Kalimat pertama klip harus langsung "memukul" (high hook strength) — tidak butuh konteks intro yang panjang.
    - Sangat relevan dengan dinamika kultur suporter sepak bola di Indonesia.

    Berikut adalah transkrip lengkap video:
    {full_scanned_transcript}

    Wajib berikan jawaban HANYA dalam format JSON Array mentah berisi TEPAT 5 data objek:
    [
      {{
        "rank": 1,
        "title": "DRAFT JUDUL SHORTS (Maksimal 60 karakter)",
        "timestamp_seconds": 120,
        "score": "98%",
        "hook": "Hook kalimat pertama untuk caption Shorts",
        "reason": "Kutipan Kunci: '...' Alasan: '...'"
      }}
    ]
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    body = json.dumps(data).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            text = res['candidates'][0]['content']['parts'][0]['text'].replace("```json", "").replace("```", "").strip()
            return json.loads(text)
    except:
        return None

# UI
st.markdown("<h1 style='text-align: center;'>⚽ VB-Detector</h1>", unsafe_allow_html=True)
if not gemini_key: gemini_key = st.text_input("🔑 Gemini API Key:", type="password")
url_input = st.text_input("🔗 Link YouTube:")

if st.button("🔥 DETEKSI MOMEN VIRAL"):
    if not gemini_key:
        st.error("Masukkan API Key terlebih dahulu!")
    elif not url_input:
        st.error("Masukkan URL video terlebih dahulu!")
    else:
        v_id = get_video_id(url_input)
        if v_id:
            with st.spinner("Agent @ftbl7talk membedah video..."):
                title, trans = fetch_youtube_data(v_id)
                if trans:
                    results = analyze_with_gemini_dynamic(gemini_key, trans)
                    if results:
                        st.session_state.saved_url = url_input
                        st.session_state.clips_data = results
                        st.rerun()
                    else:
                        st.error("Gemini gagal memproses data JSON. Coba klik lagi.")
                else:
                    st.error("Transkrip gagal ditarik oleh sistem internal. Pastikan video memiliki subtitle resmi/otomatis dari YouTube.")
        else:
            st.error("Format URL YouTube tidak dikenali.")

# Display
if st.session_state.clips_data:
    st.markdown("---")
    st.video(st.session_state.saved_url, start_time=int(st.session_state.start_time), key=st.session_state.saved_url)
    
    for clip in st.session_state.clips_data:
        detik = int(clip.get('timestamp_seconds', 0))
        with st.container():
            st.markdown(f"<div class='moment-box'>🎯 <b>{clip['title']}</b><br>{clip['reason']}<br><i>Hook: {clip['hook']}</i></div>", unsafe_allow_html=True)
            if st.button(f"🎬 Lompat ke {detik} detik", key=f"btn_{clip['rank']}"):
                st.session_state.start_time = detik
                st.rerun()