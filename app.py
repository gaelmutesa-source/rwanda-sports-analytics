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
    .status-critical { color: #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    current_year = 2026
    
    numeric_cols = ['pass_accuracy', 'dribble_success', 'interceptions', 'positioning_rating', 
                    'sprint_speed', 'stamina', 'composure', 'big_game_impact', 'market_value', 
                    'age', 'contract_end_year', 'mins_played', 'goals', 'assists',
                    'tpi_m1', 'tpi_m2', 'tpi_m3', 'tpi_m4', 'tpi_m5']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0
            
    # Core Scores
    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*0.35 + df['Tact_Score']*0.25 + df['Phys_Score']*0.25 + df['Ment_Score']*0.15)
    
    # Financial Leakage
    avg_val_per_tpi = df['market_value'].sum() / df['TPI'].sum() if df['TPI'].sum() > 0 else 0
    df['Leakage'] = (df['market_value'] - (df['TPI'] * avg_val_per_tpi)).clip(lower=0)
    
    team_avg = {'Tech': df['Tech_Score'].mean(), 'Tact': df['Tact_Score'].mean(), 
                'Phys': df['Phys_Score'].mean(), 'Ment': df['Ment_Score'].mean(), 'TPI': df['TPI'].mean()}
    return df, team_avg

def generate_pdf(df, club_name, win_prob, recommendation):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Elite Executive Briefing: {club_name}", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Strategy Date: {pd.to_datetime('today').strftime('%Y-%m-%d')}", ln=True, align='C')
    
    # Financial Audit
    club_df = df[df['club'] == club_name]
    total_leak = club_df['Leakage'].sum()
    pdf.ln(10)
    pdf.set_fill_color(200, 0, 0); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 10, txt=f" FINANCIAL AUDIT: ${int(total_leak):,} LEAKED VALUE", ln=True, fill=True)
    
    # Tactical Summary
    pdf.ln(5); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt=f"Tactical Command (Win Prob: {win_prob}%)", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(190, 7, txt=f"Recommendation: {recommendation}")
    
    # Squad Table
    pdf.ln(5); pdf.set_font("Arial", 'B', 10)
    pdf.cell(80, 8, "Player", 1); pdf.cell(30, 8, "TPI", 1); pdf.cell(40, 8, "Market Val", 1); pdf.cell(40, 8, "Health", 1); pdf.ln()
    pdf.set_font("Arial", size=9)
    for _, row in club_df.sort_values(by='TPI', ascending=False).iterrows():
        h = "FIT" if row['Phys_Score'] >= 65 else "RISK"
        pdf.cell(80, 7, row['player_name'], 1); pdf.cell(30, 7, f"{row['TPI']:.1f}", 1)
        pdf.cell(40, 7, f"${int(row['market_value']):,}", 1); pdf.cell(40, 7, h, 1); pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

# --- 2. RESTORED UPLOAD & DATA LOGIC ---
st.sidebar.title("💎 RPL ELITE")
uploaded_file = st.sidebar.file_uploader("Upload Client CSV", type="csv")

if 'df' not in st.session_state:
    st.session_state.df = None

if uploaded_file is not None:
    st.session_state.df = pd.read_csv(uploaded_file)
    st.sidebar.success("✅ Client Data Loaded")
elif st.sidebar.button("Load Cloud Database"):
    try:
        st.session_state.df = pd.read_csv("https://raw.githubusercontent.com/Marclon11/Data/main/rpl_master_data.csv")
        st.sidebar.success("✅ Cloud Sync Active")
    except:
        st.sidebar.error("Cloud Connection Failed")

if st.session_state.df is not None:
    df, team_avg = calculate_analytics(st.session_state.df)
    tabs = st.tabs(["👤 Profile", "📊 Comparison", "📋 Health", "🔥 Match Day", "📈 Progress", "💎 Executive Report"])

    with tabs[0]: # Profile with full metrics
        p_name = st.selectbox("Select Player", df['player_name'].unique(), key="prof_l")
        p_d = df.loc[df['player_name'] == p_name].iloc[0]
        st.markdown(f'<div class="player-card"><h2>{p_name}</h2>{p_d["club"]} | {p_d["nationality"]}</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Goals", int(p_d['goals']))
        c2.metric("Assists", int(p_d['assists']))
        c3.metric("TPI Index", f"{p_d['TPI']:.1f}")
        c4.metric("Value", f"${int(p_d['market_value']):,}")

    with tabs[1]: # Comparison with labels & benchmark
        st.markdown('<div class="label-box">💡 Compare pillars to the <b>Dashed Benchmark Line</b> to see elite traits.</div>', unsafe_allow_html=True)
        p1 = st.selectbox("Player", df['player_name'].unique(), key="c1")
        p1_d = df.loc[df['player_name'] == p1].iloc[0]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[p1_d['Tech_Score'], p1_d['Tact_Score'], p1_d['Phys_Score'], p1_d['Ment_Score']], name=p1))
        fig.add_trace(go.Scatter(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[team_avg['Tech'], team_avg['Tact'], team_avg['Phys'], team_avg['Ment']], mode='lines+markers', name='Avg', line=dict(dash='dash')))
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]: # Health with restored alerts
        st.header("📋 Health & Injury Alerts")
        st.markdown('<div class="label-box">💡 High performers with low Physical Scores are at <b>Critical Burnout Risk</b>.</div>', unsafe_allow_html=True)
        risks = df[df['Phys_Score'] < 65]
        if not risks.empty:
            for _, r in risks.iterrows(): st.error(f"🚨 **Injury Alert:** {r['player_name']} ({r['Phys_Score']:.1f}%)")
        else: st.success("✅ No players currently at risk.")
        st.plotly_chart(px.scatter(df, x="Phys_Score", y="TPI", text="player_name", color="TPI"), use_container_width=True)

    with tabs[5]: # Executive PDF Report
        st.header("💎 Consultant Report Generator")
        rep_club = st.selectbox("Report Club", df['club'].unique(), key="rep_c")
        
        # Simple Tactical Logic
        xi_tpi = df[df['club'] == rep_club]['TPI'].mean()
        win_p = round(50 + (xi_tpi - df['TPI'].mean()) * 2, 1)
        rec = "Focus on squad rotation to manage injury risks." if not risks[risks['club']==rep_club].empty else "Aggressive offensive press recommended."
        
        pdf_bytes = generate_pdf(df, rep_club, win_p, rec)
        st.download_button("📥 Download Executive Audit (PDF)", data=pdf_bytes, file_name=f"{rep_club}_Report.pdf")

else:
    st.info("👋 Welcome Consultant. Please upload a Client CSV or load the Cloud Database to begin.")
