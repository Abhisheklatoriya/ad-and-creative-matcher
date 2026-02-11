import streamlit as st
from pptx import Presentation
import re
import json
import io
import os

st.set_page_config(page_title="Ad Matcher - Session Sync", layout="wide")

# --- 1. LIGHTWEIGHT PPTX EXTRACTOR ---
@st.cache_data
def get_pptx_info(file_bytes):
    prs = Presentation(io.BytesIO(file_bytes))
    slides_data = []
    for slide in prs.slides:
        text = "\n".join([sh.text.strip() for sh in slide.shapes if hasattr(sh, "text")])
        codes = re.findall(r'\b\d{8}\b', text)
        if codes:
            slides_data.append({"codes": codes, "text": text})
    return slides_data

# --- 2. ASSET INDEXER (SAVES FILENAMES ONLY) ---
@st.cache_resource
def index_assets(uploaded_files):
    # Store filename -> bytes mapping
    return {f.name: f.getvalue() for f in uploaded_files if not f.name.endswith('.pptx') and not f.name.endswith('.json')}

st.title("🧠 Ad Matcher: Session Brain")

with st.sidebar:
    st.header("1. Upload Data")
    pptx_file = st.file_uploader("Upload MediaRadar PPTX", type=['pptx'])
    asset_files = st.file_uploader("Upload Assets (Multiple)", accept_multiple_files=True)
    
    st.divider()
    st.header("2. Sync Session")
    # This is where your colleague uploads the tiny file you sent them
    session_file = st.file_uploader("Upload 'session_work.json'", type=['json'])

if pptx_file and asset_files:
    slides = get_pptx_info(pptx_file.read())
    asset_map = index_assets(asset_files)
    all_codes = sorted(list(set([c for s in slides for c in s['codes']])))

    # Initialize session state for notes/work
    if session_file:
        st.session_state.notes = json.load(session_file)
        st.sidebar.success("✅ Session Brain Synced!")
    elif 'notes' not in st.session_state:
        st.session_state.notes = {}

    # --- THE "SAVE WORK" BUTTON ---
    st.sidebar.divider()
    st.sidebar.header("3. Save Progress")
    json_data = json.dumps(st.session_state.notes)
    st.sidebar.download_button(
        label="💾 Download session_work.json",
        data=json_data,
        file_name="session_work.json",
        mime="application/json",
        help="Send this tiny file to your colleague to share your progress."
    )

    # --- MAIN VIEW ---
    search = st.text_input("🔍 Search Ad Code", placeholder="Type 8-digit code...")
    display_codes = [c for c in all_codes if search in c] if search else all_codes[:10]

    for code in display_codes:
        # Automatic matching based on filename
        matches = [name for name in asset_map.keys() if code in name]
        slide_text = next((s['text'] for s in slides if code in s['codes']), "No details.")
        
        with st.expander(f"📦 Ad {code} ({len(matches)} files)"):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown("**PPTX Metadata**")
                st.caption(slide_content := st.session_state.notes.get(f"meta_{code}", slide_text))
                
                # Allow user to add persistent notes that get saved in the JSON
                user_note = st.text_area("Session Notes:", value=st.session_state.notes.get(code, ""), key=f"note_{code}")
                st.session_state.notes[code] = user_note
            
            with c2:
                for fname in matches:
                    st.write(f"📄 {fname}")
                    data = asset_map[fname]
                    ext = fname.split('.')[-1].lower()
                    if ext in ['mp4', 'mov']: st.video(data)
                    elif ext in ['jpg', 'png', 'jpeg']: st.image(data)
                    elif ext in ['mp3', 'wav']: st.audio(data)
                    st.divider()

else:
    st.info("Please upload your PPTX and Assets to begin.")
