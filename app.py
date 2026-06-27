import streamlit as st
import urllib.request
import json
import re
from youtube_transcript_api import YouTubeTranscriptApi

# Set konfigurasi halaman & tema dasar dark dengan branding baru
st.set_page_config(
    page_title="FTBL7 Labs", 
    page_icon="⚡", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# RE-DESIGN TOTAL: Injeksi CSS Kustom Meniru Nuansa Premium
st.markdown("""
    <style>
    /* Mengubah latar belakang utama menjadi dark navy/charcoal */
    .stApp {
        background-color: #0B0F19;
        color: #F3F4F6;
    }
    
    /* Mengubah gaya teks input */
    .stTextInput > div > div > input {
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
        border: 1px solid #374151 !important;
        border-radius: 30px !important;
        padding: 12px 24px !important;
    }
    
    /* Mengubah gaya text area manual input */
    .stTextArea > div > div > textarea {
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
        border: 1px solid #374151 !important;
        border-radius: 16px !important;
    }
    
    /* Tombol Utama: Blue Electric Accent */
    div.stButton > button:first-child {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border-radius: 30px !important;
        width: 100%;
        font-weight: 700;
        border: none !important;
        padding: 14px 28px !important;
        font-size: 16px !important;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    div.stButton > button:first-child:hover {
        background-color: #1D4ED8 !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
        transform: translateY(-1px);
    }

    /* Kotak Hasil Momen Konten (Card Style Modern) */
    .moment-box {
        background: linear-gradient(145deg, #1E293B, #0F172A);
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .moment-title {
        color: #FFFFFF;
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .moment-meta {
        color: #94A3B8;
        font-size: 14px;
        line-height: 1.6;
    }
    .moment-hook {
        color: #38BDF8;
        font-weight: 600;
        background-color: rgba(56, 189, 248, 0.1);
        padding: 4px 8px;
        border-radius: 6px;
        display: inline-block;
        margin-top: 8px;
    }
    
    /* Banner Informasi Khusus (Info/Warning Box Style) */
    .custom-info {
        background-color: #111827;
        border-left: 4px solid #F59E0B;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Session State Initializer
if "saved_url" not in st.session_state: st.session_state.saved_url = None
if "start_time" not in st.session_state: st.session_state.start_time = 0
if "clips_data" not in st.session_state: st.session_state.clips_data = None
if "show_manual_input" not in st.session_state: st.session_state.show_manual_input = False

# Engine API Key via Secrets
gemini_key = st.secrets.get("GEMINI_API_KEY", None)

def get_video_id(url):
    url = url.strip()
    patterns = [
        r'(?:v=|\/v\/|embed\/|\/shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?youtu\.be\/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match: return match.group(1)
    return None

def fetch_youtube_data(video_id):
    title = "Video Konten Bola"
    try:
        info_url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}"
        with urllib.request.urlopen(info_url) as res:
            info = json.loads(res.read().decode())
            title = info.get("title", "Video Konten Bola")
    except:
        pass

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['id', 'en'])
        full_text = "\n".join([f"[{int(float(i['start']))}] {i['text']}" for i in transcript_list])
        return title, full_text
    except:
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
            text = res['candidates'][0]['content']['parts'][0]['text'].replace("```json", "").replace("