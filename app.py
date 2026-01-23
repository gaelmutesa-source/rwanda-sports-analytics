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
    
    # Core Metrics
    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*weights['Technical'] + df['Tact_Score']*weights['Tactical'] + 
                 df['Phys_Score']*weights['Physical'] + df['Ment_Score']*weights['Mental'])
    
    # Market Metrics
    df['Transfer_Prob'] = ((df['TPI'] * 0.6) + (35 - df['age']) * 2) / 100
    df['Transfer_Prob'] = df['Transfer_Prob'].clip(0, 0.95)
    df['Years_Left'] = df['contract_end_year'] - current_year
    
    team_avg = {'Technical': df['Tech_Score'].mean(), 'Tactical': df['Tact_Score'].mean(),
                'Physical': df['Phys_Score'].mean(), 'Mental': df['Ment_Score'].mean()}
    return df, team_avg

# --- 2. EXECUTIVE PDF ENGINE ---
def generate_executive_pdf(p_data):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_fill_color(13, 27, 42)
    pdf.rect(0, 0, 210, 50, 'F')
    pdf.set_font('Arial', 'B', 24); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 30, 'EXECUTIVE PLAYER DOSSIER', align='C', ln=True)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, -10, 'Strictly Confidential - RPL Scouting & Management', align='C', ln=True)
    
    pdf.ln(35); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 18)
    pdf.cell(0, 10, p_data['player_name'].upper(), ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 7, f"Club: {p_data.get('club')} | Nationality: {p_data.get('nationality')}", ln=True)
    pdf.cell(0, 7, f"Market Value: ${int(p_data['market_value']):,} | Contract Ends: {int(p_data['contract_end_year'])}", ln=True)
    
    # Technical Summary
    pdf.ln(10); pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "Strategic Performance Metrics", ln=True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(70, 10, f"Total Performance Index (TPI):", 1); pdf.cell(30, 10, f"{p_data['TPI']:.1f}", 1, 1, 'C')
    pdf.cell(70, 10, f"Transfer Probability:", 1); pdf.cell(30, 10, f"{int(p_data['Transfer_Prob']*100)}%", 1, 1, 'C')
    
    pdf.ln(10); pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, "MANAGERIAL VERDICT:", ln=True)
    pdf.set_font('Arial', 'I', 11)
    status = "High-Value Target" if p_data['TPI'] > 80 and p_data['Years_Left'] <= 1 else "Core Asset"
    pdf.multi_cell(0, 8, f"Status: {status}. Analysis indicates that {p_data['player_name']} is a critical data-point for upcoming squad planning.")

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
        with c_t:
            st.header(p_data['player_name'])
            st.write(f"**TPI:** {p_data['TPI']:.1f} | **Market Value:** ${int(p_data['market_value']):,}")
            if p_data['Years_Left'] <= 0:
                st.markdown('<span class="status-critical">⚠️ CONTRACT EXPIRED</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("📄 Export Executive Dossier"):
            pdf_bytes = generate_executive_pdf(p_data)
            st.download_button("Download PDF", pdf_bytes, f"{p_name}_Executive_Report.pdf")

    with tabs[1]:
        p1_n = st.selectbox("Compare Player", df['player_name'].unique())
        p1_d = df[df['player_name'] == p1_n].iloc[0]
        fig = px.bar(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[p1_d['Tech_Score'], p1_d['Tact_Score'], p1_d['Phys_Score'], p1_d['Ment_Score']], title=f"Performance Breakdown: {p1_n}")
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        st.header("Medical & Readiness Alerts")
        low_phys = df[df['Phys_Score'] < 65]
        for _, p in low_phys.iterrows():
            st.error(f"Risk: {p['player_name']} (Readiness: {p['Phys_Score']:.1f}%)")

    with tabs[3]:
        st.subheader("Decision Support: Transfer War Room")
        
        # RESTORED GRAPH: High TPI + Short Contract = Opportunity
        fig_strat = px.scatter(
            df, 
            x="contract_end_year", 
            y="TPI", 
            size="market_value", 
            color="Transfer_Prob",
            text="player_name",
            labels={"contract_end_year": "Contract Expiry Year", "TPI": "Performance (TPI)"},
            title="Executive Opportunity Map: Performance vs. Contract Expiry",
            height=600
        )
        fig_strat.update_traces(textposition='top center')
        st.plotly_chart(fig_strat, use_container_width=True)
        
        st.info("💡 **Strategy Guidance:** Focus on the **Top-Left** quadrant. These players have the highest performance scores but are nearing the end of their contracts, making them priority targets for acquisition or renewal.")
        
        st.dataframe(df[['player_name', 'club', 'TPI', 'market_value', 'contract_end_year', 'Transfer_Prob']].sort_values(by='TPI', ascending=False), use_container_width=True)

else:
    st.info("Upload the Elite CSV to activate the management dashboard.")
