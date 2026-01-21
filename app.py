import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- 1. SETTINGS & DARK THEME UI ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0B0C10; color: #C5C6C7; }
    .stMetric { background-color: #1F2833; border: 1px solid #45A29E; padding: 20px; border-radius: 12px; }
    [data-testid="stSidebar"] { background-color: #0B0C10; border-right: 1px solid #45A29E; }
    .stTabs [data-baseweb="tab-list"] { background-color: #1F2833; border-radius: 8px; }
    div[data-testid="stExpander"] { background-color: #1F2833; border: none; }
    h1, h2, h3 { color: #66FCF1 !important; }
    </style>
    """, unsafe_allow_index=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    df_numeric = df.select_dtypes(include=['number'])
    df = df.fillna(df_numeric.median())
    
    # Pillar Logic
    df['Tech_Score'] = df.get('pass_accuracy', 50) * 0.6 + df.get('dribble_success', 50) * 0.4
    df['Tact_Score'] = (df.get('interceptions', 5) * 5) + (df.get('positioning_rating', 50) * 0.5)
    df['Phys_Score'] = (df.get('sprint_speed', 25) * 2) + (df.get('stamina', 50) * 0.2)
    df['Ment_Score'] = (df.get('composure', 70) * 0.7) + (df.get('big_game_impact', 50) * 0.3)
    
    df['TPI'] = (df['Tech_Score'] * weights['Technical'] + df['Tact_Score'] * weights['Tactical'] + 
                 df['Phys_Score'] * weights['Physical'] + df['Ment_Score'] * weights['Mental'])
    
    # Calculate League Elite (Average of Top 5 Players for Benchmarking)
    league_elite = df.nlargest(5, 'TPI')[['Tech_Score', 'Tact_Score', 'Phys_Score', 'Ment_Score']].mean()
    return df, league_elite

# --- 2. EXECUTIVE PDF ENGINE ---
class RPL_Executive_Report(FPDF):
    def header(self):
        self.set_fill_color(11, 12, 16)
        self.rect(0, 0, 210, 35, 'F')
        self.set_font('Arial', 'B', 20)
        self.set_text_color(102, 252, 241) # Cyan
        self.cell(0, 15, 'RPL SCOUTING: EXECUTIVE SUMMARY', ln=True, align='C')
        self.ln(20)

def generate_pdf(p1, elite_stats, chart_bytes):
    pdf = RPL_Executive_Report()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"PLAYER ANALYSIS: {p1['player_name']}", ln=True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Status: Scouting Priority | Current TPI: {p1['TPI']:.1f}", ln=True)
    
    with open("temp_exec.png", "wb") as f: f.write(chart_bytes)
    pdf.image("temp_exec.png", x=10, y=60, w=190)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. DASHBOARD UI ---
st.sidebar.title("💎 RPL ELITE")
uploaded_file = st.sidebar.file_uploader("UPLOAD MATCH DATA", type="csv")

if uploaded_file:
    df, elite_stats = calculate_analytics(pd.read_csv(uploaded_file))
    
    tab_ind, tab_bench, tab_sqd = st.tabs(["👤 PLAYER PROFILE", "📊 ELITE BENCHMARK", "📋 SQUAD STRATEGY"])

    with tab_ind:
        p1_name = st.selectbox("SELECT PLAYER", df['player_name'].unique())
        p1_data = df[df['player_name'] == p1_name].iloc[0]
        
        # Performance KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("TOTAL TPI", f"{p1_data['TPI']:.1f}")
        c2.metric("TECHNICAL", f"{p1_data['Tech_Score']:.1f}")
        c3.metric("PHYSICAL", f"{p1_data['Phys_Score']:.1f}")
        c4.metric("TACTICAL", f"{p1_data['Tact_Score']:.1f}")

        # Horizontal Comparison Bar Chart
        categories = ['Technical', 'Tactical', 'Physical', 'Mental']
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=categories, x=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']],
            orientation='h', name=p1_name, marker_color='#66FCF1'
        ))
        fig.update_layout(template="plotly_dark", barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with tab_bench:
        st.subheader("Comparison vs. League Elite (Top 5 Avg)")
        fig_bench = go.Figure()
        fig_bench.add_trace(go.Bar(
            y=categories, x=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']],
            orientation='h', name=p1_name, marker_color='#66FCF1'
        ))
        fig_bench.add_trace(go.Bar(
            y=categories, x=elite_stats.values,
            orientation='h', name="League Elite", marker_color='#45A29E'
        ))
        fig_bench.update_layout(template="plotly_dark", barmode='group', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bench, use_container_width=True)
        
        if st.button("DOWNLOAD EXECUTIVE REPORT"):
            img_bytes = fig_bench.to_image(format="png", engine="kaleido")
            pdf_bytes = generate_pdf(p1_data, elite_stats, img_bytes)
            st.download_button("📥 DOWNLOAD PDF", pdf_bytes, f"{p1_name}_Elite_Report.pdf")

    with tab_sqd:
        st.subheader("SQUAD HEALTH MAP")
        fig_sq = go.Figure(data=go.Scatter(
            x=df['Phys_Score'], y=df['TPI'], mode='markers+text',
            text=df['player_name'], marker=dict(size=15, color='#66FCF1')
        ))
        fig_sq.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_sq, use_container_width=True)

else:
    st.info("System Ready. Please upload CSV Match Data.")
