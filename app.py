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
    
    avg_val_tpi = df['market_value'].sum() / df['TPI'].sum() if df['TPI'].sum() > 0 else 0
    df['Leakage'] = (df['market_value'] - (df['TPI'] * avg_val_tpi)).clip(lower=0)
    
    team_avg = {'Tech': df['Tech_Score'].mean(), 'Tact': df['Tact_Score'].mean(), 
                'Phys': df['Phys_Score'].mean(), 'Ment': df['Ment_Score'].mean(), 'TPI': df['TPI'].mean()}
    return df, team_avg

# --- 3. ITARA SIGNED PDF ENGINE ---
def generate_pdf(df, club_name, win_p, rec, leakage_total):
    pdf = FPDF()
    pdf.add_page()
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
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt="I. STRATEGIC STANDING & FINANCIAL LEAKAGE", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(95, 10, "Assessment Category", 1, 0, 'C', True)
    pdf.cell(95, 10, "Value / Strategic Direction", 1, 1, 'C', True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 10, "Win Probability", 1, 0, 'C'); pdf.cell(95, 10, f"{win_p}%", 1, 1, 'C')
    pdf.cell(95, 10, "Strategy", 1, 0, 'C'); pdf.cell(95, 10, rec, 1, 1, 'C')
    pdf.cell(95, 10, "Leaked Value", 1, 0, 'C'); pdf.cell(95, 10, f"${int(leakage_total):,}", 1, 1, 'C')
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt="II. SQUAD DATASET", ln=True)
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(60, 10, "NAME", 1, 0, 'C', True); pdf.cell(30, 10, "TPI", 1, 0, 'C', True)
    pdf.cell(35, 10, "VAL", 1, 0, 'C', True); pdf.cell(30, 10, "G/A", 1, 0, 'C', True); pdf.cell(35, 10, "HEALTH", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 8)
    club_df = df[df['club'] == club_name].sort_values(by='TPI', ascending=False)
    for _, row in club_df.iterrows():
        h = "FIT" if row['Phys_Score'] >= 65 else "AT RISK"
        pdf.cell(60, 8, row['player_name'], 1, 0, 'L'); pdf.cell(30, 8, f"{row['TPI']:.1f}", 1, 0, 'C')
        pdf.cell(35, 8, f"${int(row['market_value']):,}", 1, 0, 'C'); pdf.cell(30, 8, f"{int(row['goals'])}/{int(row['assists'])}", 1, 0, 'C'); pdf.cell(35, 8, h, 1, 1, 'C')

    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(190, 5, txt="© 2026 ITARA SPORTS ANALYTICS - Unauthorized distribution prohibited by Rwandan IP Law 2026.")
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(95, 10, "Authorized Signature:", 0, 0, 'L'); pdf.cell(95, 10, "__________________________", 0, 1, 'R')

    return pdf.output(dest='S').encode('latin-1')

# --- 4. DATA HANDLING ---
st.sidebar.title("💎 ITARA ELITE")
uploaded_file = st.sidebar.file_uploader("Upload Data", type="csv")

if 'df' not in st.session_state: st.session_state.df = None

if uploaded_file is not None:
    st.session_state.df = pd.read_csv(uploaded_file)
elif st.sidebar.button("Sync with Cloud"):
    try: st.session_state.df = pd.read_csv("https://raw.githubusercontent.com/Marclon11/Data/main/rpl_master_data.csv")
    except: st.sidebar.error("Cloud Error.")

if st.session_state.df is not None:
    df, team_avg = calculate_analytics(st.session_state.df)
    tabs = st.tabs(["👤 Profile", "📊 Comparison", "📋 Health", "🔥 Match Day", "📈 Progress", "💎 ITARA Audit"])

    with tabs[0]: # PROFILE RESTORED
        p_name = st.selectbox("Select Player", df['player_name'].unique(), key="prof")
        p_d = df.loc[df['player_name'] == p_name].iloc[0]
        st.markdown(f'<div class="player-card"><h2>{p_name}</h2>{p_d["club"]}</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Goals", int(p_d['goals'])); c2.metric("Assists", int(p_d['assists']))
        c3.metric("TPI", f"{p_d['TPI']:.1f}"); c4.metric("Value", f"${int(p_d['market_value']):,}")

    with tabs[1]: # COMPARISON RESTORED
        col1, col2 = st.columns(2)
        p1 = col1.selectbox("Player 1", df['player_name'].unique(), key="p1")
        comp_on = col2.checkbox("Compare Mode")
        fig_c = go.Figure()
        p1_d = df.loc[df['player_name'] == p1].iloc[0]
        fig_c.add_trace(go.Bar(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[p1_d['Tech_Score'], p1_d['Tact_Score'], p1_d['Phys_Score'], p1_d['Ment_Score']], name=p1))
        if comp_on:
            p2 = col2.selectbox("Player 2", df['player_name'].unique(), index=1, key="p2")
            p2_d = df.loc[df['player_name'] == p2].iloc[0]
            fig_c.add_trace(go.Bar(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[p2_d['Tech_Score'], p2_d['Tact_Score'], p2_d['Phys_Score'], p2_d['Ment_Score']], name=p2))
        fig_c.add_trace(go.Scatter(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[team_avg['Tech'], team_avg['Tact'], team_avg['Phys'], team_avg['Ment']], mode='lines+markers', name='Avg', line=dict(dash='dash')))
        st.plotly_chart(fig_c, use_container_width=True)

    with tabs[2]: # HEALTH RESTORED
        risks = df[df['Phys_Score'] < 65]
        if not risks.empty:
            for _, r in risks.iterrows(): st.error(f"🚨 **Risk:** {r['player_name']} ({r['Phys_Score']:.1f}%)")
        else: st.success("✅ Squad Fit")
        st.plotly_chart(px.scatter(df, x="Phys_Score", y="TPI", text="player_name", color="TPI"), use_container_width=True)

    with tabs[3]: # MATCH DAY RESTORED
        st.header("🔥 Win Probability")
        cm1, cm2 = st.columns(2)
        my_c = cm1.selectbox("My Club", df['club'].unique(), key="mc")
        opp_c = cm2.selectbox("Opponent", [c for c in df['club'].unique() if c != my_c], key="oc")
        xi_tpi = df[df['club'] == my_c]['TPI'].mean()
        opp_tpi = df[df['club'] == opp_c]['TPI'].mean()
        win_p = round(50 + (xi_tpi - opp_tpi) * 3, 1)
        st.markdown(f'<div class="preview-box"><h1>{win_p}%</h1><p>Win Prob vs {opp_c}</p></div>', unsafe_allow_html=True)
        st.session_state.wp = win_p

    with tabs[4]: # PROGRESS RESTORED
        st.header("📈 Seasonal Trend")
        f_p = st.selectbox("Track Player", df['player_name'].unique(), key="tp")
        f_d = df.loc[df['player_name'] == f_p].iloc[0]
        st.plotly_chart(px.line(x=["M-5", "M-4", "M-3", "M-2", "Last"], y=[f_d['tpi_m5'], f_d['tpi_m4'], f_d['tpi_m3'], f_d['tpi_m2'], f_d['tpi_m1']], markers=True), use_container_width=True)

    with tabs[5]: # ITARA AUDIT PDF RESTORED
        st.header("💎 ITARA Executive Briefing")
        r_club = st.selectbox("Report Club", df['club'].unique(), key="rc")
        if st.button("Generate Signed Audit"):
            leak = df[df['club'] == r_club]['Leakage'].sum()
            pdf_b = generate_pdf(df, r_club, st.session_state.get('wp', 50.0), "Maintain Technical Shape", leak)
            st.download_button("📥 Download Signed ITARA Audit", data=pdf_b, file_name=f"{r_club}_Audit.pdf")
else: st.info("Load Data to activate.")
