import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- 1. SETTINGS & STYLING ---
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

# --- NEW PROFESSIONAL PDF ENGINE ---
class RPL_Report(FPDF):
    def header(self):
        self.set_fill_color(0, 51, 102) # Dark Navy
        self.rect(0, 0, 210, 30, 'F')
        self.set_font('Arial', 'B', 15)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'RWANDA SPORTS ANALYTICS ELITE', ln=True, align='C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, 'Professional Performance & Scouting Division', ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Proprietary Data - Confidential', align='C')

def generate_pdf_report(p1, p2, chart_bytes, compare_mode):
    pdf = RPL_Report()
    pdf.add_page()
    pdf.ln(15)
    
    # Summary Section
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 0, 0)
    title = f"SCOUTING REPORT: {p1['player_name']} vs {p2['player_name']}" if compare_mode else f"SCOUTING REPORT: {p1['player_name']}"
    pdf.cell(0, 10, title, ln=True)
    pdf.ln(5)

    # Professional Table
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(50, 10, 'Performance Pillar', 1, 0, 'C', True)
    pdf.cell(60, 10, p1['player_name'], 1, 0, 'C', True)
    if compare_mode:
        pdf.cell(60, 10, p2['player_name'], 1, 0, 'C', True)
    pdf.ln()

    pdf.set_font('Arial', '', 10)
    for m in ['Technical', 'Tactical', 'Physical', 'Mental', 'TPI']:
        key = f"{m[:4]}_Score" if m != 'TPI' else 'TPI'
        pdf.cell(50, 10, m, 1)
        # Highlight high scores
        val1 = p1[key]
        if val1 > 80: pdf.set_text_color(0, 128, 0) # Green
        pdf.cell(60, 10, f"{val1:.1f}", 1, 0, 'C')
        pdf.set_text_color(0, 0, 0)
        
        if compare_mode:
            val2 = p2[key]
            if val2 > 80: pdf.set_text_color(0, 128, 0)
            pdf.cell(60, 10, f"{val2:.1f}", 1, 0, 'C')
            pdf.set_text_color(0, 0, 0)
        pdf.ln()

    # Image (Bar Chart) - Centered and Large
    with open("temp_chart.png", "wb") as f: f.write(chart_bytes)
    pdf.ln(10)
    pdf.image("temp_chart.png", x=15, w=180)
    
    return pdf.output(dest='S').encode('latin-1')

def generate_squad_report(df, scatter_bytes):
    pdf = RPL_Report()
    pdf.add_page()
    pdf.ln(15)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'SQUAD STRATEGIC HEALTH SUMMARY', ln=True)
    
    # Visual
    with open("temp_squad.png", "wb") as f: f.write(scatter_bytes)
    pdf.image("temp_squad.png", x=15, y=55, w=180)
    
    # Fatigue List at Bottom
    pdf.set_y(160)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(200, 0, 0) # Red for warnings
    pdf.cell(0, 10, 'CRITICAL FATIGUE & READINESS WARNINGS:', ln=True)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    
    low_phys = df[df['Phys_Score'] < 65]
    for _, p in low_phys.iterrows():
        pdf.cell(0, 7, f"- {p['player_name']} ({p['position']}): Readiness Index {p['Phys_Score']:.1f}%", ln=True)

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
            with st.expander("📚 Analytics Glossary"):
                st.write("**Technical (35%):** Skill & Passing. **Tactical (25%):** Intelligence. **Physical (25%):** Speed & Power. **Mental (15%):** Composure.")
        with c2:
            st.metric(f"{p1_name} TPI", f"{p1_data['TPI']:.1f}")
            if st.button("📄 Generate Pro Individual PDF"):
                try:
                    img_bytes = fig.to_image(format="png", engine="kaleido")
                    pdf_data = generate_pdf_report(p1_data, p2_data, img_bytes, compare_mode)
                    st.download_button("📥 Download PDF", pdf_data, f"{p1_name}_Pro_Report.pdf", "application/pdf")
                except: st.error("Engine warming up...")

    with tab_sqd:
        st.header("📋 Squad Strategic Overview")
        fig_scatter = go.Figure()
        fig_scatter.add_trace(go.Scatter(x=df['Phys_Score'], y=df['TPI'], mode='markers+text', text=df['player_name'], textposition="top center", marker=dict(size=14, color=df['TPI'], colorscale='Plasma', showscale=True)))
        fig_scatter.update_layout(title="Squad Talent Map", xaxis_title="Physical Condition", yaxis_title="Performance Index")
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        if st.button("📄 Export Pro Squad Health Report"):
            try:
                s_img_bytes = fig_scatter.to_image(format="png", engine="kaleido")
                s_pdf_data = generate_squad_report(df, s_img_bytes)
                st.download_button("📥 Download Squad Report", s_pdf_data, "Squad_Health_Pro.pdf", "application/pdf")
            except: st.error("Engine error. Please ensure kaleido is stable.")
else:
    st.info("Please upload a CSV file to generate professional reports.")
