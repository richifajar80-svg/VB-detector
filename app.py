import streamlit as st
import urllib.request
import json
import re

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
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def fetch_youtube_data(video_id):
    try:
        # Mengambil judul
        info_url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}"
        with urllib.request.urlopen(info_url) as res:
            info = json.loads(res.read().decode())
            title = info.get("title", "Video Konten Bola")
        
        # Mengambil transkrip dengan deteksi error lebih detail
        trans_url = f"https://kapeka.vercel.app/api/yt-transcript?v={video_id}"
        with urllib.request.urlopen(trans_url) as res:
            data = json.loads(res.read().decode())
            
            # Tambahan: Jika transkrip kosong, kita akan tahu alasannya
            if "transcript" in data and data["transcript"]:
                full_text = "\n".join([f"[{int(float(i['start']))}] {i['text']}" for i in data["transcript"]])
                return title, full_text
            else:
                st.warning(f"API berhasil dihubungi, tapi data transkrip kosong. Respon API: {data}")
                return title, None
    except Exception as e:
        st.error(f"Terjadi kesalahan saat menghubungi API transkrip: {e}")
        return "Video Konten Bola", None
    except:
        return "Video Konten Bola", None

def analyze_with_gemini_dynamic(api_key, transcript_text):
    if not transcript_text: return None
    # Potong teks secara aman
    full_scanned_transcript = transcript_text[:220000] if isinstance(transcript_text, str) else ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    Kamu adalah AI Clip Detector untuk @ftbl7talk. Tugasmu mencari 5 momen viral (kontroversial, emosional, hook kuat) dari transkrip ini:
    {full_scanned_transcript}

    Berikan JSON Array mentah (Tepat 5 data):
    [
      {{"rank": 1, "title": "Judul", "timestamp_seconds": 120, "score": "98%", "hook": "Caption", "reason": "Kutipan: '...' Alasan: '...'"}}
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
                    st.error("Gagal menganalisis. Coba link lain.")
            else:
                st.error("Transkrip tidak ditemukan pada video ini.")

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