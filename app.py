import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- 1. SETTINGS ---
st.set_page_config(page_title="Rwanda Sports Analytics Elite", layout="wide")

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    df = df.fillna(df.median(numeric_only=True)) 

    # KPI Formulas
    df['Tech_Score'] = df.get('pass_accuracy', 50) * 0.6 + df.get('dribble_success', 50) * 0.4
    df['Tact_Score'] = (df.get('interceptions', 5) * 5) + (df.get('positioning_rating', 50) * 0.5)
    df['Phys_Score'] = (df.get('sprint_speed', 25) * 2) + (df.get('stamina', 50) * 0.2)
    df['Ment_Score'] = (df.get('composure', 70) * 0.7) + (df.get('big_game_impact', 50) * 0.3)
    
    df['TPI'] = (df['Tech_Score'] * weights['Technical'] + 
                 df['Tact_Score'] * weights['Tactical'] + 
                 df['Phys_Score'] * weights['Physical'] + 
                 df['Ment_Score'] * weights['Mental'])
    
    df['Rank_Percentile'] = df['TPI'].rank(pct=True) * 100
    return df

def generate_pdf_report(player_data, radar_img_bytes):
    """Refined PDF engine with Type Guarding to prevent TypeErrors"""
    if not isinstance(radar_img_bytes, bytes):
        return None

    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font('Arial', 'B', 18)
    pdf.cell(0, 15, 'RWANDA PERFORMANCE SCOUTING REPORT', ln=True, align='C')
    pdf.line(10, 30, 200, 30)
    
    # Stats
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"PLAYER: {str(player_data['player_name']).upper()}", ln=True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"TPI Score: {float(player_data['TPI']):.1f} / 100", ln=True)
    pdf.cell(0, 8, f"Percentile: Top {100 - float(player_data['Rank_Percentile']):.1f}%", ln=True)
    
    # Image Handling (Virtual File)
    img_buffer = io.BytesIO(radar_img_bytes)
    with open("temp_report_img.png", "wb") as f:
        f.write(img_buffer.getvalue())
    
    pdf.image("temp_report_img.png", x=110, y=45, w=85)
    
    pdf.ln(10)
    for p in ['Technical', 'Tactical', 'Physical', 'Mental']:
        val = float(player_data[f'{p[:4]}_Score'])
        pdf.cell(40, 10, f"{p}: {val:.1f}", ln=True)

    return pdf.output(dest='S').encode('latin-1')

# --- 2. APP UI ---
st.title("⚽ Rwanda Football Analytics Hub")
uploaded_file = st.sidebar.file_uploader("Upload Match Data (CSV)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = calculate_analytics(df)
    
    player_a_name = st.sidebar.selectbox("Select Primary Player", df['player_name'].unique())
    compare_mode = st.sidebar.checkbox("Enable Comparison")
    
    p1_data = df[df['player_name'] == player_a_name].iloc[0]
    
    # Radar Chart
    categories = ['Technical', 'Tactical', 'Physical', 'Mental']
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']],
        theta=categories, fill='toself', name=player_a_name
    ))

    if compare_mode:
        player_b_name = st.sidebar.selectbox("Select Comparison Player", df['player_name'].unique(), index=1)
        p2_data = df[df['player_name'] == player_b_name].iloc[0]
        fig.add_trace(go.Scatterpolar(
            r=[p2_data['Tech_Score'], p2_data['Tact_Score'], p2_data['Phys_Score'], p2_data['Ment_Score']],
            theta=categories, fill='toself', name=player_b_name
        ))

    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
    
    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.metric("TPI Score", f"{p1_data['TPI']:.1f}")
        
        # PDF TRIGGER
        if st.button("📄 Generate Report"):
            try:
                # Convert Plotly to Image Bytes
                img_bytes = fig.to_image(format="png", engine="kaleido")
                
                # Create PDF
                pdf_data = generate_pdf_report(p1_data, img_bytes)
                
                if pdf_data:
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_data,
                        file_name=f"{player_a_name}_Report.pdf",
                        mime="application/pdf"
                    )
                    st.balloons()
            except Exception as e:
                st.error(f"Error: {str(e)}")
