import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="Rwanda Sports Analytics Elite", layout="wide")

def calculate_analytics(df):
    """Calculates TPI and Percentile Rankings for the whole league"""
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    # Use numeric only for median to avoid errors with player names
    df_numeric = df.select_dtypes(include=['number'])
    df = df.fillna(df_numeric.median())

    # Core Pillar Formulas
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

def generate_pdf_report(p1, p2, chart_bytes, compare_mode):
    """Stable PDF generation for individual or comparison reports"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'OFFICIAL PERFORMANCE REPORT', ln=True, align='C')
    pdf.line(10, 25, 200, 25)
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    title = f"{p1['player_name']} vs {p2['player_name']}" if compare_mode else f"Scouting Report: {p1['player_name']}"
    pdf.cell(0, 10, title, ln=True)
    
    # Table Header
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, 'Metric', 1)
    pdf.cell(40, 10, p1['player_name'], 1)
    if compare_mode:
        pdf.cell(40, 10, p2['player_name'], 1)
    pdf.ln()

    # Table Body
    pdf.set_font('Arial', '', 10)
    for m in ['Technical', 'Tactical', 'Physical', 'Mental', 'TPI']:
        key = f"{m[:4]}_Score" if m != 'TPI' else 'TPI'
        pdf.cell(40, 10, m, 1)
        pdf.cell(40, 10, f"{p1[key]:.1f}", 1)
        if compare_mode:
            pdf.cell(40, 10, f"{p2[key]:.1f}", 1)
        pdf.ln()

    # Insert Chart
    with open("temp_chart.png", "wb") as f:
        f.write(chart_bytes)
    pdf.image("temp_chart.png", x=15, y=100, w=180)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 2. MAIN APP UI ---
st.title("⚽ Rwanda Football Analytics Hub")
uploaded_file = st.sidebar.file_uploader("Upload Match Data (CSV)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = calculate_analytics(df)
    
    # Define Tabs
    tab1, tab2 = st.tabs(["👤 Individual Analysis", "📋 Squad Health View"])

    # --- TAB 1: INDIVIDUAL & COMPARISON ---
    with tab1:
        st.header("Player Performance & Comparison")
        
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            p1_name = st.selectbox("Select Primary Player", df['player_name'].unique(), key="p1_select")
        with col_ctrl2:
            compare_mode = st.checkbox("Enable Comparison Mode", key="compare_toggle")
        
        p1_data = df[df['player_name'] == p1_name].iloc[0]
        p2_data = None

        # Bar Chart Visualization
        categories = ['Technical', 'Tactical', 'Physical', 'Mental']
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=categories, 
            y=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']],
            name=p1_name, marker_color='#003366'
        ))

        if compare_mode:
            p2_name = st.selectbox("Select Comparison Player", df['player_name'].unique(), index=1, key="p2_select")
            p2_data = df[df['player_name'] == p2_name].iloc[0]
            fig.add_trace(go.Bar(
                x=categories, 
                y=[p2_data['Tech_Score'], p2_data['Tact_Score'], p2_data['Phys_Score'], p2_data['Ment_Score']],
                name=p2_name, marker_color='#FF8C00'
            ))

        fig.update_layout(barmode='group', yaxis_range=[0,100], title="KPI Breakdown")

        c1, c2 = st.columns([2, 1])
        with c1:
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("📚 How to read this data?"):
                st.write("**Technical:** Ball control & passing. **Tactical:** Positioning. **Physical:** Speed & Stamina. **Mental:** Composure.")
        
        with c2:
            st.metric(f"{p1_name} TPI", f"{p1_data['TPI']:.1f}")
            if compare_mode and p2_data is not None:
                st.metric(f"{p2_name} TPI", f"{p2_data['TPI']:.1f}", delta=f"{p2_data['TPI'] - p1_data['TPI']:.1f}")
            
            # PDF Generation
            if st.button("📄 Generate PDF Report"):
                try:
                    img_bytes = fig.to_image(format="png", engine="kaleido")
                    pdf_data = generate_pdf_report(p1_data, p2_data, img_bytes, compare_mode)
                    st.download_button("📥 Download PDF", pdf_data, f"{p1_name}_Report.pdf", "application/pdf")
                except:
                    st.error("Engine warming up... please try again in 5 seconds.")

    # --- TAB 2: SQUAD HEALTH ---
    with tab2:
        st.header("📋 Squad Strategic Overview")
        
        # Talent Map Scatter Plot
        st.subheader("Efficiency vs. Impact Map")
        fig_scatter = go.Figure()
        fig_scatter.add_trace(go.Scatter(
            x=df['Phys_Score'], y=df['TPI'],
            mode='markers+text', text=df['player_name'],
            textposition="top center",
            marker=dict(size=12, color=df['TPI'], colorscale='Viridis', showscale=True)
        ))
        fig_scatter.update_layout(xaxis_title="Physical Readiness", yaxis_title="Total Performance Index")
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Squad Depth & Fatigue
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.subheader("Squad Depth (Positions)")
            pos_counts = df['position'].value_counts()
            fig_pie = go.Figure(data=[go.Pie(labels=pos_counts.index, values=pos_counts.values, hole=.3)])
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_s2:
            st.subheader("⚠️ Fatigue Warning")
            low_phys = df[df['Phys_Score'] < 65]
            if not low_phys.empty:
                for _, p in low_phys.iterrows():
                    st.warning(f"**{p['player_name']}** - Physical Score: {p['Phys_Score']:.1f}")
            else:
                st.success("All players are currently in peak physical condition.")

else:
    st.info("Please upload a CSV file in the sidebar to view analytics.")
