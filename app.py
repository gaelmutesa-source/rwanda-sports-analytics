import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. UI & STYLING ---
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
    # Numeric conversion for all strategy-critical columns
    cols = ['pass_accuracy', 'dribble_success', 'interceptions', 'positioning_rating', 
            'sprint_speed', 'stamina', 'composure', 'big_game_impact', 'market_value', 
            'age', 'contract_end_year', 'mins_played', 'Transfer_Prob']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Core Pillars
    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*weights['Technical'] + df['Tact_Score']*weights['Tactical'] + 
                 df['Phys_Score']*weights['Physical'] + df['Ment_Score']*weights['Mental'])
    
    # Recalculate Transfer Prob and Contract Years
    df['Transfer_Prob'] = (((df['TPI'] * 0.6) + (35 - df['age']) * 2) / 100).clip(0, 0.95)
    df['Years_Left'] = df['contract_end_year'] - 2026
    
    team_avg = {
        'Technical': df['Tech_Score'].mean(),
        'Tactical': df['Tact_Score'].mean(),
        'Physical': df['Phys_Score'].mean(),
        'Mental': df['Ment_Score'].mean()
    }
    return df, team_avg

# --- 2. EXECUTIVE PDF ---
def generate_pro_pdf(p_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(13, 27, 42)
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font('Arial', 'B', 22); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 25, 'RPL SCOUTING EXECUTIVE REPORT', align='C', ln=True)
    pdf.ln(30); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, p_data['player_name'].upper(), ln=True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f"Club: {p_data.get('club')} | Valuation: ${int(p_data['market_value']):,}", ln=True)
    pdf.cell(0, 7, f"TPI Score: {p_data['TPI']:.1f} | Contract Ends: {int(p_data['contract_end_year'])}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. MAIN DASHBOARD ---
st.sidebar.title("💎 RPL ELITE")
file = st.sidebar.file_uploader("Upload CSV", type="csv")

if file:
    df, team_avg = calculate_analytics(pd.read_csv(file))
    tabs = st.tabs(["👤 Profile", "📊 Comparison Analysis", "📋 Squad Health", "🌍 Transfer War Room"])

    with tabs[0]:
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique(), key="prof_1")
        p_d = df[df['player_name'] == p_name].iloc[0]
        st.markdown('<div class="player-card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1: st.image(p_d.get('club_logo_url', "https://via.placeholder.com/100"), width=100)
        with c2: st.image(p_d.get('photo_url', "https://via.placeholder.com/150"), width=150)
        with c3:
            st.header(p_name)
            st.write(f"**Club:** {p_d.get('club')} | **Age:** {int(p_d.get('age'))}")
            st.write(f"**Total Career Minutes:** {int(p_d.get('mins_played', 0))}")
            if p_d['Years_Left'] <= 0: st.markdown('<p class="status-critical">⚠️ CONTRACT EXPIRED</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("📄 Download Professional PDF"):
            pdf = generate_pro_pdf(p_d)
            st.download_button("Click to Download", pdf, f"{p_name}_Report.pdf")

    # --- TAB 2: COMPARISON ANALYSIS (TEAM AVERAGE FIX) ---
    with tabs[1]:
        st.subheader("Performance Comparison & Benchmarking")
        col1, col2 = st.columns(2)
        with col1: p1_name = st.selectbox("Primary Player", df['player_name'].unique(), key="comp_p1")
        with col2: compare_on = st.checkbox("Enable Comparison Mode", key="comp_check")
        
        p1_data = df[df['player_name'] == p1_name].iloc[0]
        cats = ['Technical', 'Tactical', 'Physical', 'Mental']
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=cats, y=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']], name=p1_name, marker_color='#212529'))
        
        if compare_on:
            p2_name = st.selectbox("Compare With", df['player_name'].unique(), index=1, key="comp_p2")
            p2_data = df[df['player_name'] == p2_name].iloc[0]
            fig.add_trace(go.Bar(x=cats, y=[p2_data['Tech_Score'], p2_data['Tact_Score'], p2_data['Phys_Score'], p2_data['Ment_Score']], name=p2_name, marker_color='#D00000'))
        
        # VISIBILITY FIX: Added Team Average as a High-Visibility Line Overlaid on Bars
        fig.add_trace(go.Scatter(
            x=cats, 
            y=[team_avg['Technical'], team_avg['Tactical'], team_avg['Physical'], team_avg['Mental']], 
            mode='lines+markers', 
            name='Team Average', 
            line=dict(color='#007BFF', width=4, dash='dash'),
            marker=dict(size=12, symbol='x')
        ))
        
        fig.update_layout(yaxis_range=[0,105], title="Benchmarking vs Squad Standard")
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 3: SQUAD HEALTH ---
    with tabs[2]:
        st.header("⚠️ Medical Readiness Index")
        low = df[df['Phys_Score'] < 65]
        if not low.empty:
            for _, p in low.iterrows(): st.error(f"🚨 **Injury Risk:** {p['player_name']} ({p['Phys_Score']:.1f}%)")
        else: st.success("All players fit.")
        
        fig_sq = px.scatter(df, x="Phys_Score", y="TPI", text="player_name", color="TPI", title="Talent Map")
        st.plotly_chart(fig_sq, use_container_width=True)

    # --- TAB 4: TRANSFER WAR ROOM (RESTORED SCATTER GRAPH) ---
    with tabs[3]:
        st.subheader("Decision Support: Opportunity Mapping")
        
        # RESTORED: Performance vs Contract Expiry Graph
        fig_war = px.scatter(
            df, 
            x="contract_end_year", 
            y="TPI", 
            size="market_value", 
            color="Transfer_Prob",
            text="player_name",
            labels={"contract_end_year": "Contract Expiry Year", "TPI": "Performance (TPI)"},
            title="Strategic Opportunity Map: TPI vs. Contract Expiry",
            height=600
        )
        fig_war.update_traces(textposition='top center')
        st.plotly_chart(fig_war, use_container_width=True)
        
        st.info("💡 **Strategy:** Focus on the Top-Left quadrant (High TPI, Early Expiry) for recruitment or renewal.")
        st.dataframe(df[['player_name', 'TPI', 'market_value', 'contract_end_year', 'Transfer_Prob']].sort_values(by='TPI', ascending=False))

else:
    st.info("Upload the Elite CSV to activate all tabs.")
