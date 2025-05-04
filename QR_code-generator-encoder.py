import streamlit as st
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from PIL import Image
import cv2
import numpy as np
import io
import tempfile
import os
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="QR Code Generator & Scanner",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-bottom: 1rem;
    }
    .success-text {
        color: #4CAF50;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F8F9FA;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #E3F2FD;
        border-bottom: 2px solid #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# App title
st.markdown('<h1 class="main-header">🔍 QR Code Generator & Scanner</h1>', unsafe_allow_html=True)

# Create tabs
tab1, tab2 = st.tabs(["📝 Generate QR Code", "🔍 Decode QR Code"])

# Tab 1: Generate QR Code
with tab1:
    st.markdown('<h2 class="sub-header">Generate QR Code</h2>', unsafe_allow_html=True)
    
    # Create two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # QR Code settings
        qr_data = st.text_area("Enter text or URL:", height=100, 
                              placeholder="Enter the content you want to encode in the QR code")
        
        # QR Code options
        st.subheader("QR Code Options")
        
        # Size and border
        col_size, col_border = st.columns(2)
        with col_size:
            qr_size = st.slider("Size:", min_value=1, max_value=20, value=10, 
                              help="Controls the size of the QR code")
        with col_border:
            qr_border = st.slider("Border:", min_value=0, max_value=10, value=4, 
                                help="Controls the border width around the QR code")
        
        # Error correction
        error_correction = st.selectbox(
            "Error Correction:",
            ["L (7%)", "M (15%)", "Q (25%)", "H (30%)"],
            index=1,
            help="Higher error correction allows the QR code to be readable even if partially damaged"
        )
        
        # Colors
        col_fill, col_back = st.columns(2)
        with col_fill:
            fill_color = st.color_picker("Fill Color:", "#000000")
        with col_back:
            back_color = st.color_picker("Background Color:", "#FFFFFF")
        
        # Generate button
        if st.button("Generate QR Code", type="primary", use_container_width=True):
            if not qr_data:
                st.error("Please enter text or URL to generate QR code.")
            else:
                # Get error correction level
                error_level = error_correction[0]
                error_dict = {
                    'L': ERROR_CORRECT_L,
                    'M': ERROR_CORRECT_M,
                    'Q': ERROR_CORRECT_Q,
                    'H': ERROR_CORRECT_H
                }
                
                # Create QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=error_dict.get(error_level, ERROR_CORRECT_M),
                    box_size=qr_size,
                    border=qr_border
                )
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                # Create image
                qr_image = qr.make_image(fill_color=fill_color, back_color=back_color)
                
                # Convert to bytes for display
                img_byte_arr = io.BytesIO()
                qr_image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                # Store in session state for download
                st.session_state.qr_image = qr_image
                st.session_state.qr_bytes = img_byte_arr.getvalue()
                st.session_state.show_qr = True
    
    with col2:
        # QR Code display
        st.subheader("QR Code Preview")
        
        if 'show_qr' in st.session_state and st.session_state.show_qr:
            st.image(st.session_state.qr_bytes, caption="Generated QR Code", use_container_width=True)
            
            # Download button
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"qrcode_{timestamp}.png"
            
            st.download_button(
                label="Download QR Code",
                data=st.session_state.qr_bytes,
                file_name=filename,
                mime="image/png",
                use_container_width=True
            )
            
            # Display encoded data
            st.info(f"Encoded data: {qr_data[:50]}{'...' if len(qr_data) > 50 else ''}")
        else:
            st.info("QR code preview will appear here after generation.")
            # Placeholder image
            st.image("https://via.placeholder.com/300x300?text=QR+Code+Preview", use_container_width=True)

# Tab 2: Decode QR Code
with tab2:
    st.markdown('<h2 class="sub-header">Decode QR Code</h2>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload an image containing a QR code", 
                                     type=["jpg", "jpeg", "png", "bmp", "gif"])
    
    if uploaded_file is not None:
        # Create two columns
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)
        
        with col2:
            # Process the image with OpenCV instead of pyzbar
            try:
                # Save to temp file for OpenCV processing
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    tmp_filename = tmp_file.name
                    image.save(tmp_filename)
                
                # Read with OpenCV
                img = cv2.imread(tmp_filename)
                
                # Initialize QR code detector
                qr_detector = cv2.QRCodeDetector()
                
                # Detect and decode
                decoded_data, bbox, _ = qr_detector.detectAndDecode(img)
                
                # Display results
                if decoded_data:
                    st.markdown('<p class="success-text">QR Code detected!</p>', unsafe_allow_html=True)
                    st.subheader("Decoded Data:")
                    
                    # Create a text area with the decoded data
                    decoded_text = st.text_area("", value=decoded_data, height=150, key="decoded_data")
                    
               
                    if st.button("Copy to Clipboard", use_container_width=True):
                        st.code(decoded_data)
                        st.success("Copied to clipboard! (You can select and copy the text above)")
                    
                    # If it looks like a URL, offer to open it
                    if decoded_data.startswith(('http://', 'https://', 'www.')):
                        st.markdown(f"[Open URL]({decoded_data})")
                else:
                    st.error("No QR code detected in the image.")
                
                # Clean up temp file
                os.unlink(tmp_filename)
                
            except Exception as e:
                st.error(f"Error processing image: {str(e)}")

# Sidebar
with st.sidebar:
    st.title("About")
    st.markdown("""
    This app allows you to:
    - Generate QR codes with custom settings
    - Decode QR codes from uploaded images
    
    ### How to use
    1. Select the tab for the function you want to use
    2. Follow the instructions on each tab
    3. Download or copy the results as needed
    
    ### Technologies Used
    - Streamlit
    - qrcode
    - OpenCV
    - PIL (Pillow)
    """)
    
    st.markdown("---")
    st.markdown("Developed by Rafiha Siddiqui 🚀")




print("Change")