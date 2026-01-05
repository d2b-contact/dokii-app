import streamlit as st
import anthropic
import base64
import json
from datetime import datetime
import os

# ============================================
# CONFIGURATION & STYLE
# ============================================
st.set_page_config(
    page_title="Dokii - Vérification Intelligente",
    page_icon="📄",
    layout="centered"
)

# CSS personnalisé - Dark Mode élégant
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #2c3e50 0%, #4A6274 50%, #34495e 100%);
        color: #E8E8E8;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6, p, span, div, label { color: #E8E8E8 !important; }
    
    .dokii-title {
        font-family: 'Playfair Display', serif;
        font-size: 4.5rem;
        font-weight: 900;
        color: #FFFFFF !important;
        margin: 0;
        letter-spacing: -2px;
    }
    
    .stButton > button {
        background-color: #E6DACE !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    }
    
    .stButton > button:hover {
        background-color: #D4C4B8 !important;
        transform: translateY(-2px) !important;
    }
    
    /* Force text color inside buttons */
    div.stButton > button > div > p { color: #000000 !important; }
    
    .credit-badge {
        background: rgba(230, 218, 206, 0.15);
        border: 2px solid #E6DACE;
        border-radius: 20px;
        padding: 0.75rem 1.5rem;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    
    .credit-number { font-size: 1.8rem; font-weight: 700; color: #E6DACE; }
    .credit-text { font-size: 0.85rem; color: #B8B8B8; margin-top: 0.25rem; }
    
    .trust-badge {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 15px;
        padding: 1.25rem 0.75rem;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .trust-badge:hover { background: rgba(255, 255, 255, 0.12); transform: translateY(-3px); }
    .trust-icon { font-size: 2rem; margin-bottom: 0.5rem; }
    .trust-title { font-size: 0.95rem; font-weight: 600; color: #FFFFFF; }
    .trust-subtitle { font-size: 0.75rem; color: #B8B8B8; }
    
    .block-container {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(15px);
    }
    
    .block-title { font-size: 1.8rem; font-weight: 700; color: #E6DACE; margin-bottom: 1rem; }
    
    /* Override Streamlit elements */
    .stCheckbox { color: #E8E8E8; }
    .uploadedFile { background: rgba(230, 218, 206, 0.1) !important; border: 2px solid #E6DACE !important; border-radius: 15px !important; }
    .stAlert { border-radius: 15px !important; background: rgba(255, 255, 255
