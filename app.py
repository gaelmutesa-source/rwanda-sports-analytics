import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. UI & THEME ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #F1F3F5; border-right: 1px solid #DEE2E6; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E9ECEF; border-radius: 8px; }
    .insight-box { background-color: #E7F3FF; padding: 15px; border-radius: 8px; border-left: 5px solid #007BFF; margin: 10px 0; }
    .recommendation-box { background-color: #FFF4E5; padding: 15px; border-radius: 8px; border-left: 5px solid #FF8C00; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    # Handling missing valuation data
    if 'market_value' not in df.columns:
        df['market_value'] = 50000 

    required = ['pass_accuracy', 'dribble_success', 'interceptions', 'positioning_rating', 'sprint_speed', 'stamina', 'composure', 'big_game_impact']
    for col in required:
        if col not in df.columns: df[col] = 50
    
    df_numeric = df.select_dtypes(include=['number'])
    df[df_numeric.columns] = df_numeric.fillna(df_numeric.median())
    
    # Pillar Calculations
    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*weights['Technical'] + df['Tact_Score']*weights['Tactical'] + 
                 df['Phys_Score']*weights['Physical'] + df['Ment_Score']*weights['Mental'])
    
    team_avg = {'Technical': df['Tech_Score'].mean(), 'Tactical': df['Tact_Score'].mean(), 
                'Physical': df['Phys_Score'].mean(), 'Mental': df['Ment_Score'].mean(), 'TPI': df['TPI'].mean()}
    top_5 = df.nlargest(5, 'TPI')
    elite_stats = top_5[['Tech_Score', 'Tact_Score', 'Phys_Score', 'Ment_Score']].mean()
    return df, elite_stats, team_avg

def get_scouting_notes(row):
    strength = "Elite ball progression and technical security" if row['Tech_Score'] > 75 else "Strong positional awareness and defensive screening"
    weakness = "Limited recovery pace in defensive transitions" if row['Phys_Score'] < 60 else "Decision-making under high-intensity pressing"
    if row['Tact_Score'] < 50: weakness = "Discipline in maintaining defensive block structure"
    return strength, weakness

# --- 2. PROFESSIONAL PDF ENGINE ---
def generate_pro_pdf(p_data, report_type='individual'):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(13, 27, 42) 
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font('Arial', 'B', 22); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 25, 'RPL PERFORMANCE ELITE', align='C', ln=True)
    pdf.set_font('Arial', 'I', 10); pdf.cell(0, -5, 'Official Technical Scouting & Performance Report', align='C', ln=True)
    
    pdf.ln(30); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"PLAYER: {p_data['player_name'].upper()}", ln=True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f"Club: {p_data.get('club', 'RPL Club')} | Nationality: {p_data.get('nationality', 'N/A')} | Age: {p_data.get('age', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Current Market Value: ${p_data.get('market_value', 0):,}", ln=True)
    pdf.ln(5)
    
    # Career Stats Table
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(45, 10, "Appearances", 1, 0, 'C', True); pdf.cell(45, 10, "Goals", 1, 0, 'C', True)
    pdf.cell(45, 10, "Assists", 1, 0, 'C', True); pdf.cell(45, 10, "TPI Index", 1, 1, 'C', True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(45, 10, str(int(p_data.get('appearances', 0))), 1, 0, 'C'); pdf.cell(45, 10, str(int(p_data.get('goals', 0))), 1, 0, 'C')
    pdf.cell(45, 10, str(int(p_data.get('assists', 0))), 1, 0, 'C'); pdf.cell(45, 10, f"{p_data['TPI']:.1f}", 1, 1, 'C')
    
    # Dynamic Scouting Verdict
    strength, weakness = get_scouting_notes(p_data)
    pdf.ln(10); pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 100, 0); pdf.cell(0, 10, f"STRENGTH: {strength}", ln=True)
    pdf.set_text_color(150, 0, 0); pdf.cell(0, 10, f"WEAKNESS: {weakness}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. MAIN APP ---
st.sidebar.title("💎 RPL ELITE")
file = st.sidebar.file_uploader("Upload CSV", type="csv")

if file:
    df, elite, team_avg = calculate_analytics(pd.read_csv(file))
    tabs = st.tabs(["👤 Profile", "📊 Analysis", "⚽ Match Day", "📋 Squad Health", "💰 Financial Value"])

    # TAB 1: PROFILE
    with tabs[0]:
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique(), key="prof_1")
        p_bio = df[df['player_name'] == p_name].iloc[0]
        st.header(f"{p_bio['player_name']} | {p_bio.get('club', 'RPL Club')}")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Market Value", f"${p_bio.get('market_value', 0):,}")
            st.write(f"**Nationality:** {p_bio.get('nationality', 'Rwanda')}")
        with c2:
            st.metric("Goals", int(p_bio.get('goals', 0)))
            st.write(f"**Age:** {p_bio.get('age', '24')}")
        with c3:
            st.metric("TPI Index", f"{p_bio['TPI']:.1f}")
            st.write(f"**Foot:** {p_bio.get('foot', 'Right')}")
        
        s, w = get_scouting_notes(p_bio)
        st.info(f"**Technical Strength:** {s}")
        st.warning(f"**Technical Weakness:** {w}")
        
        if st.button("📥 Download Pro Scouting Report"):
            pdf = generate_pro_pdf(p_bio)
            st.download_button("Confirm PDF Download", pdf, f"{p_name}_Elite_Report.pdf", "application/pdf")

    # TAB 2: ANALYSIS
    with tabs[1]:
        col1, col2 = st.columns(2)
        with col1: p1_n = st.selectbox("Primary Player", df['player_name'].unique(), key="an_1")
        with col2: compare = st.checkbox("Enable Comparison Mode", key="comp_1")
        
        p1_d = df[df['player_name'] == p1_n].iloc[0]
        cats = ['Technical', 'Tactical', 'Physical', 'Mental']
        fig = go.Figure()
        fig.add_trace(go.Bar(x=cats, y=[p1_d['Tech_Score'], p1_d['Tact_Score'], p1_d['Phys_Score'], p1_d['Ment_Score']], name=p1_n, marker_color='#1B263B'))
        fig.add_trace(go.Scatter(x=cats, y=[team_avg['Technical'], team_avg['Tactical'], team_avg['Physical'], team_avg['Mental']], mode='lines+markers', name='Team Avg', line=dict(color='#007BFF', dash='dash')))
        
        if compare:
            p2_n = st.selectbox("Compare With", df['player_name'].unique(), index=1, key="an_2")
            p2_d = df[df['player_name'] == p2_n].iloc[0]
            fig.add_trace(go.Bar(x=cats, y=[p2_d['Tech_Score'], p2_d['Tact_Score'], p2_d['Phys_Score'], p2_d['Ment_Score']], name=p2_n, marker_color='#C0392B'))
        
        fig.update_layout(title="Performance Benchmarking vs Team Average", xaxis_title="Pillars", yaxis_title="Score (0-100)")
        st.plotly_chart(fig, use_container_width=True)

    # TAB 3: MATCH DAY
    with tabs[2]:
        p_m = st.selectbox("Match Stats", df['player_name'].unique(), key="md_1")
        m_d = df[df['player_name'] == p_m].iloc[0]
        st.metric("Total Covered Distance", f"{m_d.get('distance', 0)} km")
        fig_h = px.density_heatmap(pd.DataFrame({'x': [m_d.get('x_coord', 50)], 'y': [m_d.get('y_coord', 50)]}), x="x", y="y", range_x=[0,100], range_y=[0,100], title="Movement Intensity (Heatmap)")
        st.plotly_chart(fig_h, use_container_width=True)

    # TAB 4: SQUAD HEALTH
    with tabs[3]:
        st.header("📋 Squad Strategic Health Index")
        h_idx = team_avg['Physical']
        c_h1, c_h2 = st.columns([1, 2])
        with c_h1: st.metric("Readiness Index", f"{h_idx:.1f}%")
        with c_h2:
            if h_idx > 80: st.success("**ELITE.** Squad at peak capacity.")
            elif h_idx > 65: st.warning("**MODERATE.** Rotation advised.")
            else: st.error("**CRITICAL.** High injury risk.")
        
        low = df[df['Phys_Score'] < 65]
        for _, p in low.iterrows(): st.error(f"🚨 **Injury Risk:** {p['player_name']} ({p['Phys_Score']:.1f}%)")
        
        fig_sq = go.Figure(data=go.Scatter(x=df['Phys_Score'], y=df['TPI'], mode='markers+text', text=df['player_name']))
        fig_sq.update_layout(title="Talent Map (Readiness vs Impact)", xaxis_title="Readiness", yaxis_title="Performance")
        st.plotly_chart(fig_sq, use_container_width=True)

    # TAB 5: FINANCIAL VALUE (NEW)
    with tabs[4]:
        st.header("💰 Squad Financial Valuation")
        fig_val = px.scatter(df, x="TPI", y="market_value", text="player_name", size="age", color="club",
                             title="Performance (TPI) vs Market Value", labels={"TPI": "Performance Index", "market_value": "Value ($)"})
        fig_val.update_traces(textposition='top center')
        st.plotly_chart(fig_val, use_container_width=True)
        
        st.markdown("""<div class="insight-box"><b>Valuation Interpretation:</b> Players in the <b>Top-Left</b> (High Value, Lower TPI) may be overpriced. 
        Players in the <b>Bottom-Right</b> (Lower Value, High TPI) represent <b>High Value Assets</b> or "Bargains" for the club.</div>""", unsafe_allow_html=True)

else:
    st.info("Upload CSV to begin.")
