import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="Rwanda Sports Analytics Elite", layout="wide")

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_index=True)

# --- 2. THE BRAINS (KPI & PERCENTILE ENGINE) ---
def calculate_analytics(df):
    """Calculates TPI and Percentile Rankings for the whole league"""
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    df = df.fillna(df.median(numeric_only=True)) # Smart fill for missing data

    # Core Pillar Formulas
    df['Tech_Score'] = df.get('pass_accuracy', 50) * 0.6 + df.get('dribble_success', 50) * 0.4
    df['Tact_Score'] = (df.get('interceptions', 5) * 5) + (df.get('positioning_rating', 50) * 0.5)
    df['Phys_Score'] = (df.get('sprint_speed', 25) * 2) + (df.get('stamina', 50) * 0.2)
    df['Ment_Score'] = (df.get('composure', 70) * 0.7) + (df.get('big_game_impact', 50) * 0.3)
    
    # Total Performance Index (TPI)
    df['TPI'] = (df['Tech_Score'] * weights['Technical'] + 
                 df['Tact_Score'] * weights['Tactical'] + 
                 df['Phys_Score'] * weights['Physical'] + 
                 df['Ment_Score'] * weights['Mental'])
    
    # Phase 3: Percentile Ranking (How good is this player vs the rest of the file?)
    df['Rank_Percentile'] = df['TPI'].rank(pct=True) * 100
    return df

def generate_pdf_report(player_data, radar_img_bytes):
    """Stable PDF generation using memory buffers"""
    pdf = FPDF()
    pdf.add_page()
    
    # Header Branding
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(0, 51, 102) # Navy Blue
    pdf.cell(0, 15, 'RWANDA PERFORMANCE SCOUTING REPORT', ln=True, align='C')
    pdf.set_font('Arial', 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'Confidential Sports Analytics Platform', ln=True, align='C')
    pdf.line(10, 35, 200, 35)
    
    # Player Profile
    pdf.ln(15)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"PLAYER: {player_data['player_name'].upper()}", ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"Position: {player_data.get('position', 'RPL Pro')}", ln=True)
    pdf.cell(0, 8, f"TPI Score: {player_data['TPI']:.1f} / 100", ln=True)
    pdf.cell(0, 8, f"League Percentile: Top {100 - player_data['Rank_Percentile']:.1f}%", ln=True)
    
    # Insert Radar
    with open("temp_radar_report.png", "wb") as f:
        f.write(radar_img_bytes)
    pdf.image("temp_radar_report.png", x=110, y=50, w=85)
    
    # Scores
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    for p in ['Technical', 'Tactical', 'Physical', 'Mental']:
        score = player_data[f'{p[:4]}_Score']
        pdf.cell(40, 10, f"{p}: {score:.1f}", ln=True)

    return pdf.output(dest='S').encode('latin-1')

# --- 3. MAIN APP UI ---
st.title("⚽ Rwanda Football Analytics Hub")
st.sidebar.image("https://img.icons8.com/ios-filled/100/000000/soccer-ball.png", width=100)
uploaded_file = st.sidebar.file_uploader("Upload Match Data (CSV)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = calculate_analytics(df)
    
    # Sidebar Controls
    st.sidebar.divider()
    player_a_name = st.sidebar.selectbox("Select Primary Player", df['player_name'].unique())
    compare_mode = st.sidebar.checkbox("Enable Side-by-Side Comparison")
    
    # Primary Player Data
    p1_data = df[df['player_name'] == player_a_name].iloc[0]
    
    # Setup Radar Chart
    categories = ['Technical', 'Tactical', 'Physical', 'Mental']
    fig = go.Figure()

    # Add Player A Trace
    fig.add_trace(go.Scatterpolar(
        r=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']],
        theta=categories, fill='toself', name=player_a_name, line_color='#003366'
    ))

    # Optional Player B Comparison
    if compare_mode:
        player_b_name = st.sidebar.selectbox("Select Comparison Player", df['player_name'].unique(), index=1)
        p2_data = df[df['player_name'] == player_b_name].iloc[0]
        fig.add_trace(go.Scatterpolar(
            r=[p2_data['Tech_Score'], p2_data['Tact_Score'], p2_data['Phys_Score'], p2_data['Ment_Score']],
            theta=categories, fill='toself', name=player_b_name, line_color='#FF8C00'
        ))

    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)

    # Dashboard Display
    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.metric("TPI Score", f"{p1_data['TPI']:.1f}", delta=f"{p1_data['Rank_Percentile']:.1f} Percentile")
        st.write(f"### Scouting Verdict")
        if p1_data['Rank_Percentile'] > 85:
            st.success("🎯 **Elite Prospect:** High priority for recruitment.")
        elif p1_data['Rank_Percentile'] > 60:
            st.info("📈 **Professional Standard:** Reliable squad member.")
        else:
            st.warning("⚠️ **Developing:** Needs technical improvement.")

        # PDF Export Logic
        try:
            # We use kaleido engine to convert the chart to image bytes
            img_bytes = fig.to_image(format="png", engine="kaleido")
            if st.button("📄 Generate Pro Report"):
                pdf_data = generate_pdf_report(p1_data, img_bytes)
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_data,
                    file_name=f"{player_a_name}_Analytics.pdf",
                    mime="application/pdf"
                )
                st.balloons()
        except Exception as e:
            st.error("The report engine is initializing. Please wait a moment.")

else:
    st.info("👋 Welcome to the RPL Analytics Hub. Please upload your CSV data in the sidebar to begin.")
