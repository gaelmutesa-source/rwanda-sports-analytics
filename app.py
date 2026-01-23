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
    .status-critical { color: #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    current_year = 2026
    
    # Core Numeric Safety
    numeric_cols = ['market_value', 'age', 'pass_accuracy', 'dribble_success', 'interceptions', 
                    'positioning_rating', 'sprint_speed', 'stamina', 'composure', 'big_game_impact', 
                    'contract_end_year', 'mins_played']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Pillar Calculations
    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*weights['Technical'] + df['Tact_Score']*weights['Tactical'] + 
                 df['Phys_Score']*weights['Physical'] + df['Ment_Score']*weights['Mental'])
    
    # Strategy Metrics
    df['Transfer_Prob'] = (((df['TPI'] * 0.6) + (35 - df['age']) * 2) / 100).clip(0, 0.95)
    df['Years_Left'] = df['contract_end_year'] - current_year
    
    team_avg = {
        'Technical': df['Tech_Score'].mean(),
        'Tactical': df['Tact_Score'].mean(),
        'Physical': df['Phys_Score'].mean(),
        'Mental': df['Ment_Score'].mean()
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
    pdf.cell(0, 7, f"Club: {p_data.get('club')} | Career Mins: {int(p_data.get('mins_played', 0))}", ln=True)
    pdf.cell(0, 7, f"Market Value: ${int(p_data['market_value']):,}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. MAIN DASHBOARD ---
st.sidebar.title("💎 RPL ELITE")
file = st.sidebar.file_uploader("Upload Elite CSV", type="csv")

if file:
    df, team_avg = calculate_analytics(pd.read_csv(file))
    tabs = st.tabs(["👤 Elite Profile", "📊 Comparison Analysis", "📋 Squad Health", "🌍 Transfer War Room"])

    # --- TAB 1: PROFILE ---
    with tabs[0]:
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique(), key="prof_1")
        p_d = df[df['player_name'] == p_name].iloc[0]
        
        st.markdown('<div class="player-card">', unsafe_allow_html=True)
        c_l, c_p, c_t = st.columns([1, 1, 3])
        with c_l:
            if pd.notna(p_d.get('club_logo_url')) and p_d['club_logo_url'] != "":
                st.image(p_d['club_logo_url'], width=100)
        with c_p:
            if pd.notna(p_d.get('photo_url')) and p_d['photo_url'] != "":
                st.image(p_d['photo_url'], width=150)
            else: st.image("https://via.placeholder.com/150?text=Photo", width=150)
        with c_t:
            st.header(p_name)
            st.subheader(f"{p_d.get('club')} | {p_d.get('nationality')}")
            st.write(f"**Total Career Minutes:** {int(p_d.get('mins_played', 0))} mins")
            if p_d['Years_Left'] <= 0:
                st.markdown('<span class="status-critical">⚠️ CONTRACT EXPIRED</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Goals", int(p_d.get('goals', 0)))
        m2.metric("Assists", int(p_d.get('assists', 0)))
        m3.metric("Valuation", f"${int(p_d['market_value']):,}")

        if st.button("📄 Export Pro PDF"):
            pdf = generate_pro_pdf(p_d)
            st.download_button("Download Now", pdf, f"{p_name}_Report.pdf")

    # --- TAB 2: COMPARISON ANALYSIS (TEAM AVG & COMPARISON MODE LOCKED) ---
    with tabs[1]:
        st.subheader("Performance Comparison & Benchmarking")
        col1, col2 = st.columns(2)
        with col1: p1_name = st.selectbox("Primary Player", df['player_name'].unique(), key="an_p1")
        with col2: compare_on = st.checkbox("Enable Comparison Mode", key="an_comp")
        
        p1_data = df[df['player_name'] == p1_name].iloc[0]
        cats = ['Technical', 'Tactical', 'Physical', 'Mental']
        
        fig = go.Figure()
        # Bar 1: Primary Player
        fig.add_trace(go.Bar(x=cats, y=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']], 
                             name=p1_name, marker_color='#212529'))
        
        if compare_on:
            p2_name = st.selectbox("Compare With", df['player_name'].unique(), index=1, key="an_p2")
            p2_data = df[df['player_name'] == p2_name].iloc[0]
            # Bar 2: Comparison Player
            fig.add_trace(go.Bar(x=cats, y=[p2_data['Tech_Score'], p2_data['Tact_Score'], p2_data['Phys_Score'], p2_data['Ment_Score']], 
                                 name=p2_name, marker_color='#D00000'))
        
        # Layered Line: Team Average (FORCED VISIBILITY)
        fig.add_trace(go.Scatter(
            x=cats, 
            y=[team_avg['Technical'], team_avg['Tactical'], team_avg['Physical'], team_avg['Mental']], 
            mode='lines+markers', 
            name='Team Average', 
            line=dict(color='#007BFF', width=4, dash='dash'),
            marker=dict(size=12, symbol='diamond')
        ))
        
        fig.update_layout(yaxis_range=[0,105], title="Benchmarking vs Squad Standard")
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 3: SQUAD HEALTH (INJURY ALERTS LOCKED) ---
    with tabs[2]:
        st.header("⚠️ Medical Readiness Index")
        low_phys = df[df['Phys_Score'] < 65]
        if not low_phys.empty:
            for _, p in low_phys.iterrows():
                st.error(f"🚨 **INJURY RISK:** {p['player_name']} - Readiness: {p['Phys_Score']:.1f}%. Career Load: {int(p['mins_played'])} mins.")
        else: st.success("Squad meeting all readiness standards.")
        
        fig_sq = px.scatter(df, x="Phys_Score", y="TPI", text="player_name", color="TPI", title="Squad Talent Map")
        st.plotly_chart(fig_sq, use_container_width=True)

    # --- TAB 4: TRANSFER WAR ROOM (OPPORTUNITY MAP LOCKED) ---
    with tabs[3]:
        st.subheader("Strategic Opportunity Mapping")
        
        fig_war = px.scatter(
            df, 
            x="contract_end_year", 
            y="TPI", 
            size="market_value", 
            color="Transfer_Prob",
            text="player_name",
            labels={"contract_end_year": "Contract Expiry", "TPI": "Performance (TPI)"},
            title="TPI vs. Contract Expiry (Bubble Size = Market Value)",
            height=600
        )
        fig_war.update_traces(textposition='top center')
        st.plotly_chart(fig_war, use_container_width=True)
        
        # Fixed Market Value Display in Ranking
        rank_df = df[['player_name', 'club', 'market_value', 'TPI', 'Transfer_Prob', 'contract_end_year']].copy()
        rank_df['market_value'] = rank_df['market_value'].apply(lambda x: f"${int(x):,}")
        st.dataframe(rank_df.sort_values(by='TPI', ascending=False), use_container_width=True)

else:
    st.info("Upload the finalized Elite CSV to activate all tabs.")
