import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #F1F3F5; border-right: 1px solid #DEE2E6; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E9ECEF; border-radius: 8px; }
    .insight-box { background-color: #E7F3FF; padding: 15px; border-radius: 8px; border-left: 5px solid #007BFF; margin: 10px 0; }
    .recommendation-box { background-color: #FFF4E5; padding: 15px; border-radius: 8px; border-left: 5px solid #FF8C00; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    required = ['pass_accuracy', 'dribble_success', 'interceptions', 'positioning_rating', 'sprint_speed', 'stamina', 'composure', 'big_game_impact']
    for col in required:
        if col not in df.columns: df[col] = 50
    df_numeric = df.select_dtypes(include=['number'])
    df[df_numeric.columns] = df_numeric.fillna(df_numeric.median())
    
    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*weights['Technical'] + df['Tact_Score']*weights['Tactical'] + 
                 df['Phys_Score']*weights['Physical'] + df['Ment_Score']*weights['Mental'])
    
    team_avg = {'Technical': df['Tech_Score'].mean(), 'Tactical': df['Tact_Score'].mean(), 
                'Physical': df['Phys_Score'].mean(), 'Mental': df['Ment_Score'].mean(), 'TPI': df['TPI'].mean()}
    return df, team_avg

# --- 2. THE STABLE PDF ENGINE ---
def generate_pro_pdf(p_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(13, 27, 42) 
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font('Arial', 'B', 22); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 25, 'RPL PERFORMANCE ELITE', align='C', ln=True)
    pdf.ln(30); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"PLAYER: {p_data['player_name'].upper()}", ln=True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f"Club: {p_data.get('club', 'RPL Club')} | Age: {p_data.get('age', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Match Volume: {p_data.get('mins_played', 0)} mins | {p_data.get('distance', 0)} km covered", ln=True)
    
    # Scouting Verdict Table
    pdf.ln(10); pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(60, 10, "Metric", 1, 0, 'C', True); pdf.cell(60, 10, "Value", 1, 1, 'C', True)
    pdf.set_font('Arial', '', 11)
    for m in ['Goals', 'Assists', 'pass_accuracy', 'interceptions']:
        pdf.cell(60, 10, m.replace('_', ' ').title(), 1)
        pdf.cell(60, 10, str(p_data.get(m, 0)), 1, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. MAIN DASHBOARD ---
st.sidebar.title("💎 RPL ELITE")
file = st.sidebar.file_uploader("Upload Match Dataset", type="csv")

if file:
    df, team_avg = calculate_analytics(pd.read_csv(file))
    tabs = st.tabs(["👤 Profile", "📊 Performance Analysis", "⚽ Match Day Depth", "📋 Squad Health", "🏋️ Training Optimizer"])

    # --- TAB 1: PROFILE ---
    with tabs[0]:
        p_name = st.selectbox("Select Player", df['player_name'].unique(), key="p_prof")
        p_data = df[df['player_name'] == p_name].iloc[0]
        st.header(f"{p_data['player_name']} | {p_data.get('club', 'RPL Club')}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Appearances", int(p_data.get('appearances', 0)))
        c2.metric("Market Value", f"${p_data.get('market_value', 0):,}")
        c3.metric("TPI Score", f"{p_data['TPI']:.1f}")

        if st.button("📥 Download Executive PDF"):
            pdf = generate_pro_pdf(p_data)
            st.download_button("Confirm PDF Download", pdf, f"{p_name}_Report.pdf", "application/pdf")

    # --- TAB 2: PERFORMANCE ANALYSIS ---
    with tabs[1]:
        col1, col2 = st.columns(2)
        with col1: p1_n = st.selectbox("Primary Player", df['player_name'].unique(), key="p_an")
        with col2: compare = st.checkbox("Enable Comparison", key="p_comp")
        
        p1_d = df[df['player_name'] == p1_n].iloc[0]
        cats = ['Technical', 'Tactical', 'Physical', 'Mental']
        fig = go.Figure()
        fig.add_trace(go.Bar(x=cats, y=[p1_d['Tech_Score'], p1_d['Tact_Score'], p1_d['Phys_Score'], p1_d['Ment_Score']], name=p1_n, marker_color='#212529'))
        fig.add_trace(go.Scatter(x=cats, y=[team_avg['Technical'], team_avg['Tactical'], team_avg['Physical'], team_avg['Mental']], mode='lines+markers', name='Team Average', line=dict(color='#007BFF', dash='dash')))
        
        if compare:
            p2_n = st.selectbox("Compare With", df['player_name'].unique(), index=1, key="p_an2")
            p2_d = df[df['player_name'] == p2_n].iloc[0]
            fig.add_trace(go.Bar(x=cats, y=[p2_d['Tech_Score'], p2_d['Tact_Score'], p2_d['Phys_Score'], p2_d['Ment_Score']], name=p2_n, marker_color='#D00000'))
        
        fig.update_layout(title="Pillar Benchmarking", yaxis_title="Competency %")
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 3: MATCH DAY DEPTH ---
    with tabs[2]:
        p_match = st.selectbox("Detailed Match Performance", df['player_name'].unique(), key="p_match")
        m_d = df[df['player_name'] == p_match].iloc[0]
        
        # Volume Metrics
        v1, v2, v3, v4 = st.columns(4)
        v1.metric("Minutes Played", f"{int(m_d.get('mins_played', 0))} min")
        v2.metric("Passes Completed", int(m_d.get('passes_completed', 0)))
        v3.metric("Accuracy Rate", f"{m_d['pass_accuracy']}%")
        v4.metric("Interceptions", int(m_d.get('interceptions', 0)))
        
        # Phase Contribution Chart
        st.subheader("Phase Contribution (Defensive vs. Attacking)")
        fig_phase = go.Figure(go.Bar(
            x=['Defensive Contribution', 'Attacking Contribution'],
            y=[m_d.get('def_contribution', 50), m_d.get('atk_contribution', 50)],
            marker_color=['#1B263B', '#C0392B']
        ))
        st.plotly_chart(fig_phase, use_container_width=True)
        
        st.markdown(f"""<div class="insight-box"><b>Strategic Insight:</b> {p_match} recorded an <b>Attacking Contribution</b> of {m_d.get('atk_contribution', 0)}%. 
        This suggests they are a primary driver in the final third. Their <b>Accuracy Rate</b> of {m_d['pass_accuracy']}% proves they are reliable under pressure.</div>""", unsafe_allow_html=True)

    # --- TAB 4: SQUAD HEALTH ---
    with tabs[3]:
        st.header("📋 Squad Readiness Index")
        h_idx = df['Phys_Score'].mean()
        st.metric("Avg Readiness", f"{h_idx:.1f}%")
        
        low = df[df['Phys_Score'] < 65]
        for _, p in low.iterrows(): st.error(f"🚨 **Injury Risk:** {p['player_name']} ({p['Phys_Score']:.1f}%)")

    # --- TAB 5: TRAINING OPTIMIZER ---
    with tabs[4]:
        p_train = st.selectbox("Generate Training Plan", df['player_name'].unique(), key="p_train")
        pt_d = df[df['player_name'] == p_train].iloc[0]
        
        scores = {'Technical': pt_d['Tech_Score'], 'Tactical': pt_d['Tact_Score'], 'Physical': pt_d['Phys_Score'], 'Mental': pt_d['Ment_Score']}
        weakest_pillar = min(scores, key=scores.get)
        
        st.subheader(f"Focus Area: {weakest_pillar} Improvement")
        with st.container():
            st.markdown(f"""<div class="recommendation-box"><b>Coach's Action Plan for {p_train}:</b>
            <br>1. <b>Primary Drill:</b> { "Small-sided games for ball retention" if weakest_pillar == 'Technical' else "Video Analysis & Shadow Play" if weakest_pillar == 'Tactical' else "Interval Sprints & Power Loading" if weakest_pillar == 'Physical' else "High-pressure simulation drills" }.
            <br>2. <b>Expected Outcome:</b> Increase {weakest_pillar} Pillar by 5-10% over the next 4-week microcycle.</div>""", unsafe_allow_html=True)

else:
    st.info("Upload the High-Performance Dataset to begin.")
