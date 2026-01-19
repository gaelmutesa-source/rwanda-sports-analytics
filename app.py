import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- 1. CONFIGURATION & BRAINS ---
st.set_page_config(page_title="Rwanda Sports Analytics", layout="wide")

def calculate_tpi(df):
    """Proprietary KPI Calculation Logic"""
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    
    # Fill missing values with league average (50) to prevent crashes
    df = df.fillna(50)
    
    # Formulas (Adjust these as your IP grows)
    df['Tech_Score'] = df.get('pass_accuracy', 50) * 0.6 + df.get('dribble_success', 50) * 0.4
    df['Tact_Score'] = (df.get('interceptions', 5) * 5) + (df.get('positioning_rating', 50) * 0.5)
    df['Phys_Score'] = (df.get('sprint_speed', 25) * 2) + (df.get('stamina', 50) * 0.2)
    df['Ment_Score'] = (df.get('composure', 70) * 0.7) + (df.get('big_game_impact', 50) * 0.3)
    
    df['TPI'] = (df['Tech_Score'] * weights['Technical'] + 
                 df['Tact_Score'] * weights['Tactical'] + 
                 df['Phys_Score'] * weights['Physical'] + 
                 df['Ment_Score'] * weights['Mental'])
    return df

def generate_pdf_report(player_data, radar_img_bytes):
    """Generates PDF using memory buffers to avoid Permission Errors"""
    pdf = FPDF()
    pdf.add_page()
    
    # Branding
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'RWANDA PERFORMANCE SCOUTING REPORT', ln=True, align='C')
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 10, 'Official Analytics Platform - 2025/26 Season', ln=True, align='C')
    pdf.line(10, 30, 200, 30)
    
    # Player Stats
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"PLAYER: {player_data['player_name'].upper()}", ln=True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Position: {player_data.get('position', 'Pro Player')}", ln=True)
    pdf.cell(0, 8, f"Total Performance Index (TPI): {player_data['TPI']:.1f} / 100", ln=True)
    
    # Insert Radar Image from Buffer
    # We save buffer to a temp name string that FPDF treats as a virtual file
    with open("temp_radar.png", "wb") as f:
        f.write(radar_img_bytes)
    pdf.image("temp_radar.png", x=110, y=45, w=85)
    
    # Pillar Breakdown
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 11)
    for pillar in ['Technical', 'Tactical', 'Physical', 'Mental']:
        score = player_data[f'{pillar[:4]}_Score'] # Matches Tech_Score, Tact_Score etc.
        pdf.cell(40, 10, f"{pillar}:", border=0)
        pdf.cell(20, 10, f"{score:.1f}", border=0, ln=True)

    return pdf.output(dest='S').encode('latin-1')

# --- 2. USER INTERFACE ---
st.title("⚽ Rwanda Football Analytics Platform")
uploaded_file = st.sidebar.file_uploader("Upload Player Data (CSV)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = calculate_tpi(df)
    
    selected_player = st.selectbox("Select Player to Analyze", df['
