import streamlit as st
from pptx import Presentation
import re
import zipfile
import io

st.set_page_config(page_title="Direct PPTX Ad Matcher", layout="wide")

@st.cache_data
def extract_data_from_pptx(file):
    """Parses PPTX slides to find Ad Codes and associated text blocks."""
    prs = Presentation(file)
    full_slides_data = []
    all_codes = []

    for i, slide in enumerate(prs.slides):
        slide_text = []
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                slide_text.append(shape.text.strip())
        
        combined_text = "\n".join(slide_text)
        # Find 8-digit codes (e.g., 48735196)
        codes = re.findall(r'\b\d{8}\b', combined_text)
        
        if codes:
            all_codes.extend(codes)
            full_slides_data.append({"codes": codes, "text": combined_text})
            
    return sorted(list(set(all_codes))), full_slides_data

@st.cache_resource
def load_assets(uploaded_files):
    """Processes individual files or ZIP folders into memory."""
    processed_assets = []
    for uploaded_file in uploaded_files:
        if uploaded_file.name.lower().endswith('.zip'):
            with zipfile.ZipFile(uploaded_file) as z:
                for file_info in z.infolist():
                    if file_info.is_dir() or "__MACOSX" in file_info.filename:
                        continue
                    with z.open(file_info) as f:
                        processed_assets.append({
                            "name": file_info.filename,
                            "data": f.read(),
                            "ext": file_info.filename.split('.')[-1].lower()
                        })
        else:
            processed_assets.append({
                "name": uploaded_file.name,
                "data": uploaded_file.getvalue(),
                "ext": uploaded_file.name.split('.')[-1].lower()
            })
    return processed_assets

st.title("⚡ Direct PPTX to Creative Matcher")

with st.sidebar:
    st.header("Upload Data")
    pptx_file = st.file_uploader("Upload PowerPoint Report", type=['pptx'])
    raw_files = st.file_uploader("Upload Assets (Individual or ZIP)", accept_multiple_files=True)
    if st.button("Reset App"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.rerun()

if pptx_file and raw_files:
    ad_codes, slides_content = extract_data_from_pptx(pptx_file)
    all_assets = load_assets(raw_files)

    st.success(f"Extracted {len(ad_codes)} Ad Codes from PowerPoint and loaded {len(all_assets)} assets.")
    
    search = st.text_input("🔍 Filter by Ad Code", placeholder="e.g. 48735196")
    display_codes = [c for c in ad_codes if search in c] if search else ad_codes

    for code in display_codes:
        # Find the specific text block from PPTX for this code
        relevant_text = next((item['text'] for item in slides_content if code in item['codes']), "Details not found.")
        # Find matching creative files
        matches = [a for a in all_assets if code in a['name']]
        
        with st.expander(f"📦 Ad Code: {code} ({len(matches)} files found)", expanded=True):
            col1, col2 = st.columns([1, 1.5])
            
            with col1:
                st.markdown("**Details from PPTX:**")
                # Clean up the display text for just this ad
                pattern = f"Ad Code: {code}.*?(?=Ad Code:|$)"
                clean_match = re.search(pattern, relevant_text, re.DOTALL)
                st.info(clean_match.group(0) if clean_match else relevant_text)

            with col2:
                if matches:
                    for asset in matches:
                        st.caption(f"File: {asset['name']}")
                        if asset['ext'] in ['mp4', 'mov', 'webm']:
                            st.video(asset['data'])
                        elif asset['ext'] in ['mp3', 'wav']:
                            st.audio(asset['data'])
                        elif asset['ext'] in ['jpg', 'jpeg', 'png', 'gif']:
                            st.image(asset['data'])
                        st.download_button("Download Asset", data=asset['data'], file_name=asset['name'], key=f"{code}_{asset['name']}")
                        st.divider()
                else:
                    st.warning("No creative file found with this Ad Code in the filename.")
else:
    st.info("Please upload the PPTX report and your assets to begin.")
