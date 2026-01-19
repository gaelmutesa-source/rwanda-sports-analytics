import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(page_title="Rwanda Sports Analytics", layout="wide")

st.title("⚽ Rwanda Football Performance Index")
st.sidebar.header("Control Panel")

# 1. File Uploader
uploaded_file = st.sidebar.file_uploader("Upload Match Data (CSV or Excel)", type=["csv", "xlsx"])

def calculate_tpi(df):
    # Weights for the 4 Pillars
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    
    # Simple scoring logic (assuming columns exist in your data)
    # This is where your "Secret Sauce" formulas live
    df['Tech_Score'] = df.get('pass_accuracy', 50) * 0.6 + df.get('dribble_success', 50) * 0.4
    df['Tact_Score'] = df.get('interceptions', 5) * 10
    df['Phys_Score'] = df.get('sprint_speed', 25) * 3
    df['Ment_Score'] = df.get('composure', 70)
    
    df['TPI'] = (df['Tech_Score'] * weights['Technical'] + 
                 df['Tact_Score'] * weights['Tactical'] + 
                 df['Phys_Score'] * weights['Physical'] + 
                 df['Ment_Score'] * weights['Mental'])
    return df

if uploaded_file:
    # Load Data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    df = calculate_tpi(df)

    # 2. Player Selection
    player_list = df['player_name'].unique()
    selected_player = st.selectbox("Select Player to Analyze", player_list)
    
    player_data = df[df['player_name'] == selected_player].iloc[0]

    # 3. Radar Chart (The Professional "Scouting" View)
    categories = ['Technical', 'Tactical', 'Physical', 'Mental']
    values = [player_data['Tech_Score'], player_data['Tact_Score'], 
              player_data['Phys_Score'], player_data['Ment_Score']]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name=selected_player))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Total Performance Index (TPI)", f"{player_data['TPI']:.1f}")
        st.write(f"**Position:** {player_data.get('position', 'N/A')}")
    with col2:
        st.plotly_chart(fig)

else:
    st.info("Waiting for data upload. Please upload a CSV file with columns: player_name, pass_accuracy, dribble_success, etc.")
    
    from fpdf import FPDF
import base64

def create_pdf(player_data, radar_image_path):
    pdf = FPDF()
    pdf.add_page()
    
    # Header & Branding
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 10, 'RWANDA PERFORMANCE SCOUTING REPORT', ln=True, align='C')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, 'Strictly Confidential - Powered by Your Company Name', ln=True, align='C')
    pdf.line(10, 30, 200, 30)

    # Player Info Section
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"Player: {player_data['player_name']}", ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"Position: {player_data['position']}", ln=True)
    pdf.cell(0, 8, f"Current TPI Score: {player_data['TPI']:.1f} / 100", ln=True)

    # KPI Breakdown Table
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(50, 10, 'Pillar', border=1)
    pdf.cell(50, 10, 'Score', border=1, ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(50, 10, 'Technical', border=1)
    pdf.cell(50, 10, f"{player_data['Tech_Score']:.1f}", border=1, ln=True)
    pdf.cell(50, 10, 'Tactical', border=1)
    pdf.cell(50, 10, f"{player_data['Tact_Score']:.1f}", border=1, ln=True)
    
    # Insert Radar Chart (Visual)
    # Note: Streamlit charts must be saved as images first to be put in PDF
    pdf.image(radar_image_path, x=110, y=50, w=90)

    # Final Recommendation
    tpi = player_data['TPI']
    verdict = "ELITE" if tpi > 85 else "PROFESSIONAL" if tpi > 70 else "DEVELOPING"
    pdf.ln(20)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(255, 0, 0) if verdict == "ELITE" else pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"SCOUTING VERDICT: {verdict}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- Inside your Streamlit App logic ---
if st.button("Generate Professional PDF Report"):
    # 1. Save the plotly chart as a temp image
    fig.write_image("temp_radar.png") 
    
    # 2. Generate PDF
    pdf_bytes = create_pdf(player_data, "temp_radar.png")
    
    # 3. Create Download Link
    st.download_button(
        label="Download PDF Scouting Report",
        data=pdf_bytes,
        file_name=f"{player_data['player_name']}_Scouting_Report.pdf",
        mime="application/pdf"
    )
