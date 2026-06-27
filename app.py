import streamlit as st
import urllib.request
import json
import re

# Set konfigurasi halaman & tema dasar dark dengan branding baru
st.set_page_config(
    page_title="FTBL7 Labs", 
    page_icon="⚡", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# RE-DESIGN TOTAL: Injeksi CSS Kustom Meniru Nuansa Premium Dark Mode
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

    # CARA BARU: Request menggunakan API server proxy publik agar tidak terblokir
    try:
        bypass_url = f"https://api.subtitles.me/api/transcript?v={video_id}"
        req = urllib.request.Request(
            bypass_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode())
            if "transcript" in data:
                full_text = "\n".join([f"[{int(float(i['start']))}] {i['text']}" for i in data["transcript"]])
                return title, full_text
    except:
        # Cadangan Endpoint Kedua jika API pertama sibuk
        try:
            backup_url = f"https://youtube-transcript-open.vercel.app/api/transcript?v={video_id}"
            with urllib.request.urlopen(backup_url, timeout=10) as res:
                data = json.loads(res.read().decode())
                if "transcript" in data:
                    full_text = "\n".join([f"[{int(float(i['start']))}] {i['text']}" for i in data["transcript"]])
                    return title, full_text
        except:
            return title, None
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
            text = res['candidates'][0]['content']['parts'][0]['text'].strip()
            
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            
            text = text.strip("` \n")
            return json.loads(text)
    except:
        return None

# --- TAMPILAN HEADER BRANDING ---
st.markdown("<h1 style='color: #FFFFFF; font-weight: 800; margin-bottom: 4px;'>🔬 FTBL7 Labs</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8; font-size: 15px; margin-bottom: 30px;'>Ready to find viral Shorts moments in seconds?</p>", unsafe_allow_html=True)

if not gemini_key: 
    gemini_key = st.text_input("🔑 Gemini API Key:", type="password")
url_input = st.text_input("🔗 Paste your YouTube video link below:", placeholder="https://youtu.be/...")

st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

if st.button("🔥 DETEKSI MOMEN VIRAL"):
    if not gemini_key:
        st.error("Masukkan API Key terlebih dahulu!")
    elif not url_input:
        st.error("Masukkan URL video terlebih dahulu!")
    else:
        v_id = get_video_id(url_input)
        if v_id:
            with st.spinner("Analyzing automated transcript map..."):
                title, trans = fetch_youtube_data(v_id)
                if trans:
                    results = analyze_with_gemini_dynamic(gemini_key, trans)
                    if results:
                        st.session_state.saved_url = url_input
                        st.session_state.clips_data = results
                        st.session_state.show_manual_input = False
                        st.rerun()
                    else:
                        st.error("Gemini gagal menyusun struktur JSON data.")
                else:
                    st.session_state.saved_url = url_input
                    st.session_state.show_manual_input = True
                    st.rerun()
        else:
            st.error("Format URL YouTube tidak dikenali.")

# Interface Cadangan (Muncul jika proxy publik di atas juga sedang penuh)
if st.session_state.show_manual_input:
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='custom-info'>
            ⚠️ <b>Automated System Overloaded.</b><br>
            Jika penarikan otomatis gagal, silakan gunakan metode manual: Buka video di YouTube -> Klik <b>'Show Transcript'</b> -> Salin teksnya dan taruh di bawah ini.
        </div>
    """, unsafe_allow_html=True)
    
    manual_trans = st.text_area("📋 Tempel teks transkrip di sini:", height=180, placeholder="[00:12] Coach Justin: Taktik mereka salah...")
    
    if st.button("🚀 ANALISIS TRANSKRIP MANUAL"):
        if manual_trans:
            with st.spinner("AI Agent @ftbl7talk sedang mengekstrak poin emosi tertinggi..."):
                results = analyze_with_gemini_dynamic(gemini_key, manual_trans)
                if results:
                    st.session_state.clips_data = results
                    st.session_state.show_manual_input = False
                    st.rerun()
                else:
                    st.error("Sistem AI gagal membedah teks tersebut.")
        else:
            st.error("Kotak transkrip tidak boleh kosong!")

# Panel Display Hasil Deteksi
if st.session_state.clips_data:
    st.markdown("<hr style='border-color: #1E293B;'>", unsafe_allow_html=True)
    
    try:
        raw_start = st.session_state.get("start_time", 0)
        start_seconds = int(raw_start) if raw_start is not None else 0
    except (ValueError, TypeError):
        start_seconds = 0

    st.video(st.session_state.saved_url, start_time=start_seconds, key=st.session_state.saved_url)
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    
    for clip in st.session_state.clips_data:
        try:
            detik = int(clip.get('timestamp_seconds', 0))
        except (ValueError, TypeError):
            detik = 0
            
        st.markdown(f"""
            <div class='moment-box'>
                <div class='moment-title'>🔥 [Rank {clip['rank']}] {clip['title']}</div>
                <div class='moment-meta'>{clip['reason']}</div>
                <div class='moment-hook'>Hook: {clip['hook']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"🎬 Lompat ke Momen Detik {detik}", key=f"btn_{clip['rank']}"):
            st.session_state.start_time = detik
            st.rerun()