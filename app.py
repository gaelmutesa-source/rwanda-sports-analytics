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
    .insight-box { background-color: #E7F3FF; padding: 15px; border-radius: 8px; border-left: 5px solid #007BFF; margin-top: 10px; }
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
    df['TPI'] = (df['Tech_Score']*weights['Technical'] + df['Tact_Score']*weights['Tactical'] + df['Phys_Score']*weights['Physical'] + df['Ment_Score']*weights['Mental'])
    
    # Calculate Team Averages
    team_avg = {
        'Technical': df['Tech_Score'].mean(),
        'Tactical': df['Tact_Score'].mean(),
        'Physical': df['Phys_Score'].mean(),
        'Mental': df['Ment_Score'].mean()
    }
    
    top_5 = df.nlargest(5, 'TPI')
    elite_stats = top_5[['Tech_Score', 'Tact_Score', 'Phys_Score', 'Ment_Score']].mean()
    return df, elite_stats, team_avg

# --- 2. ENHANCED PDF ENGINE ---
def generate_pdf(report_type, p1_data, p2_data=None, chart_bytes=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(33, 37, 41) 
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font('Arial', 'B', 16); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 20, f"RPL ELITE {report_type.upper()} REPORT", align='C', ln=True)
    pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 12)
    
    pdf.cell(0, 10, f"Player: {p1_data['player_name']}", ln=True)
    if report_type == 'profile':
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, f"Nationality: {p1_data.get('nationality', 'N/A')}", ln=True)
        pdf.cell(0, 8, f"Age: {p1_data.get('age', 'N/A')} | Foot: {p1_data.get('foot', 'N/A')}", ln=True)
    
    if chart_bytes:
        img_buf = io.BytesIO(chart_bytes)
        pdf.image(img_buf, x=10, y=80, w=190)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. MAIN DASHBOARD ---
st.sidebar.title("💎 RPL ELITE")
file = st.sidebar.file_uploader("Upload CSV", type="csv")

if file:
    df, elite, team_avg = calculate_analytics(pd.read_csv(file))
    tabs = st.tabs(["👤 Profile", "📊 Analysis", "⚽ Match Day", "📋 Squad Health"])

    # TAB 1: PROFILE
    with tabs[0]:
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique())
        p_bio = df[df['player_name'] == p_name].iloc[0]
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Biometric Overview")
            st.write(f"**Nationality:** {p_bio.get('nationality', 'Rwanda')}")
            st.write(f"**Age:** {p_bio.get('age', '24')}")
            st.write(f"**Preferred Foot:** {p_bio.get('foot', 'Right')}")
        with c2:
            st.subheader("Technical Verdict")
            st.info(f"**Primary Strength:** {'Physical Dominance' if p_bio['Phys_Score'] > 75 else 'Tactical Positioning'}")
            st.warning(f"**Key Weakness:** {'Mental Pressure' if p_bio['Ment_Score'] < 60 else 'Technical Consistency'}")
        
        if st.button("📥 Download Profile PDF"):
            pdf = generate_pdf('profile', p_bio)
            st.download_button("Click to Download", pdf, f"{p_name}_Profile.pdf")

    # TAB 2: ANALYSIS
    with tabs[1]:
        col1, col2 = st.columns(2)
        with col1: p1_n = st.selectbox("Primary Player", df['player_name'].unique(), key="a1")
        with col2: compare = st.checkbox("Enable Comparison Mode")
        
        p1_d = df[df['player_name'] == p1_n].iloc[0]
        fig = go.Figure()
        cats = ['Technical', 'Tactical', 'Physical', 'Mental']
        vals1 = [p1_d['Tech_Score'], p1_d['Tact_Score'], p1_d['Phys_Score'], p1_d['Ment_Score']]
        
        # Player 1 Bar
        fig.add_trace(go.Bar(x=cats, y=vals1, name=p1_n, marker_color='#212529'))
        
        # Team Average Line (The requested feature)
        fig.add_trace(go.Scatter(x=cats, y=[team_avg['Technical'], team_avg['Tactical'], team_avg['Physical'], team_avg['Mental']], 
                                 mode='lines+markers', name='Team Average', 
                                 line=dict(color='#007BFF', width=3, dash='dash')))
        
        p2_d = None
        if compare:
            p2_n = st.selectbox("Compare With", df['player_name'].unique(), index=1)
            p2_d = df[df['player_name'] == p2_n].iloc[0]
            vals2 = [p2_d['Tech_Score'], p2_d['Tact_Score'], p2_d['Phys_Score'], p2_d['Ment_Score']]
            fig.add_trace(go.Bar(x=cats, y=vals2, name=p2_n, marker_color='#D00000'))
        
        fig.update_layout(title="Performance Pillar Benchmarking", xaxis_title="Performance Pillars", yaxis_title="Competency Score (0-100)")
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(f"""<div class="insight-box"><b>Strategic Interpretation:</b> The <b>Blue Dashed Line</b> represents the squad's average. 
        If {p1_n}'s bars are above this line, they are outperforming the current roster standard. This is critical for <b>starting lineup</b> decisions and <b>contract renewals</b>.</div>""", unsafe_allow_html=True)
        
        if st.button("📥 Download Analysis PDF"):
            img = fig.to_image(format="png")
            pdf = generate_pdf('analysis', p1_d, p2_d, img)
            st.download_button("Download Report", pdf, f"{p1_n}_Analysis.pdf")

    # TAB 3: MATCH DAY
    with tabs[2]:
        p_m = st.selectbox("Select Match Performance", df['player_name'].unique())
        m_d = df[df['player_name'] == p_m].iloc[0]
        st.metric("Covered Distance", f"{m_d.get('distance', 10.0)} km")
        
        fig_h = px.density_heatmap(pd.DataFrame({'x': [m_d.get('x_coord', 50)], 'y': [m_d.get('y_coord', 50)]}), x="x", y="y", range_x=[0,100], range_y=[0,100], title="Movement Intensity Map")
        fig_h.update_layout(xaxis_title="Pitch Width (m)", yaxis_title="Pitch Length (m)")
        st.plotly_chart(fig_h, use_container_width=True)
        
        st.markdown("""<div class="insight-box"><b>Heatmap Interpretation:</b> Intense colors indicate high-activity zones. High activity in the final third indicates strong offensive intent.</div>""", unsafe_allow_html=True)

    # TAB 4: SQUAD HEALTH
    with tabs[3]:
        fig_s = go.Figure(data=go.Scatter(x=df['Phys_Score'], y=df['TPI'], mode='markers+text', text=df['player_name']))
        fig_s.update_layout(title="Squad Talent Map", xaxis_title="Physical Readiness (%)", yaxis_title="Total Performance Index (TPI)")
        st.plotly_chart(fig_s, use_container_width=True)
        
        # Team Readiness Benchmark on Talent Map
        st.info(f"**Current Squad Physical Readiness Average:** {df['Phys_Score'].mean():.1f}%")
        
        low = df[df['Phys_Score'] < 65]
        for _, p in low.iterrows(): st.error(f"⚠️ **Fatigue Alert:** {p['player_name']} ({p['Phys_Score']:.1f}%)")

else:
    st.info("Upload CSV to begin.")
