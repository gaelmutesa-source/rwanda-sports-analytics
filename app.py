import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- 1. SETTINGS ---
st.set_page_config(page_title="Rwanda Sports Analytics Elite", layout="wide")

def calculate_analytics(df):
    """Restored exact Pillar Weightings: Tech (35%), Tact (25%), Phys (25%), Ment (15%)"""
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    
    # Fill numeric gaps with medians
    df_numeric = df.select_dtypes(include=['number'])
    df = df.fillna(df_numeric.median())

    # Pillar Formula Logic
    df['Tech_Score'] = df.get('pass_accuracy', 50) * 0.6 + df.get('dribble_success', 50) * 0.4
    df['Tact_Score'] = (df.get('interceptions', 5) * 5) + (df.get('positioning_rating', 50) * 0.5)
    df['Phys_Score'] = (df.get('sprint_speed', 25) * 2) + (df.get('stamina', 50) * 0.2)
    df['Ment_Score'] = (df.get('composure', 70) * 0.7) + (df.get('big_game_impact', 50) * 0.3)
    
    # Final TPI (Total Performance Index)
    df['TPI'] = (
        (df['Tech_Score'] * weights['Technical']) + 
        (df['Tact_Score'] * weights['Tactical']) + 
        (df['Phys_Score'] * weights['Physical']) + 
        (df['Ment_Score'] * weights['Mental'])
    )
    
    df['Rank_Percentile'] = df['TPI'].rank(pct=True) * 100
    return df

def generate_pdf_report(p1, p2, chart_bytes, compare_mode):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'OFFICIAL PERFORMANCE REPORT', ln=True, align='C')
    pdf.line(10, 25, 200, 25)
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    title = f"{p1['player_name']} vs {p2['player_name']}" if compare_mode else f"Scouting Report: {p1['player_name']}"
    pdf.cell(0, 10, title, ln=True)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, 'Metric', 1); pdf.cell(40, 10, p1['player_name'], 1)
    if compare_mode: pdf.cell(40, 10, p2['player_name'], 1)
    pdf.ln()
    
    pdf.set_font('Arial', '', 10)
    for m in ['Technical', 'Tactical', 'Physical', 'Mental', 'TPI']:
        key = f"{m[:4]}_Score" if m != 'TPI' else 'TPI'
        pdf.cell(40, 10, m, 1); pdf.cell(40, 10, f"{p1[key]:.1f}", 1)
        if compare_mode: pdf.cell(40, 10, f"{p2[key]:.1f}", 1)
        pdf.ln()
    
    with open("temp_chart.png", "wb") as f: f.write(chart_bytes)
    pdf.image("temp_chart.png", x=15, y=100, w=180)
    return pdf.output(dest='S').encode('latin-1')

# --- 2. MAIN APP UI ---
st.title("⚽ Rwanda Football Analytics Hub")
uploaded_file = st.sidebar.file_uploader("Upload Match Data (CSV)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = calculate_analytics(df)
    
    # TABS FOR SQUAD HEALTH AND INDIVIDUAL VIEW
    tab_ind, tab_sqd = st.tabs(["👤 Individual Analysis", "📋 Squad Health View"])

    with tab_ind:
        st.header("Player Performance & Comparison")
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            p1_name = st.selectbox("Select Primary Player", df['player_name'].unique(), key="sel_p1")
        with col_ctrl2:
            compare_mode = st.checkbox("Enable Comparison Mode", key="tog_comp")
        
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
            
            # --- UPDATED: HOW TO READ THE DATA ---
            with st.expander("📚 Analytics Glossary: How to interpret these scores"):
                st.subheader("The Four Pillars")
                st.write("**1. Technical (35%):** Measures efficiency with the ball. High scores indicate elite passing accuracy and dribble success rates.")
                st.write("**2. Tactical (25%):** Measures 'Football IQ.' High scores indicate superior positioning and defensive anticipation (interceptions).")
                st.write("**3. Physical (25%):** Measures raw athletic output. High scores indicate top-tier sprint speeds and the stamina to play 90+ minutes.")
                st.write("**4. Mental (15%):** Measures composure and reliability. This identifies players who perform in big match moments without making errors.")
                st.info("💡 **TPI (Total Performance Index):** An overall score out of 100. Over 80 = National Team Standard; 60-70 = Professional Starter; <50 = Needs Intervention.")

        with c2:
            st.metric(f"{p1_name} TPI", f"{p1_data['TPI']:.1f}")
            if compare_mode and p2_data is not None:
                st.metric(f"{p2_name} TPI", f"{p2_data['TPI']:.1f}", delta=f"{p2_data['TPI'] - p1_data['TPI']:.1f}")
            if st.button("📄 Generate PDF Report"):
                try:
                    img_bytes = fig.to_image(format="png", engine="kaleido")
                    pdf_data = generate_pdf_report(p1_data, p2_data, img_bytes, compare_mode)
                    st.download_button("📥 Download PDF", pdf_data, f"{p1_name}_Report.pdf", "application/pdf")
                except: st.error("Engine warming up...")

    with tab_sqd:
        st.header("📋 Squad Strategic Overview")
        st.markdown("This view provides the Technical Director with a birds-eye view of team balance.")
        
        # Talent Map
        fig_scatter = go.Figure()
        fig_scatter.add_trace(go.Scatter(x=df['Phys_Score'], y=df['TPI'], mode='markers+text', text=df['player_name'], textposition="top center", marker=dict(size=14, color=df['TPI'], colorscale='Plasma', showscale=True)))
        fig_scatter.update_layout(title="Talent Map: Efficiency (TPI) vs Readiness (Physical)", xaxis_title="Physical Condition", yaxis_title="Performance Index")
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Risk & Fatigue
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.subheader("Positional Depth")
            pos_counts = df['position'].value_counts()
            st.plotly_chart(go.Figure(data=[go.Pie(labels=pos_counts.index, values=pos_counts.values, hole=.3)]), use_container_width=True)
        with col_s2:
            st.subheader("⚠️ Fatigue Alerts")
            low_phys = df[df['Phys_Score'] < 65]
            if not low_phys.empty:
                for _, p in low_phys.iterrows(): st.warning(f"**{p['player_name']}** - Physical: {p['Phys_Score']:.1f}")
            else: st.success("The entire squad is currently meeting the Physical Baseline.")

else:
    st.info("Welcome to Rwanda Sports Analytics. Please upload a CSV file to generate reports.")
