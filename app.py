import streamlit as st
from pptx import Presentation
import re
import io
import pandas as pd

st.set_page_config(page_title="Ad Metadata Dashboard", layout="wide")

def extract_ad_data(file_bytes):
    """Extracts all ad metadata and links from the PPTX."""
    prs = Presentation(io.BytesIO(file_bytes))
    ads = []
    
    for slide in prs.slides:
        # Get all text from the slide
        text = "\n".join([sh.text.strip() for sh in slide.shapes if hasattr(sh, "text")])
        
        # Extract the Ad Code
        code_match = re.search(r'Ad Code:\s*(\d+)', text)
        if code_match:
            code = code_match.group(1)
            
            # Find the hyperlink attached to 'View Ad' or images
            link = "Link not found"
            for shape in slide.shapes:
                if shape.has_text_frame and "View Ad" in shape.text:
                    if shape.click_action.hyperlink.address:
                        link = shape.click_action.hyperlink.address
            
            # Map the other metadata fields
            ads.append({
                "Ad Code": code,
                "Brand": re.search(r'Brand:\s*(.*)', text).group(1) if "Brand:" in text else "N/A",
                "Media Outlet": re.search(r'Media Outlet:\s*(.*)', text).group(1) if "Media Outlet:" in text else "N/A",
                "Media Type": re.search(r'Media:\s*(.*)', text).group(1) if "Media:" in text else "N/A",
                "First Run": re.search(r'First Run Date:\s*(.*)', text).group(1) if "First Run Date:" in text else "N/A",
                "Link": link
            })
    return ads

st.title("📋 Ad Metadata & Link Dashboard")
st.markdown("Upload the MediaRadar PPTX to view a searchable list of all ads and their direct links.")

pptx_file = st.file_uploader("Upload PPTX Report", type=['pptx'])

if pptx_file:
    data = extract_ad_data(pptx_file.read())
    df = pd.DataFrame(data)
    
    # Dashboard Stats
    st.info(f"Successfully extracted {len(df)} ads from the report.")
    
    # Search and Filter
    search = st.text_input("🔍 Search by Brand or Ad Code")
    if search:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

    # Display Data
    for _, row in df.iterrows():
        with st.expander(f"📦 {row['Ad Code']} - {row['Brand']}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**Outlet:** {row['Media Outlet']}")
                st.write(f"**Type:** {row['Media Type']}")
                st.write(f"**First Run:** {row['First Run']}")
            with col2:
                st.link_button("🔗 View Creative on MediaRadar", row['Link'])

    # Export to CSV option
    st.download_button("📥 Export List to CSV", df.to_csv(index=False), "Ad_List.csv", "text/csv")
