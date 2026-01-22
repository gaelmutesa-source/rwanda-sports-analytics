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
    .player-card { border: 2px solid #E9ECEF; padding: 20px; border-radius: 15px; background: white; text-align: center; }
    .insight-box { background-color: #E7F3FF; padding: 15px; border-radius: 8px; border-left: 5px solid #007BFF; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    required = ['pass_accuracy', 'dribble_success', 'interceptions', 'positioning_rating', 'sprint_speed', 'stamina', 'composure', 'big_game_impact']
    for col in required:
        if col not in df.columns: df[col] = 50
    df_numeric = df.select_dtypes(include=['number'])
    df[df_numeric.columns] = df_numeric.fillna(df_numeric.median())
    
    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*weights['Technical'] + df['Tact_Score']*weights['Tactical'] + 
                 df['Phys_Score']*weights['Physical'] + df['Ment_Score']*weights['Mental'])
    
    return df, df[['Tech_Score', 'Tact_Score', 'Phys_Score', 'Ment_Score']].mean()

# --- 2. EXECUTIVE PDF ENGINE ---
def generate_pro_pdf(p_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(13, 27, 42) 
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font('Arial', 'B', 22); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 25, 'OFFICIAL SCOUTING DOSSIER', align='C', ln=True)
    pdf.ln(30); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"{p_data['player_name'].upper()}", ln=True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f"Club: {p_data.get('club', 'N/A')} | Career Mins: {int(p_data.get('mins_played', 0))} | Value: ${p_data.get('market_value', 0):,}", ln=True)
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, "Technical Performance Matrix", ln=True)
    for m in ['Tech_Score', 'Tact_Score', 'Phys_Score', 'Ment_Score', 'TPI']:
        pdf.set_font('Arial', '', 10)
        pdf.cell(50, 8, m.replace('_', ' '), 1); pdf.cell(30, 8, f"{p_data[m]:.1f}", 1, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- 3. MAIN APP ---
st.sidebar.title("💎 RPL ELITE")
file = st.sidebar.file_uploader("Upload Data", type="csv")

if file:
    df, team_avg = calculate_analytics(pd.read_csv(file))
    tabs = st.tabs(["👤 Elite Profile", "📊 Scouting Ranking", "📋 Squad Health", "⚽ Performance Depth"])

    # --- TAB 1: ELITE PROFILE ---
    with tabs[0]:
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique())
        p_data = df[df['player_name'] == p_name].iloc[0]
        
        st.markdown('<div class="player-card">', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2])
        with c1:
            if p_data.get('photo_url'): st.image(p_data['photo_url'], width=200)
            else: st.image("https://via.placeholder.com/200?text=Player+Photo", width=200)
        with c2:
            st.header(p_data['player_name'])
            st.subheader(f"{p_data.get('club')} | {p_data.get('nationality')}")
            st.write(f"**Total Career Minutes:** {int(p_data.get('mins_played', 0))} mins")
            st.write(f"**Age:** {int(p_data.get('age', 0))} | **Foot:** {p_data.get('foot')}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Goals", int(p_data.get('goals', 0)))
        m2.metric("Assists", int(p_data.get('assists', 0)))
        m3.metric("Market Value", f"${p_data.get('market_value', 0):,}")

        if st.button("📄 Generate Professional PDF"):
            pdf = generate_pro_pdf(p_data)
            st.download_button("Download Report", pdf, f"{p_name}_Profile.pdf")

    # --- TAB 2: SCOUTING RANKING ---
    with tabs[1]:
        st.subheader("Global Squad Ranking")
        sort_by = st.selectbox("Rank By Metric", ["atk_contribution", "def_contribution", "TPI", "mins_played"])
        ranked_df = df[['player_name', 'position', 'market_value', sort_by]].sort_values(by=sort_by, ascending=False)
        st.table(ranked_df)

    # --- TAB 3: SQUAD HEALTH (INJURY ALERTS) ---
    with tabs[2]:
        st.header("⚠️ Medical Readiness & Decision Support")
        low_phys = df[df['Phys_Score'] < 65]
        if not low_phys.empty:
            for _, p in low_phys.iterrows():
                st.error(f"**CRITICAL INJURY RISK:** {p['player_name']} is below 65% readiness. Cumulative minutes ({int(p['mins_played'])}) suggest extreme fatigue.")
        else: st.success("No players currently at risk.")
        
        fig_sq = go.Figure(data=go.Scatter(x=df['Phys_Score'], y=df['TPI'], mode='markers+text', text=df['player_name'], marker=dict(size=15, color=df['TPI'], colorscale='Plasma')))
        fig_sq.update_layout(title="Talent Map (Physical Readiness vs Impact)", xaxis_title="Readiness (%)", yaxis_title="TPI Index")
        st.plotly_chart(fig_sq, use_container_width=True)

    # --- TAB 4: PERFORMANCE DEPTH ---
    with tabs[3]:
        p_depth = st.selectbox("Deep Performance Analysis", df['player_name'].unique())
        pd_data = df[df['player_name'] == p_depth].iloc[0]
        
        st.subheader("Phase Contribution Profile")
        fig_radial = go.Figure(go.Bar(x=['Attacking Contribution', 'Defensive Contribution'], y=[pd_data['atk_contribution'], pd_data['def_contribution']], marker_color=['#C0392B', '#1B263B']))
        st.plotly_chart(fig_radial, use_container_width=True)
        
        st.markdown(f'<div class="insight-box"><b>Technical Verdict:</b> {p_depth} shows a { "High Defensive" if pd_data["def_contribution"] > 70 else "High Attacking" } profile. Total cumulative passes: {int(pd_data["passes_completed"])}.</div>', unsafe_allow_html=True)

else:
    st.info("Upload Career Performance CSV to proceed.")
