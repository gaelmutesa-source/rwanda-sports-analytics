import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="ITARA Sports Analytics", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    .label-box { background-color: #EBF8FF; border-left: 5px solid #3182CE; padding: 12px; margin-bottom: 15px; border-radius: 4px; font-size: 0.9rem; }
    .preview-box { background-color: #1B263B; padding: 25px; border-radius: 15px; color: white; text-align: center; }
    .sidebar .sidebar-content { background-image: linear-gradient(#1B263B, #1B263B); color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ANALYTICS ENGINE ---
def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    numeric_cols = ['pass_accuracy', 'dribble_success', 'interceptions', 'positioning_rating', 
                    'sprint_speed', 'stamina', 'composure', 'big_game_impact', 'market_value', 
                    'age', 'contract_end_year', 'mins_played', 'goals', 'assists',
                    'tpi_m1', 'tpi_m2', 'tpi_m3', 'tpi_m4', 'tpi_m5']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0
            
    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*0.35 + df['Tact_Score']*0.25 + df['Phys_Score']*0.25 + df['Ment_Score']*0.15)
    
    avg_val_tpi = df['market_value'].sum() / df['TPI'].sum() if df['TPI'].sum() > 0 else 0
    df['Leakage'] = (df['market_value'] - (df['TPI'] * avg_val_tpi)).clip(lower=0)
    
    team_avg = {'Tech': df['Tech_Score'].mean(), 'Tact': df['Tact_Score'].mean(), 
                'Phys': df['Phys_Score'].mean(), 'Ment': df['Ment_Score'].mean(), 'TPI': df['TPI'].mean()}
    return df, team_avg

# --- 3. ITARA SIGNED PDF ENGINE ---
def generate_pdf(df, club_name, win_p, rec, leakage_total):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Executive Header
    pdf.set_fill_color(27, 38, 59)
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 22)
    pdf.cell(190, 20, txt="STRATEGIC PERFORMANCE AUDIT", ln=True, align='L')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 5, txt="OFFICIAL DATA PROVIDER: ITARA SPORTS ANALYTICS", ln=True, align='L')
    pdf.cell(190, 5, txt=f"CONFIDENTIAL FOR: {club_name.upper()}", ln=True, align='L')
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(20)
    
    # 2. Strategic Table
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt="I. STRATEGIC STANDING & FINANCIAL LEAKAGE", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(95, 10, "Assessment Category", 1, 0, 'C', True)
    pdf.cell(95, 10, "Value / Strategic Direction", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 10, "Win Probability (Next Match)", 1, 0, 'C')
    pdf.cell(95, 10, f"{win_p}%", 1, 1, 'C')
    pdf.cell(95, 10, "Recommended Tactical Block", 1, 0, 'C')
    pdf.cell(95, 10, rec, 1, 1, 'C')
    pdf.cell(95, 10, "Total Squad Capital Inefficiency", 1, 0, 'C')
    pdf.cell(95, 10, f"${int(leakage_total):,}", 1, 1, 'C')
    
    pdf.ln(10)

    # 3. Squad Performance Table
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt="II. INDIVIDUAL PLAYER AUDIT", ln=True)
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(60, 10, "NAME", 1, 0, 'C', True)
    pdf.cell(30, 10, "TPI INDEX", 1, 0, 'C', True)
    pdf.cell(35, 10, "MARKET VAL", 1, 0, 'C', True)
    pdf.cell(30, 10, "G/A", 1, 0, 'C', True)
    pdf.cell(35, 10, "READINESS", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 8)
    club_df = df[df['club'] == club_name].sort_values(by='TPI', ascending=False)
    for _, row in club_df.iterrows():
        health = "STABLE" if row['Phys_Score'] >= 65 else "CRITICAL"
        pdf.cell(60, 8, row['player_name'], 1, 0, 'L')
        pdf.cell(30, 8, f"{row['TPI']:.1f}", 1, 0, 'C')
        pdf.cell(35, 8, f"${int(row['market_value']):,}", 1, 0, 'C')
        pdf.cell(30, 8, f"{int(row['goals'])}/{int(row['assists'])}", 1, 0, 'C')
        pdf.cell(35, 8, health, 1, 1, 'C')

    # 4. Footer, Copyright & ITARA Signature
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(190, 5, txt="Disclaimer: This data is proprietary property of ITARA Sports Analytics. Unauthorized duplication or distribution is prohibited by Rwandan IP Law 2026.")
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(95, 10, "Authorized Signature (ITARA Chief Analyst):", 0, 0, 'L')
    pdf.cell(95, 10, "__________________________", 0, 1, 'R')
    
    pdf.set_font("Arial", '', 8)
    pdf.cell(190, 10, txt=f"© 2026 ITARA SPORTS ANALYTICS - All Rights Reserved.", ln=True, align='C')

    return pdf.output(dest='S').encode('latin-1')

# --- 4. APP INTERFACE ---
st.sidebar.title("💎 ITARA ELITE")
uploaded_file = st.sidebar.file_uploader("Upload Client CSV", type="csv")

if 'df' not in st.session_state:
    st.session_state.df = None

if uploaded_file is not None:
    st.session_state.df = pd.read_csv(uploaded_file)
elif st.sidebar.button("Sync with Cloud Database"):
    try:
        st.session_state.df = pd.read_csv("https://raw.githubusercontent.com/Marclon11/Data/main/rpl_master_data.csv")
    except:
        st.sidebar.error("Cloud Error.")

if st.session_state.df is not None:
    df, team_avg = calculate_analytics(st.session_state.df)
    tabs = st.tabs(["📊 Comparison", "📋 Health", "🔥 Match Day", "📈 Progress", "💎 ITARA Audit"])

    with tabs[2]:
        st.header("🔥 Match Command")
        c_m1, c_m2 = st.columns(2)
        my_club = c_m1.selectbox("My Club", df['club'].unique(), key="m1")
        opponent = c_m2.selectbox("Opponent", [c for c in df['club'].unique() if c != my_club], key="m2")
        xi_tpi = df[df['club'] == my_club]['TPI'].mean()
        opp_tpi = df[df['club'] == opponent]['TPI'].mean()
        win_p = round(50 + (xi_tpi - opp_tpi) * 3, 1)
        st.markdown(f'<div class="preview-box"><h1>{win_p}%</h1><p>Win Prob vs {opponent}</p></div>', unsafe_allow_html=True)
        st.session_state.last_win_p = win_p

    with tabs[4]:
        st.header("💎 ITARA Executive Briefing")
        rep_club = st.selectbox("Select Club for Formal Audit", df['club'].unique(), key="rep_c")
        if st.button("Generate Signed ITARA PDF"):
            wp = st.session_state.get('last_win_p', 50.0)
            leak = df[df['club'] == rep_club]['Leakage'].sum()
            rec = "Defensive low block focus." if wp < 55 else "High-intensity technical press."
            pdf_bytes = generate_pdf(df, rep_club, wp, rec, leak)
            st.download_button("📥 Download Official ITARA Audit", data=pdf_bytes, file_name=f"{rep_club}_ITARA_Official_Audit.pdf")

else:
    st.info("Upload CSV to activate ITARA Sports Analytics Suite.")
