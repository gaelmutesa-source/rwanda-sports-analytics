import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    .player-card { border: 2px solid #E9ECEF; padding: 20px; border-radius: 15px; background: white; margin-bottom: 20px; }
    .label-box { background-color: #EBF8FF; border-left: 5px solid #3182CE; padding: 12px; margin-bottom: 15px; border-radius: 4px; font-size: 0.9rem; }
    .preview-box { background-color: #1B263B; padding: 25px; border-radius: 15px; color: white; text-align: center; }
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
    
    # Financial Logic
    avg_val_tpi = df['market_value'].sum() / df['TPI'].sum() if df['TPI'].sum() > 0 else 0
    df['Leakage'] = (df['market_value'] - (df['TPI'] * avg_val_tpi)).clip(lower=0)
    
    team_avg = {'Tech': df['Tech_Score'].mean(), 'Tact': df['Tact_Score'].mean(), 
                'Phys': df['Phys_Score'].mean(), 'Ment': df['Ment_Score'].mean(), 'TPI': df['TPI'].mean()}
    return df, team_avg

# --- 3. PROFESSIONAL PDF ENGINE ---
def generate_pdf(df, club_name, win_p, rec, leakage_total):
    pdf = FPDF()
    pdf.add_page()
    
    # Header Branding
    pdf.set_fill_color(33, 37, 41)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(190, 20, txt="STRATEGIC PERFORMANCE AUDIT", ln=True, align='L')
    pdf.set_font("Arial", '', 12)
    pdf.cell(190, 10, txt=f"CONFIDENTIAL REPORT: {club_name.upper()}", ln=True, align='L')
    
    # Reset Text Color
    pdf.set_text_color(0, 0, 0)
    pdf.ln(15)
    
    # Section 1: Executive Summary
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(49, 130, 206)
    pdf.cell(190, 10, txt="1. EXECUTIVE SUMMARY", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 11)
    summary_txt = (f"This audit provides a quantified evaluation of {club_name}'s current squad performance, "
                   f"market efficiency, and match-day readiness for the 2026 season.")
    pdf.multi_cell(190, 7, txt=summary_txt)
    pdf.ln(5)

    # Section 2: Tactical Command (Table)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt="TACTICAL PREVIEW & PROBABILITY", ln=True)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(248, 249, 250)
    pdf.cell(95, 10, "Metric", 1, 0, 'C', True)
    pdf.cell(95, 10, "Value / Recommendation", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 10, "Next Match Win Probability", 1, 0, 'C')
    pdf.cell(95, 10, f"{win_p}%", 1, 1, 'C')
    pdf.cell(95, 10, "Tactical Strategy", 1, 0, 'C')
    pdf.cell(95, 10, rec, 1, 1, 'C')
    pdf.cell(95, 10, "Financial Capital Leakage", 1, 0, 'C')
    pdf.cell(95, 10, f"${int(leakage_total):,}", 1, 1, 'C')
    
    pdf.ln(10)

    # Section 3: Detailed Squad Audit (Table)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt="SQUAD ANALYTICS DATASET", ln=True)
    
    # Table Header
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(233, 236, 239)
    pdf.cell(60, 10, "PLAYER NAME", 1, 0, 'C', True)
    pdf.cell(25, 10, "TPI INDEX", 1, 0, 'C', True)
    pdf.cell(35, 10, "MARKET VALUE", 1, 0, 'C', True)
    pdf.cell(35, 10, "GOALS/AST", 1, 0, 'C', True)
    pdf.cell(35, 10, "HEALTH STATUS", 1, 1, 'C', True)
    
    # Table Content
    pdf.set_font("Arial", '', 8)
    club_df = df[df['club'] == club_name].sort_values(by='TPI', ascending=False)
    for _, row in club_df.iterrows():
        health = "STABLE" if row['Phys_Score'] >= 65 else "CRITICAL"
        pdf.cell(60, 8, row['player_name'], 1, 0, 'L')
        pdf.cell(25, 8, f"{row['TPI']:.1f}", 1, 0, 'C')
        pdf.cell(35, 8, f"${int(row['market_value']):,}", 1, 0, 'C')
        pdf.cell(35, 8, f"{int(row['goals'])} / {int(row['assists'])}", 1, 0, 'C')
        pdf.cell(35, 8, health, 1, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- 4. STREAMLIT APP LOGIC ---
st.sidebar.title("💎 RPL ELITE")
uploaded_file = st.sidebar.file_uploader("Upload Client CSV", type="csv")

if 'df' not in st.session_state:
    st.session_state.df = None

if uploaded_file is not None:
    st.session_state.df = pd.read_csv(uploaded_file)
elif st.sidebar.button("Sync with Cloud"):
    try:
        st.session_state.df = pd.read_csv("https://raw.githubusercontent.com/Marclon11/Data/main/rpl_master_data.csv")
    except:
        st.sidebar.error("Cloud Error.")

if st.session_state.df is not None:
    df, team_avg = calculate_analytics(st.session_state.df)
    tabs = st.tabs(["👤 Profile", "📊 Comparison", "📋 Health", "🔥 Match Day", "📈 Progress", "💎 Executive Report"])

    with tabs[1]:
        col_c1, col_c2 = st.columns(2)
        p1 = col_c1.selectbox("Primary Player", df['player_name'].unique(), key="c1")
        p2_on = col_c2.checkbox("Compare Mode", key="p2_on")
        p1_d = df.loc[df['player_name'] == p1].iloc[0]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[p1_d['Tech_Score'], p1_d['Tact_Score'], p1_d['Phys_Score'], p1_d['Ment_Score']], name=p1, marker_color='#212529'))
        if p2_on:
            p2 = col_c2.selectbox("Compare With", df['player_name'].unique(), index=1, key="c2")
            p2_d = df.loc[df['player_name'] == p2].iloc[0]
            fig.add_trace(go.Bar(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[p2_d['Tech_Score'], p2_d['Tact_Score'], p2_d['Phys_Score'], p2_d['Ment_Score']], name=p2, marker_color='#D00000'))
        fig.add_trace(go.Scatter(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[team_avg['Tech'], team_avg['Tact'], team_avg['Phys'], team_avg['Ment']], mode='lines+markers', name='Avg', line=dict(dash='dash')))
        st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        st.header("🔥 Match Command")
        c_m1, c_m2 = st.columns(2)
        my_club = c_m1.selectbox("My Club", df['club'].unique(), key="m1")
        opponent = c_m2.selectbox("Opponent", [c for c in df['club'].unique() if c != my_club], key="m2")
        xi_tpi = df[df['club'] == my_club]['TPI'].mean()
        opp_tpi = df[df['club'] == opponent]['TPI'].mean()
        win_p = round(50 + (xi_tpi - opp_tpi) * 3, 1)
        st.markdown(f'<div class="preview-box"><h1>{win_p}%</h1><p>Win Prob vs {opponent}</p></div>', unsafe_allow_html=True)
        st.session_state.last_win_p = win_p

    with tabs[5]:
        st.header("💎 Executive Reporting")
        rep_club = st.selectbox("Club for Audit", df['club'].unique(), key="rc")
        if st.button("Generate Professional PDF"):
            wp = st.session_state.get('last_win_p', 50.0)
            leak = df[df['club'] == rep_club]['Leakage'].sum()
            rec = "Neutral block recommended." if wp < 55 else "Aggressive press recommended."
            pdf_bytes = generate_pdf(df, rep_club, wp, rec, leak)
            st.download_button("📥 Download Executive Report", data=pdf_bytes, file_name=f"{rep_club}_Audit_2026.pdf")

else:
    st.info("Upload CSV to activate.")
