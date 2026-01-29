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

def generate_pdf(df, club_name, win_p, rec):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Executive Audit: {club_name}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt=f"Win Probability: {win_p}% | Recommendation: {rec}", ln=True)
    pdf.ln(5)
    club_df = df[df['club'] == club_name].sort_values(by='TPI', ascending=False)
    for _, row in club_df.iterrows():
        pdf.cell(190, 8, txt=f"{row['player_name']} - TPI: {row['TPI']:.1f} - Value: ${int(row['market_value']):,}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 2. DATA HANDLING ---
st.sidebar.title("💎 RPL ELITE")
uploaded_file = st.sidebar.file_uploader("1. Upload Local Data", type="csv")

if 'df' not in st.session_state:
    st.session_state.df = None

if uploaded_file is not None:
    st.session_state.df = pd.read_csv(uploaded_file)
elif st.sidebar.button("2. Sync with Cloud Database"):
    try:
        st.session_state.df = pd.read_csv("https://raw.githubusercontent.com/Marclon11/Data/main/rpl_master_data.csv")
    except:
        st.sidebar.error("Cloud unavailable.")

if st.session_state.df is not None:
    df, team_avg = calculate_analytics(st.session_state.df)
    tabs = st.tabs(["👤 Profile", "📊 Comparison", "📋 Health", "🔥 Match Day", "📈 Progress", "💎 Executive Report"])

    # --- TAB 1: PROFILE ---
    with tabs[0]:
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique(), key="prof_v_locked")
        p_d = df.loc[df['player_name'] == p_name].iloc[0]
        st.markdown(f'<div class="player-card"><h2>{p_name}</h2>{p_d["club"]}</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Goals", int(p_d['goals']))
        c2.metric("Assists", int(p_d['assists']))
        c3.metric("TPI Index", f"{p_d['TPI']:.1f}")
        c4.metric("Value", f"${int(p_d['market_value']):,}")

    # --- TAB 2: COMPARISON ---
    with tabs[1]:
        st.markdown('<div class="label-box">💡 Compare players or benchmark against the <b>League Average Line</b>.</div>', unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        p1 = col_c1.selectbox("Primary Player", df['player_name'].unique(), key="comp_p1_final")
        enable_p2 = col_c2.checkbox("Enable Comparison Mode", key="enable_p2_final")
        
        p1_d = df.loc[df['player_name'] == p1].iloc[0]
        fig_c = go.Figure()
        fig_c.add_trace(go.Bar(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[p1_d['Tech_Score'], p1_d['Tact_Score'], p1_d['Phys_Score'], p1_d['Ment_Score']], name=p1, marker_color='#212529'))
        
        if enable_p2:
            p2 = col_c2.selectbox("Compare With", df['player_name'].unique(), index=1, key="comp_p2_final")
            p2_d = df.loc[df['player_name'] == p2].iloc[0]
            fig_c.add_trace(go.Bar(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[p2_d['Tech_Score'], p2_d['Tact_Score'], p2_d['Phys_Score'], p2_d['Ment_Score']], name=p2, marker_color='#D00000'))
        
        fig_c.add_trace(go.Scatter(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[team_avg['Tech'], team_avg['Tact'], team_avg['Phys'], team_avg['Ment']], mode='lines+markers', name='League Avg', line=dict(dash='dash', color='#007BFF'), marker=dict(symbol='diamond', size=10)))
        st.plotly_chart(fig_c, use_container_width=True)

    # --- TAB 3: HEALTH ---
    with tabs[2]:
        risks = df[df['Phys_Score'] < 65]
        if not risks.empty:
            for _, r in risks.iterrows(): st.error(f"🚨 **Injury Risk:** {r['player_name']} ({r['Phys_Score']:.1f}%)")
        else: st.success("✅ All players fit.")
        st.plotly_chart(px.scatter(df, x="Phys_Score", y="TPI", text="player_name", color="TPI"), use_container_width=True)

    # --- TAB 4: MATCH DAY ---
    with tabs[3]:
        st.header("🔥 Match Command Center")
        col_m1, col_m2 = st.columns(2)
        my_club = col_m1.selectbox("Select Your Club", df['club'].unique(), key="m_c_final")
        opponent = col_m2.selectbox("Select Opponent", [c for c in df['club'].unique() if c != my_club], key="m_o_final")
        
        xi_tpi = df[df['club'] == my_club]['TPI'].mean()
        opp_tpi = df[df['club'] == opponent]['TPI'].mean()
        win_p = round(50 + (xi_tpi - opp_tpi) * 3, 1)
        
        st.markdown(f'<div class="preview-box"><h1>{win_p}%</h1><p>Win Probability vs {opponent}</p></div>', unsafe_allow_html=True)
        # Store for PDF report
        st.session_state.current_win_p = win_p

    # --- TAB 5: PROGRESS ---
    with tabs[4]:
        st.header("📈 Seasonal Form Progress")
        f_name = st.selectbox("Track Player Form", df['player_name'].unique(), key="f_t_final")
        f_d = df.loc[df['player_name'] == f_name].iloc[0]
        history = [f_d['tpi_m5'], f_d['tpi_m4'], f_d['tpi_m3'], f_d['tpi_m2'], f_d['tpi_m1']]
        st.plotly_chart(px.line(x=["M-5", "M-4", "M-3", "M-2", "Last Match"], y=history, markers=True, title=f"Trend: {f_name}"), use_container_width=True)

    # --- TAB 6: EXECUTIVE PDF ---
    with tabs[5]:
        st.header("💎 Executive Performance Report")
        rep_club = st.selectbox("Select Club for Report", df['club'].unique(), key="rep_c_final")
        if st.button("Generate Strategy PDF"):
            wp = st.session_state.get('current_win_p', 50.0)
            pdf_b = generate_pdf(df, rep_club, wp, "Maintain tactical discipline and physical load management.")
            st.download_button("📥 Download Report", data=pdf_b, file_name=f"{rep_club}_Strategy.pdf")

else:
    st.info("Upload CSV or Sync Cloud to activate the Elite Analytics Suite.")
