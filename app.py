import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. UI CONFIGURATION ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #F1F3F5; border-right: 1px solid #DEE2E6; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E9ECEF; border-radius: 8px; }
    h1, h2, h3 { color: #0D1B2A !important; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    df_numeric = df.select_dtypes(include=['number'])
    df[df_numeric.columns] = df_numeric.fillna(df_numeric.median())
    
    df['Tech_Score'] = df.get('pass_accuracy', 50) * 0.6 + df.get('dribble_success', 50) * 0.4
    df['Tact_Score'] = (df.get('interceptions', 5) * 5) + (df.get('positioning_rating', 50) * 0.5)
    df['Phys_Score'] = (df.get('sprint_speed', 25) * 2) + (df.get('stamina', 50) * 0.2)
    df['Ment_Score'] = (df.get('composure', 70) * 0.7) + (df.get('big_game_impact', 50) * 0.3)
    
    df['TPI'] = (df['Tech_Score'] * weights['Technical'] + 
                 df['Tact_Score'] * weights['Tactical'] + 
                 df['Phys_Score'] * weights['Physical'] + 
                 df['Ment_Score'] * weights['Mental'])
    
    top_5 = df.nlargest(5, 'TPI')
    elite_stats = top_5[['Tech_Score', 'Tact_Score', 'Phys_Score', 'Ment_Score']].mean()
    return df, elite_stats

# --- 2. MULTI-MODE PDF ENGINE ---
def generate_pdf_report(data_type, p1_data, df=None, chart_bytes=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(33, 37, 41) 
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font('Arial', 'B', 18); pdf.set_text_color(255, 255, 255)
    
    if data_type == 'individual':
        pdf.cell(0, 20, f"PERFORMANCE REPORT: {p1_data['player_name']}", align='C', ln=True)
        pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 12)
        for m in ['Technical', 'Tactical', 'Physical', 'Mental', 'TPI']:
            key = f"{m[:4]}_Score" if m != 'TPI' else 'TPI'
            pdf.cell(50, 10, f"{m}: {p1_data[key]:.1f}", ln=True)
    else:
        pdf.cell(0, 20, "SQUAD STRATEGIC HEALTH REPORT", align='C', ln=True)
        pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Risk Assessment:", ln=True)
        low_phys = df[df['Phys_Score'] < 65]
        for _, p in low_phys.iterrows():
            pdf.set_text_color(200, 0, 0)
            pdf.cell(0, 8, f"- {p['player_name']}: CRITICAL FATIGUE ({p['Phys_Score']:.1f})", ln=True)

    if chart_bytes:
        img_buffer = io.BytesIO(chart_bytes)
        pdf.image(img_buffer, x=10, y=100, w=190)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. UI LOGIC ---
st.sidebar.title("💎 RPL ELITE")
uploaded_file = st.sidebar.file_uploader("UPLOAD DATASET (CSV)", type="csv")

if uploaded_file:
    raw_df = pd.read_csv(uploaded_file)
    df, elite_stats = calculate_analytics(raw_df)
    
    tabs = st.tabs(["👤 Profile", "📊 Analysis", "⚽ Match Day", "🌟 Elite", "📋 Squad Health"])

    # --- TAB 1: PLAYER PROFILE ---
    with tabs[0]:
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique(), key="prof_sel")
        p_bio = df[df['player_name'] == p_name].iloc[0]
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write(f"**Nationality:** {p_bio.get('nationality', 'Rwanda')}")
            st.write(f"**Age:** {p_bio.get('age', '24')}")
        with c2:
            st.write(f"**Preferred Foot:** {p_bio.get('foot', 'Right')}")
            st.write(f"**Position:** {p_bio.get('position', 'Forward')}")
        with c3:
            st.success(f"**Strength:** { 'High Stamina' if p_bio['Phys_Score'] > 75 else 'Technical Control'}")
            st.warning(f"**Weakness:** { 'Defensive IQ' if p_bio['Tact_Score'] < 50 else 'Match Composure'}")

    # --- TAB 2: INDIVIDUAL ANALYSIS ---
    with tabs[1]:
        p1_name = st.selectbox("Primary Player", df['player_name'].unique(), key="p1_an")
        p1_data = df[df['player_name'] == p1_name].iloc[0]
        fig_bar = go.Figure(go.Bar(y=['Tech', 'Tact', 'Phys', 'Ment'], x=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']], orientation='h', marker_color='#212529'))
        st.plotly_chart(fig_bar, use_container_width=True)
        if st.button("📥 Download Individual PDF"):
            img = fig_bar.to_image(format="png")
            pdf = generate_pdf_report('individual', p1_data, chart_bytes=img)
            st.download_button("Download Report", pdf, f"{p1_name}_Report.pdf")

    # --- TAB 3: MATCH DAY PERFORMANCE ---
    with tabs[2]:
        p_match = st.selectbox("Select Match Stats", df['player_name'].unique(), key="match_sel")
        m_data = df[df['player_name'] == p_match].iloc[0]
        
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Goals", int(m_data.get('goals', 0)))
        mc2.metric("Assists", int(m_data.get('assists', 0)))
        mc3.metric("Distance (km)", f"{m_data.get('distance', 10.2)}km")
        
        st.subheader("Match Heatmap (Movement Density)")
        # Simulating heatmap with random movement around a position
        heatmap_data = pd.DataFrame({'x': [20, 30, 40, 50, 60, 55], 'y': [40, 45, 50, 80, 70, 65]})
        fig_heat = px.density_heatmap(heatmap_data, x="x", y="y", nbinsx=10, nbinsy=10, range_x=[0,100], range_y=[0,100], color_continuous_scale="Viridis")
        st.plotly_chart(fig_heat, use_container_width=True)

    # --- TAB 4: ELITE BENCHMARK ---
    with tabs[3]:
        st.subheader("Vs. League Elite")
        # (Existing Elite Logic...)

    # --- TAB 5: SQUAD HEALTH ---
    with tabs[4]:
        st.header("📋 Squad Strategic Overview")
        fig_sq = go.Figure(data=go.Scatter(x=df['Phys_Score'], y=df['TPI'], mode='markers+text', text=df['player_name'], marker=dict(size=14, color=df['TPI'], colorscale='Viridis')))
        st.plotly_chart(fig_sq, use_container_width=True)
        
        st.subheader("📊 Squad Depth & Alerts")
        sc1, sc2 = st.columns(2)
        with sc1:
            pos_counts = df['position'].value_counts()
            st.plotly_chart(go.Figure(data=[go.Pie(labels=pos_counts.index, values=pos_counts.values, hole=.3)]), use_container_width=True)
        with sc2:
            low_phys = df[df['Phys_Score'] < 65]
            for _, p in low_phys.iterrows():
                st.error(f"**Risk:** {p['player_name']} ({p['Phys_Score']:.1f})")
        
        if st.button("📥 Download Squad Health PDF"):
            img_s = fig_sq.to_image(format="png")
            pdf_s = generate_pdf_report('squad', None, df=df, chart_bytes=img_s)
            st.download_button("Download Squad Report", pdf_s, "Squad_Health.pdf")

else:
    st.info("System Ready. Please upload CSV Match Data.")
