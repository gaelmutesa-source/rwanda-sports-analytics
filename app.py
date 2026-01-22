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
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    # Safety Check: Ensure 'market_value' is treated as a float
    if 'market_value' in df.columns:
        df['market_value'] = pd.to_numeric(df['market_value'], errors='coerce').fillna(0)
    
    required = ['pass_accuracy', 'dribble_success', 'interceptions', 'positioning_rating', 
                'sprint_speed', 'stamina', 'composure', 'big_game_impact']
    for col in required:
        if col not in df.columns: df[col] = 50
    
    df_numeric = df.select_dtypes(include=['number'])
    df[df_numeric.columns] = df_numeric.fillna(0)
    
    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*weights['Technical'] + df['Tact_Score']*weights['Tactical'] + 
                 df['Phys_Score']*weights['Physical'] + df['Ment_Score']*weights['Mental'])
    
    team_avg = {
        'Technical': df['Tech_Score'].mean(), 'Tactical': df['Tact_Score'].mean(),
        'Physical': df['Phys_Score'].mean(), 'Mental': df['Ment_Score'].mean()
    }
    return df, team_avg

# --- 2. EXECUTIVE PDF ENGINE ---
def generate_pro_pdf(p_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(13, 27, 42) 
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font('Arial', 'B', 22); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 25, 'OFFICIAL PERFORMANCE DOSSIER', align='C', ln=True)
    pdf.ln(30); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"{str(p_data['player_name']).upper()}", ln=True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f"Club: {p_data.get('club', 'RPL Club')} | Career Minutes: {int(p_data.get('mins_played', 0))}", ln=True)
    pdf.cell(0, 7, f"Nationality: {p_data.get('nationality', 'N/A')} | Value: ${int(p_data['market_value']):,}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. MAIN APP ---
st.sidebar.title("💎 RPL ELITE")
file = st.sidebar.file_uploader("Upload CSV", type="csv")

if file:
    df, team_avg = calculate_analytics(pd.read_csv(file))
    tabs = st.tabs(["👤 Profile", "📊 Performance Analysis", "📋 Squad Health", "🌍 Global Ranking"])

    # --- TAB 1: PROFILE (LOGO INTEGRATED) ---
    with tabs[0]:
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique(), key="prof_box")
        p_data = df[df['player_name'] == p_name].iloc[0]
        
        st.markdown('<div class="player-card">', unsafe_allow_html=True)
        c_l, c_p, c_t = st.columns([1, 1, 3])
        with c_l:
            logo = p_data.get('club_logo_url')
            if pd.notna(logo) and logo != "": st.image(logo, width=100)
        with c_p:
            photo = p_data.get('photo_url')
            if pd.notna(photo) and photo != "": st.image(photo, width=150)
            else: st.image("https://via.placeholder.com/150?text=Photo", width=150)
        with c_t:
            st.header(p_data['player_name'])
            st.subheader(f"{p_data.get('club')} | {p_data.get('nationality')}")
            st.write(f"**Total Career Minutes:** {int(p_data.get('mins_played', 0))} mins")
        st.markdown('</div>', unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Goals", int(p_data.get('goals', 0)))
        m2.metric("Assists", int(p_data.get('assists', 0)))
        m3.metric("Valuation", f"${int(p_data['market_value']):,}")

        if st.button("📄 Export Official PDF"):
            pdf_data = generate_pro_pdf(p_data)
            st.download_button("Download Report", pdf_data, f"{p_name}_Report.pdf")

    # --- TAB 2: ANALYSIS (COMPARISON & BENCHMARKING) ---
    with tabs[1]:
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
        
        fig.update_layout(title="Performance Pillar Benchmarking", yaxis_title="Score (0-100)")
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 3: SQUAD HEALTH (INJURY ALERTS PRESERVED) ---
    with tabs[2]:
        st.header("⚠️ Medical Readiness Index")
        low_phys = df[df['Phys_Score'] < 65]
        if not low_phys.empty:
            for _, p in low_phys.iterrows():
                st.error(f"**INJURY RISK:** {p['player_name']} - Readiness: {p['Phys_Score']:.1f}%. High load: {int(p['mins_played'])} mins.")
        else: st.success("Squad meeting all readiness standards.")
        
        fig_sq = px.scatter(df, x="Phys_Score", y="TPI", text="player_name", color="TPI", title="Squad Talent Map")
        st.plotly_chart(fig_sq, use_container_width=True)

    # --- TAB 4: GLOBAL RANKING (MARKET VALUE FIXED) ---
    with tabs[3]:
        st.subheader("Global Squad Ranking")
        # Fixing the display: Format numeric column as currency for the view
        rank_df = df[['player_name', 'position', 'club', 'market_value', 'TPI', 'mins_played']].copy()
        rank_df['market_value'] = rank_df['market_value'].apply(lambda x: f"${int(x):,}")
        st.dataframe(rank_df.sort_values(by='TPI', ascending=False), use_container_width=True)

else:
    st.info("Upload the finalized Elite CSV to begin.")
