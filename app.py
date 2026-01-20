import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Rwanda Sports Analytics Elite", layout="wide")

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    df = df.fillna(df.median(numeric_only=True)) 
    
    df['Tech_Score'] = df.get('pass_accuracy', 50) * 0.6 + df.get('dribble_success', 50) * 0.4
    df['Tact_Score'] = (df.get('interceptions', 5) * 5) + (df.get('positioning_rating', 50) * 0.5)
    df['Phys_Score'] = (df.get('sprint_speed', 25) * 2) + (df.get('stamina', 50) * 0.2)
    df['Ment_Score'] = (df.get('composure', 70) * 0.7) + (df.get('big_game_impact', 50) * 0.3)
    
    df['TPI'] = (df['Tech_Score'] * weights['Technical'] + df['Tact_Score'] * weights['Tactical'] + 
                 df['Phys_Score'] * weights['Physical'] + df['Ment_Score'] * weights['Mental'])
    
    df['Rank_Percentile'] = df['TPI'].rank(pct=True) * 100
    return df

def generate_pdf_report(p1, p2, chart_bytes, compare_mode):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'OFFICIAL PLAYER COMPARISON REPORT', ln=True, align='C')
    pdf.line(10, 25, 200, 25)
    
    # Comparison Details
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    title = f"{p1['player_name']} vs {p2['player_name']}" if compare_mode else f"Scouting Report: {p1['player_name']}"
    pdf.cell(0, 10, title, ln=True)
    
    # Data Table
    pdf.set_font('Arial', '', 10)
    pdf.cell(40, 10, 'Metric', 1)
    pdf.cell(40, 10, p1['player_name'], 1)
    if compare_mode:
        pdf.cell(40, 10, p2['player_name'], 1)
    pdf.ln()

    for m in ['Technical', 'Tactical', 'Physical', 'Mental', 'TPI']:
        key = f"{m[:4]}_Score" if m != 'TPI' else 'TPI'
        pdf.cell(40, 10, m, 1)
        pdf.cell(40, 10, f"{p1[key]:.1f}", 1)
        if compare_mode:
            pdf.cell(40, 10, f"{p2[key]:.1f}", 1)
        pdf.ln()

    # Insert Bar Chart
    with open("temp_chart.png", "wb") as f:
        f.write(chart_bytes)
    pdf.image("temp_chart.png", x=15, y=100, w=180)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 2. UI ---
st.title("⚽ Rwanda Football Analytics Hub")
uploaded_file = st.sidebar.file_uploader("Upload CSV Data", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = calculate_analytics(df)
    
    p1_name = st.sidebar.selectbox("Select Primary Player", df['player_name'].unique())
    compare_mode = st.sidebar.checkbox("Enable Player Comparison")
    p1_data = df[df['player_name'] == p1_name].iloc[0]
    
    # Visualization: Grouped Bar Chart
    categories = ['Technical', 'Tactical', 'Physical', 'Mental']
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=categories, 
        y=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']],
        name=p1_name, marker_color='#003366'
    ))

    p2_data = None
    if compare_mode:
        p2_name = st.sidebar.selectbox("Select Comparison Player", df['player_name'].unique(), index=1)
        p2_data = df[df['player_name'] == p2_name].iloc[0]
        fig.add_trace(go.Bar(
            x=categories, 
            y=[p2_data['Tech_Score'], p2_data['Tact_Score'], p2_data['Phys_Score'], p2_data['Ment_Score']],
            name=p2_name, marker_color='#FF8C00'
        ))

    fig.update_layout(barmode='group', yaxis_range=[0,100], title="Performance Breakdown")

    # Layout
    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
        
        # --- DATA INTERPRETATION SECTION ---
        with st.expander("📚 How to read this data?"):
            st.write("**Technical:** Ball control and passing accuracy.")
            st.write("**Tactical:** Positioning and defensive intelligence.")
            st.write("**Physical:** Speed, stamina, and power.")
            st.write("**Mental:** Composure under pressure and leadership.")
            st.info("A score above 70 is considered 'League Professional' standard.")

    with col2:
        st.metric(f"{p1_name} TPI", f"{p1_data['TPI']:.1f}")
        if compare_mode:
            st.metric(f"{p2_name} TPI", f"{p2_data['TPI']:.1f}", 
                      delta=f"{p2_data['TPI'] - p1_data['TPI']:.1f}")
        
        # PDF Trigger
        if st.button("📄 Generate Comparison PDF"):
            try:
                img_bytes = fig.to_image(format="png", engine="kaleido")
                pdf_data = generate_pdf_report(p1_data, p2_data, img_bytes, compare_mode)
                st.download_button("📥 Download Report", pdf_data, f"Comparison_{p1_name}.pdf", "application/pdf")
            except:
                st.error("Engine warming up...")

else:
    st.info("Please upload a CSV file to begin.")

# --- NEW: SQUAD HEALTH LOGIC ---
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = calculate_analytics(df)
    
    # Create Tabs for different views
    tab1, tab2 = st.tabs(["Individual Analysis", "Squad Health View"])

    with tab1:
        # (Keep your existing Player Comparison and Bar Chart code here)
        st.write("Use this tab for detailed scouting and comparisons.")

    with tab2:
        st.header("📋 Squad Strategic Overview")
        
        # 1. SQUAD TALENT MAP (Efficiency vs. Impact)
        st.subheader("Squad Performance Distribution")
        fig_scatter = go.Figure()
        fig_scatter.add_trace(go.Scatter(
            x=df['Phys_Score'], 
            y=df['TPI'],
            mode='markers+text',
            text=df['player_name'],
            textposition="top center",
            marker=dict(size=12, color=df['TPI'], colorscale='Viridis', showscale=True)
        ))
        fig_scatter.update_layout(
            title="Physical Output vs. Total Impact",
            xaxis_title="Physical Score (Stamina/Speed)",
            yaxis_title="Total Performance Index (TPI)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        # 2. INJURY RISK / FATIGUE MONITOR
        st.subheader("⚠️ Physical Readiness & Injury Risk")
        
        # Define a 'Risk' threshold (e.g., players with Physical Score < 50)
        risk_df = df[df['Phys_Score'] < 60].sort_values(by='Phys_Score')
        
        if not risk_df.empty:
            cols = st.columns(len(risk_df))
            for i, row in enumerate(risk_df.iterrows()):
                player = row[1]
                with cols[i % 3]:
                    st.warning(f"**{player['player_name']}**")
                    st.caption(f"Physical: {player['Phys_Score']:.1f}")
                    st.progress(player['Phys_Score'] / 100)
        else:
            st.success("All players are currently meeting the physical baseline.")

        # 3. POSITION DENSITY
        st.subheader("Squad Depth Analysis")
        pos_counts = df['position'].value_counts()
        fig_pie = go.Figure(data=[go.Pie(labels=pos_counts.index, values=pos_counts.values, hole=.3)])
        st.plotly_chart(fig_pie)
