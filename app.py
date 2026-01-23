import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #F1F3F5; border-right: 1px solid #DEE2E6; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E9ECEF; border-radius: 8px; }
    .player-card { border: 2px solid #E9ECEF; padding: 20px; border-radius: 15px; background: white; }
    .status-critical { color: #dc3545; font-weight: bold; font-size: 1.2em; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    current_year = 2026
    
    numeric_cols = ['market_value', 'age', 'pass_accuracy', 'dribble_success', 'interceptions', 
                    'positioning_rating', 'sprint_speed', 'stamina', 'composure', 'big_game_impact', 'contract_end_year']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*weights['Technical'] + df['Tact_Score']*weights['Tactical'] + 
                 df['Phys_Score']*weights['Physical'] + df['Ment_Score']*weights['Mental'])
    
    df['Transfer_Prob'] = ((df['TPI'] * 0.6) + (35 - df['age']) * 2) / 100
    df['Transfer_Prob'] = df['Transfer_Prob'].clip(0, 0.95)
    df['Years_Left'] = df['contract_end_year'] - current_year
    
    team_avg = {'Technical': df['Tech_Score'].mean(), 'Tactical': df['Tact_Score'].mean(),
                'Physical': df['Phys_Score'].mean(), 'Mental': df['Ment_Score'].mean()}
    return df, team_avg

# --- 2. THE EXECUTIVE PDF ENGINE (REFINED) ---
def generate_executive_pdf(p_data):
    pdf = FPDF()
    pdf.add_page()
    
    # Page 1: Corporate Branding Header
    pdf.set_fill_color(13, 27, 42) # Deep Navy
    pdf.rect(0, 0, 210, 50, 'F')
    pdf.set_font('Arial', 'B', 24); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 30, 'EXECUTIVE PLAYER DOSSIER', align='C', ln=True)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, -10, 'Strictly Confidential - RPL Scouting & Management', align='C', ln=True)
    
    # Profile Info
    pdf.ln(35); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 18)
    pdf.cell(0, 10, p_data['player_name'].upper(), ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 7, f"Club: {p_data.get('club')} | Nationality: {p_data.get('nationality')}", ln=True)
    pdf.cell(0, 7, f"Age: {int(p_data.get('age'))} | Career Minutes: {int(p_data.get('mins_played')):,} mins", ln=True)
    
    # Financials Row
    pdf.ln(10); pdf.set_fill_color(230, 230, 230); pdf.set_font('Arial', 'B', 12)
    pdf.cell(63, 12, "Market Valuation", 1, 0, 'C', True); pdf.cell(63, 12, "Contract Risk", 1, 0, 'C', True); pdf.cell(64, 12, "Transfer Prob", 1, 1, 'C', True)
    pdf.set_font('Arial', '', 14)
    pdf.cell(63, 12, f"${int(p_data['market_value']):,}", 1, 0, 'C'); 
    risk = "CRITICAL" if p_data['Years_Left'] <= 0 else f"{int(p_data['Years_Left'])} Years"
    pdf.cell(63, 12, risk, 1, 0, 'C'); 
    pdf.cell(64, 12, f"{int(p_data['Transfer_Prob']*100)}%", 1, 1, 'C')
    
    # Technical Matrix Table
    pdf.ln(10); pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "Technical Performance Matrix", ln=True)
    pdf.set_font('Arial', 'B', 11); pdf.set_fill_color(245, 245, 245)
    pdf.cell(70, 10, "KPI Pillar", 1, 0, 'L', True); pdf.cell(30, 10, "Score", 1, 1, 'C', True)
    pdf.set_font('Arial', '', 11)
    for m in ['Technical', 'Tactical', 'Physical', 'Mental']:
        pdf.cell(70, 10, m, 1); pdf.cell(30, 10, f"{p_data[m[:4]+'_Score']:.1f}", 1, 1, 'C')
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(70, 10, "Total Performance Index (TPI)", 1, 0, 'L', True); pdf.cell(30, 10, f"{p_data['TPI']:.1f}", 1, 1, 'C', True)

    # Managerial Verdict
    pdf.ln(10); pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, "TECHNICAL VERDICT:", ln=True)
    pdf.set_font('Arial', 'I', 11)
    verdict = f"{p_data['player_name']} represents a "
    verdict += "High-Value Asset " if p_data['TPI'] > 75 else "Squad Rotation Asset "
    verdict += f"with a {int(p_data['Transfer_Prob']*100)}% likelihood of market movement in the current window."
    pdf.multi_cell(0, 8, verdict)

    return pdf.output(dest='S').encode('latin-1')

# --- 3. MAIN APP ---
st.sidebar.title("💎 RPL ELITE")
file = st.sidebar.file_uploader("Upload Elite CSV", type="csv")

if file:
    df, team_avg = calculate_analytics(pd.read_csv(file))
    tabs = st.tabs(["👤 Profile", "📊 Performance Analysis", "📋 Squad Health", "🌍 Transfer War Room"])

    with tabs[0]:
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique(), key="prof_box")
        p_data = df[df['player_name'] == p_name].iloc[0]
        
        st.markdown('<div class="player-card">', unsafe_allow_html=True)
        c_l, c_p, c_t = st.columns([1, 1, 3])
        with c_l:
            if pd.notna(p_data.get('club_logo_url')) and p_data['club_logo_url'] != "":
                st.image(p_data['club_logo_url'], width=100)
        with c_p:
            if pd.notna(p_data.get('photo_url')) and p_data['photo_url'] != "":
                st.image(p_data['photo_url'], width=150)
            else: st.image("https://via.placeholder.com/150?text=Photo", width=150)
        with c_t:
            st.header(p_data['player_name'])
            st.subheader(f"{p_data.get('club')} | {p_data.get('nationality')}")
            st.write(f"**Contract:** {int(p_data['contract_end_year'])} | **Market Value:** ${int(p_data['market_value']):,}")
            if p_data['Years_Left'] <= 0:
                st.markdown('<span class="status-critical">⚠️ CONTRACT EXPIRED / EXPIRING SOON</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Action Bar
        col_pdf, col_spacer = st.columns([1, 2])
        with col_pdf:
            if st.button("📄 Generate Executive Dossier"):
                pdf_bytes = generate_executive_pdf(p_data)
                st.download_button("Download Report", pdf_bytes, f"{p_name}_Executive_Report.pdf")

    with tabs[1]:
        # Stability: Full Comparison logic
        col1, col2 = st.columns(2)
        with col1: p1_n = st.selectbox("Primary Player", df['player_name'].unique(), key="an_p1")
        with col2: compare = st.checkbox("Enable Comparison Mode", key="an_comp")
        p1_d = df[df['player_name'] == p1_n].iloc[0]
        cats = ['Technical', 'Tactical', 'Physical', 'Mental']
        fig = go.Figure()
        fig.add_trace(go.Bar(x=cats, y=[p1_d['Tech_Score'], p1_d['Tact_Score'], p1_d['Phys_Score'], p1_d['Ment_Score']], name=p1_n, marker_color='#212529'))
        fig.add_trace(go.Scatter(x=cats, y=[team_avg['Technical'], team_avg['Tactical'], team_avg['Physical'], team_avg['Mental']], mode='lines+markers', name='Team Average', line=dict(color='#007BFF', dash='dash')))
        if compare:
            p2_n = st.selectbox("Compare With", df['player_name'].unique(), index=1, key="an_p2")
            p2_d = df[df['player_name'] == p2_n].iloc[0]
            fig.add_trace(go.Bar(x=cats, y=[p2_d['Tech_Score'], p2_d['Tact_Score'], p2_d['Phys_Score'], p2_d['Ment_Score']], name=p2_n, marker_color='#D00000'))
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        st.header("⚠️ Medical Readiness Index")
        low_phys = df[df['Phys_Score'] < 65]
        if not low_phys.empty:
            for _, p in low_phys.iterrows():
                st.error(f"🚨 **INJURY RISK:** {p['player_name']} (Readiness: {p['Phys_Score']:.1f}%). Load: {int(p['mins_played']):,} mins.")
        else: st.success("Squad meeting all readiness standards.")

    with tabs[3]:
        st.subheader("Market War Room")
        display_df = df[['player_name', 'club', 'age', 'TPI', 'market_value', 'contract_end_year', 'Transfer_Prob']].copy()
        display_df['Transfer_Prob'] = display_df['Transfer_Prob'].apply(lambda x: f"{int(x*100)}%")
        display_df['market_value'] = display_df['market_value'].apply(lambda x: f"${int(x):,}")
        st.dataframe(display_df.sort_values(by='TPI', ascending=False), use_container_width=True)

else:
    st.info("Upload the finalized Executive CSV to proceed.")
