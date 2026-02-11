import streamlit as st
from pptx import Presentation
import re
import zipfile
import io
import os

st.set_page_config(page_title="Ad Matcher - Stable Build", layout="wide")

# 1. Memory-Efficient PPTX Parser
@st.cache_data
def extract_data_from_pptx(file_bytes):
    try:
        prs = Presentation(io.BytesIO(file_bytes))
        full_slides_data = []
        all_codes = []
        for slide in prs.slides:
            text_chunks = [shape.text.strip() for shape in slide.shapes if hasattr(shape, "text")]
            combined_text = "\n".join(text_chunks)
            codes = re.findall(r'\b\d{8}\b', combined_text)
            if codes:
                all_codes.extend(codes)
                full_slides_data.append({"codes": codes, "text": combined_text})
        return sorted(list(set(all_codes))), full_slides_data
    except Exception as e:
        return [], []

# 2. Optimized Asset Loader
@st.cache_resource
def load_assets_smart(uploaded_files):
    assets = []
    pptx_info = {"data": None, "name": None}
    
    for uploaded_file in uploaded_files:
        name = uploaded_file.name.lower()
        if name.endswith('.pptx'):
            pptx_info["data"] = uploaded_file.getvalue()
            pptx_info["name"] = uploaded_file.name
        elif name.endswith('.zip'):
            with zipfile.ZipFile(uploaded_file) as z:
                for info in z.infolist():
                    if info.is_dir() or "__MACOSX" in info.filename: continue
                    with z.open(info) as f:
                        content = f.read()
                        if info.filename.lower().endswith('.pptx'):
                            pptx_info["data"] = content
                            pptx_info["name"] = info.filename
                        else:
                            assets.append({
                                "name": os.path.basename(info.filename),
                                "data": content,
                                "ext": info.filename.split('.')[-1].lower()
                            })
        else:
            assets.append({
                "name": uploaded_file.name,
                "data": uploaded_file.getvalue(),
                "ext": name.split('.')[-1].lower()
            })
    return pptx_info, assets

st.title("📦 Ad Matcher Session Sync")

# Use a single uploader for everything to save memory
files = st.file_uploader("Upload PPTX, Assets, or Session ZIP (Up to 1GB)", accept_multiple_files=True)

if files:
    pptx_info, all_assets = load_assets_smart(files)

    if pptx_info["data"]:
        ad_codes, slides_content = extract_data_from_pptx(pptx_info["data"])
        
        # Sidebar Export
        with st.sidebar:
            st.header("Session Management")
            if st.button("💾 Prepare Session Download"):
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
                    z.writestr(pptx_info["name"], pptx_info["data"])
                    for a in all_assets:
                        z.writestr(f"assets/{a['name']}", a['data'])
                st.download_button("Click to Download Zip", buf.getvalue(), "Session_Export.zip", "application/zip")
            
            if st.button("Clear App Cache"):
                st.cache_resource.clear()
                st.cache_data.clear()
                st.rerun()

        st.success(f"Ready! {len(ad_codes)} Ads | {len(all_assets)} Creatives")
        
        search = st.text_input("🔍 Search Ad Code", placeholder="e.g. 48735196")
        display_codes = [c for c in ad_codes if search in c] if search else ad_codes

        for code in display_codes:
            matches = [a for a in all_assets if code in a['name']]
            # Get text from the slide containing this code
            slide_text = next((s['text'] for s in slides_content if code in s['codes']), "No details found.")
            
            with st.expander(f"📦 Ad {code} ({len(matches)} files)"):
                c1, c2 = st.columns([1, 1.5])
                with c1:
                    st.markdown("**PPTX Metadata:**")
                    st.caption(slide_text)
                with c2:
                    for asset in matches:
                        st.write(f"📄 {asset['name']}")
                        if asset['ext'] in ['mp4', 'mov', 'webm']: st.video(asset['data'])
                        elif asset['ext'] in ['mp3', 'wav']: st.audio(asset['data'])
                        elif asset['ext'] in ['jpg', 'jpeg', 'png', 'gif']: st.image(asset['data'])
                        st.divider()
    else:
        st.warning("Please include a PowerPoint file in your upload.")
