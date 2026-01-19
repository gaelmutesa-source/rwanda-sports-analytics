import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- 1. CONFIGURATION & BRAINS ---
st.set_page_config(page_title="Rwanda Sports Analytics", layout="wide")

def calculate_tpi(df):
    """Proprietary KPI Calculation Logic"""
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    
    # Fill missing values with league average (50) to prevent crashes
    df = df.fillna(50)
    
    # Formulas (Adjust these as your IP grows)
    df['Tech_Score'] = df.get('pass_accuracy', 50) * 0.6 + df.get('dribble_success', 50) * 0.4
    df['Tact_Score'] = (df.get('interceptions', 5) * 5) + (df.get('positioning_rating', 50) * 0.5)
    df['Phys_Score'] = (df.get('sprint_speed', 25) * 2) + (df.get('stamina', 50) * 0.2)
    df['Ment_Score'] = (df.get('composure', 70) * 0.7) + (df.get('big_game_impact', 50) * 0.3)
    
    df['TPI'] = (df['Tech_Score'] * weights['Technical'] + 
                 df['Tact_Score'] * weights['Tactical'] + 
                 df['Phys_Score'] * weights['Physical'] + 
                 df['Ment_Score'] * weights['Mental'])
    return df

def generate_pdf_report(player_data, radar_img_bytes):
    """Generates PDF using memory buffers to avoid Permission Errors"""
    pdf = FPDF()
    pdf.add_page()
    
    # Branding
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'RWANDA PERFORMANCE SCOUTING REPORT', ln=True, align='C')
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 10, 'Official Analytics Platform - 2025/26 Season', ln=True, align='C')
    pdf.line(10, 30, 200, 30)
    
    # Player Stats
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"PLAYER: {player_data['player_name'].upper()}", ln=True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Position: {player_data.get('position', 'Pro Player')}", ln=True)
    pdf.cell(0, 8, f"Total Performance Index (TPI): {player_data['TPI']:.1f} / 100", ln=True)
    
    # Insert Radar Image from Buffer
    # We save buffer to a temp name string that FPDF treats as a virtual file
    with open("temp_radar.png", "wb") as f:
        f.write(radar_img_bytes)
    pdf.image("temp_radar.png", x=110, y=45, w=85)
    
    # Pillar Breakdown
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 11)
    for pillar in ['Technical', 'Tactical', 'Physical', 'Mental']:
        score = player_data[f'{pillar[:4]}_Score'] # Matches Tech_Score, Tact_Score etc.
        pdf.cell(40, 10, f"{pillar}:", border=0)
        pdf.cell(20, 10, f"{score:.1f}", border=0, ln=True)

    return pdf.output(dest='S').encode('latin-1')

# --- 2. USER INTERFACE ---
st.title("⚽ Rwanda Football Analytics Platform")
uploaded_file = st.sidebar.file_uploader("Upload Player Data (CSV)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = calculate_tpi(df)
    
    selected_player = st.selectbox("Select Player to Analyze", df['player_name'].unique())
    player_data = df[df['player_name'] == selected_player].iloc[0]
    
    # Create Radar Chart
    categories = ['Technical', 'Tactical', 'Physical', 'Mental']
    values = [player_data['Tech_Score'], player_data['Tact_Score'], 
              player_data['Phys_Score'], player_data['Ment_Score']]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name=selected_player))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.metric("Total TPI", f"{player_data['TPI']:.1f}")
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.write("### Scouting Summary")
        st.write(f"This report evaluates **{selected_player}** based on Rwanda Premier League standards.")
        
        # PDF Generation Button
        try:
            # Generate the image bytes first
            img_bytes = fig.to_image(format="png", engine="kaleido")
            
            if st.button("Generate Professional PDF"):
                pdf_output = generate_pdf_report(player_data, img_bytes)
                st.download_button(
                    label="⬇️ Download PDF Report",
                    data=pdf_output,
                    file_name=f"{selected_player}_Scouting_Report.pdf",
                    mime="application/pdf"
                )
                st.balloons()
        except Exception as e:
            st.error("The PDF engine is warming up. Please refresh the page in 30 seconds.")
            st.info("Technical Note: Ensure 'kaleido==0.2.1' is in your requirements.txt")

else:
    st.info("Welcome! Please upload a CSV file in the sidebar to begin analysis.")

# --- ADD TO YOUR UI SECTION ---
st.sidebar.subheader("Comparison Mode")
compare_mode = st.sidebar.checkbox("Enable Player Comparison")

if compare_mode:
    player_b_name = st.sidebar.selectbox("Select Player B", df['player_name'].unique(), index=1)
    player_b_data = df[df['player_name'] == player_b_name].iloc[0]
    
    # Add Player B to the Radar Chart
    values_b = [player_b_data['Tech_Score'], player_b_data['Tact_Score'], 
                player_b_data['Phys_Score'], player_b_data['Ment_Score']]
    
    fig.add_trace(go.Scatterpolar(
        r=values_b, 
        theta=categories, 
        fill='toself', 
        name=player_b_name,
        line_color='red' # You can set this to rival club colors!
    ))
    fig.update_layout(showlegend=True)
