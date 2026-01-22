import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- 1. UI CONFIGURATION ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 20px; border-radius: 10px; }
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

def generate_pdf(p1, p2=None, chart_bytes=None, compare_mode=False):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(33, 37, 41) 
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font('Arial', 'B', 20); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 20, 'RPL SCOUTING EXECUTIVE REPORT', align='C', ln=True)
    pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 14)
    title = f"ANALYSIS: {p1['player_name']} vs {p2['player_name']}" if compare_mode else f"ANALYSIS: {p1['player_name']}"
    pdf.cell(0, 10, title, ln=True)
    pdf.ln(5); pdf.set_font('Arial', 'B', 12); pdf.set_fill_color(233, 236, 239)
    pdf.cell(50, 10, "Metric", 1, 0, 'C', True); pdf.cell(50, 10, p1['player_name'], 1, 0, 'C', True)
    if compare_mode: pdf.cell(50, 10, p2['player_name'], 1, 0, 'C', True)
    pdf.ln(); pdf.set_font('Arial', '', 11)
    for m in ['Technical', 'Tactical', 'Physical', 'Mental', 'TPI']:
        key = f"{m[:4]}_Score" if m != 'TPI' else 'TPI'
        pdf.cell(50, 10, m, 1); pdf.cell(50, 10, f"{p1[key]:.1f}", 1, 0, 'C')
        if compare_mode: pdf.cell(50, 10, f"{p2[key]:.1f}", 1, 0, 'C')
        pdf.ln()
    if chart_bytes:
        img_buffer = io.BytesIO(chart_bytes)
        pdf.image(img_buffer, x=10, y=120, w=190)
    return pdf.output(dest='S').encode('latin-1')

# --- UI LOGIC ---
st.sidebar.title("💎 RPL ELITE")
uploaded_file = st.sidebar.file_uploader("UPLOAD DATASET (CSV)", type="csv")

if uploaded_file:
    raw_df = pd.read_csv(uploaded_file)
    df, elite_stats = calculate_analytics(raw_df)
    tab_ind, tab_bench, tab_sqd = st.tabs(["👤 INDIVIDUAL ANALYSIS", "📊 ELITE BENCHMARK", "📋 SQUAD HEALTH"])

    with tab_ind:
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1: p1_name = st.selectbox("PRIMARY PLAYER", df['player_name'].unique(), key="p1")
        with col_ctrl2: compare_mode = st.checkbox("ENABLE PLAYER COMPARISON")
        
        p1_data = df[df['player_name'] == p1_name].iloc[0]
        categories = ['Technical', 'Tactical', 'Physical', 'Mental']
        fig = go.Figure()
        fig.add_trace(go.Bar(y=categories, x=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']], orientation='h', name=p1_name, marker_color='#212529'))
        
        p2_data = None
        if compare_mode:
            p2_name = st.selectbox("COMPARISON PLAYER", df['player_name'].unique(), index=1, key="p2")
            p2_data = df[df['player_name'] == p2_name].iloc[0]
            fig.add_trace(go.Bar(y=categories, x=[p2_data['Tech_Score'], p2_data['Tact_Score'], p2_data['Phys_Score'], p2_data['Ment_Score']], orientation='h', name=p2_name, marker_color='#D00000'))

        fig.update_layout(barmode='group', xaxis_range=[0,100], paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        c_chart, c_stats = st.columns([2, 1])
        with c_chart: st.plotly_chart(fig, use_container_width=True)
        with c_stats:
            st.metric(f"{p1_name} TPI", f"{p1_data['TPI']:.1f}")
            if compare_mode: st.metric(f"{p2_name} TPI", f"{p2_data['TPI']:.1f}", delta=f"{p2_data['TPI'] - p1_data['TPI']:.1f}")
            if st.button("📄 GENERATE PDF REPORT"):
                try:
                    img_bytes = fig.to_image(format="png", engine="kaleido")
                    pdf_data = generate_pdf(p1_data, p2_data, img_bytes, compare_mode)
                    st.download_button("📥 DOWNLOAD PDF", pdf_data, f"{p1_name}_Report.pdf", "application/pdf")
                except Exception as e: st.error(f"Error: {e}")

    with tab_bench:
        st.subheader("Comparison vs. League Elite (Top 5 Average)")
        fig_bench = go.Figure()
        fig_bench.add_trace(go.Bar(y=categories, x=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']], orientation='h', name=p1_name, marker_color='#212529'))
        fig_bench.add_trace(go.Bar(y=categories, x=elite_stats.values, orientation='h', name="League Elite", marker_color='#adb5bd'))
        fig_bench.update_layout(barmode='group', xaxis_range=[0,100])
        st.plotly_chart(fig_bench, use_container_width=True)

    with tab_sqd:
        st.header("📋 Squad Strategic Overview")
        
        # Talent Map
        fig_sq = go.Figure(data=go.Scatter(x=df['Phys_Score'], y=df['TPI'], mode='markers+text', text=df['player_name'], textposition="top center", marker=dict(size=14, color=df['TPI'], colorscale='Viridis', showscale=True)))
        st.plotly_chart(fig_sq, use_container_width=True)
        
        col_depth, col_injury = st.columns(2)
        
        with col_depth:
            st.subheader("📊 Squad Depth Analysis")
            if 'position' in df.columns:
                pos_counts = df['position'].value_counts()
                fig_pie = go.Figure(data=[go.Pie(labels=pos_counts.index, values=pos_counts.values, hole=.3)])
                fig_pie.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.warning("Position column not found for depth analysis.")
        
        with col_injury:
            st.subheader("⚠️ Medical & Fatigue Alerts")
            low_phys = df[df['Phys_Score'] < 65]
            if not low_phys.empty:
                for _, p in low_phys.iterrows():
                    st.error(f"**Risk:** {p['player_name']} - Physical: {p['Phys_Score']:.1f}. Recommend Rest.")
            else:
                st.success("All players meet physical readiness thresholds.")
