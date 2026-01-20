import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- 1. SETTINGS ---
st.set_page_config(page_title="Rwanda Sports Analytics Elite", layout="wide")

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    df_numeric = df.select_dtypes(include=['number'])
    df = df.fillna(df_numeric.median())

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
    pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, 'INDIVIDUAL PERFORMANCE REPORT', ln=True, align='C')
    pdf.line(10, 25, 200, 25); pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    title = f"{p1['player_name']} vs {p2['player_name']}" if compare_mode else f"Scouting Report: {p1['player_name']}"
    pdf.cell(0, 10, title, ln=True)
    pdf.set_font('Arial', 'B', 10); pdf.cell(40, 10, 'Metric', 1); pdf.cell(40, 10, p1['player_name'], 1)
    if compare_mode: pdf.cell(40, 10, p2['player_name'], 1)
    pdf.ln()
    for m in ['Technical', 'Tactical', 'Physical', 'Mental', 'TPI']:
        key = f"{m[:4]}_Score" if m != 'TPI' else 'TPI'
        pdf.cell(40, 10, m, 1); pdf.cell(40, 10, f"{p1[key]:.1f}", 1)
        if compare_mode: pdf.cell(40, 10, f"{p2[key]:.1f}", 1)
        pdf.ln()
    with open("temp_p_chart.png", "wb") as f: f.write(chart_bytes)
    pdf.image("temp_p_chart.png", x=15, y=100, w=180)
    return pdf.output(dest='S').encode('latin-1')

def generate_squad_report(df, scatter_bytes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, 'SQUAD STRATEGIC HEALTH REPORT', ln=True, align='C')
    pdf.line(10, 25, 200, 25); pdf.ln(10)
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, 'Squad Talent Map Overview', ln=True)
    with open("temp_s_chart.png", "wb") as f: f.write(scatter_bytes)
    pdf.image("temp_s_chart.png", x=15, y=45, w=180)
    pdf.set_y(150)
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, 'Critical Fatigue Warnings:', ln=True)
    pdf.set_font('Arial', '', 10)
    low_phys = df[df['Phys_Score'] < 65]
    for _, p in low_phys.iterrows():
        pdf.cell(0, 8, f"- {p['player_name']}: Physical Readiness Score {p['Phys_Score']:.1f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 2. MAIN APP UI ---
st.title("⚽ Rwanda Football Analytics Hub")
uploaded_file = st.sidebar.file_uploader("Upload Match Data (CSV)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = calculate_analytics(df)
    tab_ind, tab_sqd = st.tabs(["👤 Individual Analysis", "📋 Squad Health View"])

    with tab_ind:
        st.header("Player Performance & Comparison")
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1: p1_name = st.selectbox("Select Primary Player", df['player_name'].unique(), key="sel_p1")
        with col_ctrl2: compare_mode = st.checkbox("Enable Comparison Mode", key="tog_comp")
        
        p1_data = df[df['player_name'] == p1_name].iloc[0]
        categories = ['Technical', 'Tactical', 'Physical', 'Mental']
        fig = go.Figure()
        fig.add_trace(go.Bar(x=categories, y=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']], name=p1_name, marker_color='#003366'))
        
        p2_data = None
        if compare_mode:
            p2_name = st.selectbox("Select Comparison Player", df['player_name'].unique(), index=1, key="sel_p2")
            p2_data = df[df['player_name'] == p2_name].iloc[0]
            fig.add_trace(go.Bar(x=categories, y=[p2_data['Tech_Score'], p2_data['Tact_Score'], p2_data['Phys_Score'], p2_data['Ment_Score']], name=p2_name, marker_color='#FF8C00'))

        fig.update_layout(barmode='group', yaxis_range=[0,100], title="KPI Pillar Breakdown")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("📚 Analytics Glossary: How to interpret these scores"):
                st.write("**Technical (35%):** Ball control & passing. **Tactical (25%):** Positioning & IQ. **Physical (25%):** Speed & Stamina. **Mental (15%):** Composure.")
        with c2:
            st.metric(f"{p1_name} TPI", f"{p1_data['TPI']:.1f}")
            if st.button("📄 Generate Individual PDF"):
                try:
                    img_bytes = fig.to_image(format="png", engine="kaleido")
                    pdf_data = generate_pdf_report(p1_data, p2_data, img_bytes, compare_mode)
                    st.download_button("📥 Download PDF", pdf_data, f"{p1_name}_Report.pdf", "application/pdf")
                except: st.error("Engine warming up...")

    with tab_sqd:
        st.header("📋 Squad Strategic Overview")
        fig_scatter = go.Figure()
        fig_scatter.add_trace(go.Scatter(x=df['Phys_Score'], y=df['TPI'], mode='markers+text', text=df['player_name'], textposition="top center", marker=dict(size=14, color=df['TPI'], colorscale='Plasma', showscale=True)))
        fig_scatter.update_layout(title="Talent Map: Efficiency (TPI) vs Readiness (Physical)", xaxis_title="Physical Condition", yaxis_title="Performance Index")
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        with st.expander("🔍 Understanding the Talent Map (Quadrant Analysis)"):
            st.write("### How to read this Map:")
            st.write("🎯 **Top-Right (The Elites):** High impact and peak physical condition. These are your 'Unstoppables'.")
            st.write("🧠 **Top-Left (The Geniuses):** High impact but lower physical scores. Often older, highly intelligent playmakers who rely on positioning.")
            st.write("🏃 **Bottom-Right (The Workhorses):** Great physical output but lower TPI. These players are fantastic athletes who need tactical training to improve their impact.")
            st.write("⚠️ **Bottom-Left (The Risks):** Low impact and low physical readiness. Potential candidates for rotation or extra training.")

        if st.button("📄 Export Squad Health Report"):
            try:
                s_img_bytes = fig_scatter.to_image(format="png", engine="kaleido")
                s_pdf_data = generate_squad_report(df, s_img_bytes)
                st.download_button("📥 Download Squad Report", s_pdf_data, "Squad_Health_Report.pdf", "application/pdf")
            except: st.error("Engine error. Please ensure kaleido==0.2.1 is installed.")
        
        col_s1, col_s2 = st.columns(2)
        with col_s2:
            st.subheader("⚠️ Fatigue Alerts")
            low_phys = df[df['Phys_Score'] < 65]
            if not low_phys.empty:
                for _, p in low_phys.iterrows(): st.warning(f"**{p['player_name']}** - Physical: {p['Phys_Score']:.1f}")
            else: st.success("All players in peak condition.")
