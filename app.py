import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide", page_icon="🛰️")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #F1F3F5; border-right: 1px solid #DEE2E6; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E9ECEF; border-radius: 8px; }
    .player-card { border: 2px solid #E9ECEF; padding: 20px; border-radius: 15px; background: white; margin-bottom: 20px; }
    .label-box { background-color: #EBF8FF; border-left: 5px solid #3182CE; padding: 12px; margin-bottom: 15px; border-radius: 4px; font-size: 0.9rem; }
    .preview-box { background-color: #1B263B; padding: 25px; border-radius: 15px; color: white; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    current_year = 2026
    
    numeric_cols = ['pass_accuracy', 'dribble_success', 'interceptions', 'positioning_rating', 
                    'sprint_speed', 'stamina', 'composure', 'big_game_impact', 'market_value', 
                    'age', 'contract_end_year', 'mins_played', 'goals', 'assists',
                    'tpi_m1', 'tpi_m2', 'tpi_m3', 'tpi_m4', 'tpi_m5']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0
            
    if 'league' not in df.columns: df['league'] = 'Rwanda Premier'
    if 'nationality' not in df.columns: df['nationality'] = 'Rwanda'
    if 'club' not in df.columns: df['club'] = 'Unknown Club'

    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*weights['Technical'] + df['Tact_Score']*weights['Tactical'] + 
                 df['Phys_Score']*weights['Physical'] + df['Ment_Score']*weights['Mental'])
    
    df['Transfer_Prob'] = (((df['TPI'] * 0.6) + (35 - df['age']) * 2) / 100).clip(0, 0.95)
    df['Years_Left'] = df['contract_end_year'] - current_year
    
    team_avg = {'Tech': df['Tech_Score'].mean(), 'Tact': df['Tact_Score'].mean(), 
                'Phys': df['Phys_Score'].mean(), 'Ment': df['Ment_Score'].mean(), 'TPI': df['TPI'].mean()}
    return df, team_avg

# --- 2. DATA SOURCE ---
st.sidebar.title("💎 RPL ELITE")
DEFAULT_URL = "https://raw.githubusercontent.com/Marclon11/Data/main/rpl_master_data.csv"
source = st.sidebar.radio("Data Source", ["Cloud Database", "Local Upload"])

df_raw = None
if source == "Cloud Database":
    try:
        df_raw = pd.read_csv(DEFAULT_URL)
        st.sidebar.success("✅ Cloud Sync Active")
    except Exception as e:
        st.sidebar.warning(f"Cloud Offline. Error: {e}")
else:
    file = st.sidebar.file_uploader("Upload CSV", type="csv")
    if file: df_raw = pd.read_csv(file)

if df_raw is not None:
    df, team_avg = calculate_analytics(df_raw)
    
    tabs = st.tabs(["👤 Profile", "📊 Comparison", "📋 Health", "🌍 War Room", "🔥 Match Day", "📈 Progress", "🛰️ Regional"])

    with tabs[0]:
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique(), key="prof_selector")
        p_d = df.loc[df['player_name'] == p_name].iloc[0]
        st.markdown(f'<div class="player-card"><h2>{p_name}</h2><b>{p_d["club"]} | {p_d["league"]}</b></div>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("TPI Index", f"{p_d['TPI']:.1f}")
        m2.metric("Market Value", f"${int(p_d['market_value']):,}")
        m3.metric("Nationality", p_d['nationality'])

    with tabs[1]:
        st.markdown('<div class="label-box">💡 <b>How to read this chart:</b> Compare the bars against the <b>Dashed Blue Line</b>. If a bar is above the line, the player is performing <b>above league average</b> in that specific pillar.</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        p1 = col1.selectbox("Primary Player", df['player_name'].unique(), key="c1_unique")
        compare_on = col2.checkbox("Enable Comparison", key="comp_toggle")
        p1_data = df.loc[df['player_name'] == p1].iloc[0]
        cats = ['Technical', 'Tactical', 'Physical', 'Mental']
        fig = go.Figure()
        fig.add_trace(go.Bar(x=cats, y=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']], name=p1, marker_color='#212529'))
        if compare_on:
            p2 = st.selectbox("Compare With", df['player_name'].unique(), index=1, key="c2_unique")
            p2_data = df.loc[df['player_name'] == p2].iloc[0]
            fig.add_trace(go.Bar(x=cats, y=[p2_data['Tech_Score'], p2_data['Tact_Score'], p2_data['Phys_Score'], p2_data['Ment_Score']], name=p2, marker_color='#D00000'))
        fig.add_trace(go.Scatter(x=cats, y=[team_avg['Tech'], team_avg['Tact'], team_avg['Phys'], team_avg['Ment']], mode='lines+markers', name='League Avg', line=dict(color='#007BFF', dash='dash'), marker=dict(size=10, symbol='diamond')))
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        st.markdown('<div class="label-box">💡 <b>Talent Map Insight:</b> Players in the <b>Top Right</b> are your high-performers with high fitness. Players in the <b>Top Left</b> are elite talents at high risk of injury (overloaded).</div>', unsafe_allow_html=True)
        low = df[df['Phys_Score'] < 65]
        for _, p in low.iterrows(): st.error(f"🚨 Risk: {p['player_name']} ({p['Phys_Score']:.1f}%)")
        fig_health = px.scatter(df, x="Phys_Score", y="TPI", text="player_name", color="TPI", title="Talent Map: Readiness vs. Performance")
        st.plotly_chart(fig_health, use_container_width=True)

    with tabs[3]:
        st.markdown('<div class="label-box">💡 <b>Opportunity Map:</b> Bubble size represents <b>Market Value</b>. Focus on large bubbles near <b>2026/2027</b>; these are your high-value assets with expiring contracts.</div>', unsafe_allow_html=True)
        fig_war = px.scatter(df, x="contract_end_year", y="TPI", size="market_value", color="Transfer_Prob", text="player_name")
        st.plotly_chart(fig_war, use_container_width=True)

    with tabs[5]:
        st.markdown('<div class="label-box">💡 <b>Momentum Guide:</b> An <b>upward slope</b> indicates a player in peak form. A <b>downward slope</b> over 3 matches suggests it is time to rotate or investigate burnout.</div>', unsafe_allow_html=True)
        f_name = st.selectbox("Track Form", df['player_name'].unique(), key="form_tr")
        f_d = df.loc[df['player_name'] == f_name].iloc[0]
        hist = [f_d['tpi_m5'], f_d['tpi_m4'], f_d['tpi_m3'], f_d['tpi_m2'], f_d['tpi_m1']]
        fig_f = px.line(x=["M-5", "M-4", "M-3", "M-2", "Last"], y=hist, markers=True, title=f"Trend: {f_name}")
        st.plotly_chart(fig_f, use_container_width=True)

    with tabs[6]:
        st.markdown('<div class="label-box">💡 <b>Scouting Radar:</b> The <b>Red Area</b> represents the regional target. The <b>Blue Area</b> is your current squad average. Sign players whose red area significantly expands past the blue.</div>', unsafe_allow_html=True)
        target = st.selectbox("Regional Target", df[df['league'] != 'Rwanda Premier']['player_name'].unique(), key="target_scout")
        if target:
            t_d = df.loc[df['player_name'] == target].iloc[0]
            fig_sc = go.Figure()
            fig_sc.add_trace(go.Scatterpolar(r=[t_d['Tech_Score'], t_d['Tact_Score'], t_d['Phys_Score'], t_d['Ment_Score']], theta=['Tech', 'Tact', 'Phys', 'Ment'], fill='toself', name=target, line_color='#E53E3E'))
            fig_sc.add_trace(go.Scatterpolar(r=[team_avg['Tech'], team_avg['Tact'], team_avg['Phys'], team_avg['Ment']], theta=['Tech', 'Tact', 'Phys', 'Ment'], fill='toself', name="Squad Avg", line_color='#3182CE'))
            st.plotly_chart(fig_sc, use_container_width=True)

else:
    st.info("Upload CSV to activate labels and analytics.")
