import streamlit as st
import urllib.request
import json
import re

# Set konfigurasi halaman agar rapi di HP Android
st.set_page_config(page_title="VB-Detector | @ftbl7talk", page_icon="⚽", layout="centered")

# Kustomisasi CSS untuk nuansa Biru-Putih Premium Android
st.markdown("""
    <style>
    .main { background-color: #FFFFFF; }
    div.stButton > button:first-child {
        background-color: #1E40AF; color: white; border-radius: 8px;
        width: 100%; font-weight: bold; border: none; padding: 12px;
    }
    div.stButton > button:first-child:hover { background-color: #1D4ED8; }
    .stTextInput > div > div > input { border-radius: 8px; }
    .moment-box {
        background-color: #F8FAFC; border-left: 5px solid #1E40AF;
        padding: 15px; border-radius: 0 8px 8px 0; margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ADAPTIVE API KEY ENGINE (LOCAL & CLOUD)
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    gemini_key = st.secrets["GEMINI_API_KEY"]
else:
    gemini_key = None

# Inisialisasi memori permanen (Session State)
if "video_title" not in st.session_state:
    st.session_state.video_title = None
if "detected_moments" not in st.session_state:
    st.session_state.detected_moments = None
if "video_id" not in st.session_state:
    st.session_state.video_id = None

# Fungsi mengambil ID Video YouTube
def get_video_id(url):
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

# Fungsi mengambil judul & transkrip otomatis via API pihak ketiga (Multi-Jalur Cadangan)
def fetch_youtube_data(video_id):
    title = "Video Konten Bola"
    try:
        # Mengambil info video untuk judul asli
        info_url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}"
        req = urllib.request.Request(info_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            info_data = json.loads(response.read().decode())
            title = info_data.get("title", "Video Konten Bola")
    except:
        pass
        
    # JALUR UTAMA API TRANSKRIP
    try:
        transcript_url = f"https://kapeka.vercel.app/api/yt-transcript?v={video_id}"
        req_trans = urllib.request.Request(transcript_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_trans) as resp_trans:
            trans_data = json.loads(resp_trans.read().decode())
            
        if trans_data.get("success", False):
            full_text = ""
            for item in trans_data.get("transcript", []):
                text = item.get("text", "")
                start = int(float(item.get("start", 0)))
                full_text += f"[{start}] {text}\n"
            return title, full_text
    except:
        pass

    # JALUR CADANGAN API TRANSKRIP (Jika Jalur Utama Gagal/Limit)
    try:
        alt_url = f"https://subtitles-youtube.vercel.app/api/transcript?v={video_id}"
        req_alt = urllib.request.Request(alt_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_alt) as resp_alt:
            alt_data = json.loads(resp_alt.read().decode())
            if alt_data.get("success", False) or "transcript" in alt_data:
                full_text = ""
                for item in alt_data.get("transcript", []):
                    text = item.get("text", "")
                    start = int(float(item.get("start", 0)))
                    full_text += f"[{start}] {text}\n"
                return title, full_text
    except:
        pass

    return title, None

# Fungsi analisis Gemini dengan Otak Agent @ftbl7talk
def analyze_with_gemini(api_key, transcript_text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    Anda adalah AI Clip Detector untuk channel YouTube Shorts @ftbl7talk. Tugasmu menganalisis transkrip video dan menentukan 5 klip paling potensial viral, diranking dari yang paling kuat.
    
    Konteks channel:
    - Konten: klip dari Coach Justin (Justinus Lhaksana), analis sepak bola Indonesia yang dikenal blak-blakan dan kontroversial.
    - Audiens: pria Indonesia, 25–34 tahun, mobile aktif.
    - Trigger terkuat: pernyataan kontroversial Coach Justin, topik Timnas Indonesia, naturalisasi, reaksi emosional tokoh terkenal.

    Kriteria pemilihan klip:
    - Durasi ideal 30–90 detik per klip.
    - Harus mengandung pernyataan mengejutkan, kontroversial, panas, atau emosional tinggi.
    - Kalimat pertama klip harus langsung "memukul" (high hook strength) — tidak butuh konteks intro yang panjang.
    - Sangat relevan dengan dinamika kultur suporter sepak bola di Indonesia.

    Berikut adalah teks transkrip video yang harus Anda analisis (angka di dalam kurung siku adalah penanda waktu detik):
    {transcript_text}

    Berikan hasil analisis dalam format JSON murni tanpa markdown, tanpa tulisan ```json. Format harus berupa array berisi tepat 5 objek dengan struktur seperti ini:
    [
      {{
        "ranking": 1, 
        "detik": 120, 
        "judul": "TULIS DRAFT JUDUL SHORTS DISINI",
        "alasan": "Tulis detail alasan viral disini.",
        "caption": "Tulis hook kalimat pertama untuk caption Shorts disini.",
        "kutipan": "Tulis kutipan kalimat kunci paling krusial disini."
      }},
      {{
        "ranking": 2, 
        "detik": 450, 
        "judul": "TULIS DRAFT JUDUL SHORTS DISINI",
        "alasan": "Tulis detail alasan viral disini.",
        "caption": "Tulis hook kalimat pertama untuk caption Shorts disini.",
        "kutipan": "Tulis kutipan kalimat kunci paling krusial disini."
      }}
    ]
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    body = json.dumps(data).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            text_response = res_data['candidates'][0]['content']['parts'][0]['text']
            clean_text = text_response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
    except Exception:
        return None

# ==========================================
# APPLICATION UI
# ==========================================
st.markdown("<h1 style='text-align: center; margin-bottom: 4px;'>⚽ VB-Detector</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748B; font-size: 13px; margin-bottom: 24px;'>AI Clip Detector Engine for @ftbl7talk</p>", unsafe_allow_html=True)

with st.container():
    if not gemini_key:
        gemini_key = st.text_input("🔑 Masukkan Gemini API Key Anda:", type="password")
        
    youtube_url = st.text_input("🔗 Tempel Link YouTube Podcast Bola:", placeholder="[https://www.youtube.com/watch?v=](https://www.youtube.com/watch?v=)...")

if st.button("🔥 DETEKSI MOMEN VIRAL"):
    if not gemini_key:
        st.error("Silakan isi Gemini API Key terlebih dahulu!")
    elif not youtube_url:
        st.error("Silakan tempel link video YouTube terlebih dahulu!")
    else:
        v_id = get_video_id(youtube_url)
        if not v_id:
            st.error("Link YouTube tidak valid!")
        else:
            with st.spinner("🔄 @ftbl7talk Agent sedang membedah emosi video... Mohon tunggu..."):
                title, transcript = fetch_youtube_data(v_id)
                
                st.session_state.video_title = title
                st.session_state.video_id = v_id
                
                if not transcript:
                    st.error("Gagal mengambil transkrip otomatis. Pastikan video memiliki subtitle/transkrip aktif.")
                    st.session_state.detected_moments = None
                else:
                    results = analyze_with_gemini(gemini_key, transcript)
                    if results:
                        st.session_state.detected_moments = results
                    else:
                        st.error("Gemini gagal menganalisis secara akurat. Silakan coba lagi.")

# TAMPILKAN HASIL SECARA STABIL DARI MEMORI PERMANEN (SESSION STATE)
if st.session_state.video_title and st.session_state.video_id:
    st.markdown("---")
    st.markdown(f"### 🎬 Analisis Video: {st.session_state.video_title}")
    
    query_params = st.query_params
    start_seconds = 0
    if "t" in query_params:
        try:
            start_seconds = int(query_params["t"])
        except:
            start_seconds = 0

    # Perbaikan Sintaksis Jalur Video Utama (Bebas Eror MediaFileStorageError)
    st.video(f"[https://www.youtube.com/watch?v=](https://www.youtube.com/watch?v=){st.session_state.video_id}", start_time=start_seconds)

    if st.session_state.detected_moments:
        st.markdown("### 🏆 5 Nominasi Klip Viral Pilihan Agent")
        for moment in st.session_state.detected_moments:
            with st.container():
                st.markdown(f"""
                <div class="moment-box">
                    <h4 style='color: #1E40AF; margin-bottom: 6px;'>🎯 Rank {moment['ranking']} — Menit {moment['detik'] // 60}:{moment['detik'] % 60:02d}</h4>
                    <p><b>🎬 Draft Judul:</b> <code>{moment.get('judul', 'Belum ada judul')}</code></p>
                    <p style='font-size: 14px; color: #1E293B;'><b>📌 Kutipan Kunci:</b> <i>"{moment.get('kutipan', '-')}"</i></p>
                    <p style='font-size: 13px; color: #475569; margin-bottom: 4px;'><b>🔥 Alasan Viral:</b> {moment.get('alasan', '-')}</p>
                    <p style='font-size: 13px; color: #059669; margin-bottom: 0px;'><b>🪝 Hook Caption:</b> {moment.get('caption', '-')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🎬 Lompat ke Detik {moment['detik']}", key=f"btn_{moment['ranking']}"):
                    st.query_params["t"] = moment['detik']
                    st.rerun()