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
    .preview-box { background-color: #1B263B; padding: 25px; border-radius: 15px; color: white; text-align: center; }
    .quota-box { background-color: #FFF5F5; border: 1px solid #FEB2B2; padding: 10px; border-radius: 5px; color: #C53030; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    current_year = 2026
    
    # Critical Columns for Integrity
    numeric_cols = ['pass_accuracy', 'dribble_success', 'interceptions', 'positioning_rating', 
                    'sprint_speed', 'stamina', 'composure', 'big_game_impact', 'market_value', 
                    'age', 'contract_end_year', 'mins_played', 'goals', 'assists',
                    'tpi_m1', 'tpi_m2', 'tpi_m3', 'tpi_m4', 'tpi_m5']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0
            
    # Category Safety
    if 'league' not in df.columns: df['league'] = 'Rwanda Premier'
    if 'nationality' not in df.columns: df['nationality'] = 'Rwanda'
    if 'club' not in df.columns: df['club'] = 'Unknown Club'

    # Core Analytics Logic
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

    # --- TAB 1: PROFILE (FIXED) ---
    with tabs[0]:
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique(), key="prof_selector")
        p_d = df.loc[df['player_name'] == p_name].iloc[0]
        st.markdown(f'<div class="player-card"><h2>{p_name}</h2><b>{p_d["club"]} | {p_d["league"]}</b></div>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("TPI", f"{p_d['TPI']:.1f}")
        m2.metric("Market Value", f"${int(p_d['market_value']):,}")
        m3.metric("Nationality", p_d['nationality'])

    # --- TAB 2: COMPARISON (BENCHMARK FIXED) ---
    with tabs[1]:
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
        fig.add_trace(go.Scatter(x=cats, y=[team_avg['Tech'], team_avg['Tact'], team_avg['Phys'], team_avg['Ment']], mode='lines+markers', name='League Avg', line=dict(color='#007BFF', dash='dash')))
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 3: HEALTH ---
    with tabs[2]:
        low = df[df['Phys_Score'] < 65]
        for _, p in low.iterrows(): st.error(f"🚨 Risk: {p['player_name']} ({p['Phys_Score']:.1f}%)")
        fig_health = px.scatter(df, x="Phys_Score", y="TPI", text="player_name", color="TPI", title="Talent Map")
        st.plotly_chart(fig_health, use_container_width=True)

    # --- TAB 4: WAR ROOM ---
    with tabs[3]:
        fig_war = px.scatter(df, x="contract_end_year", y="TPI", size="market_value", color="Transfer_Prob", text="player_name")
        st.plotly_chart(fig_war, use_container_width=True)

    # --- TAB 5: MATCH DAY ---
    with tabs[4]:
        starting_xi = st.multiselect("Select Starting XI", df['player_name'].unique(), max_selections=11)
        if len(starting_xi) > 0:
            xi_avg = df[df['player_name'].isin(starting_xi)][['Tech_Score', 'Tact_Score', 'Phys_Score', 'Ment_Score', 'TPI']].mean()
            opp = st.selectbox("Opponent", df['club'].unique(), key="match_opp")
            opp_df = df[df['club'] == opp]
            if not opp_df.empty:
                opp_avg = opp_df[['Tech_Score', 'Tact_Score', 'Phys_Score', 'Ment_Score', 'TPI']].mean()
                win_p = max(5, min(95, (50 + ((xi_avg['TPI'] - opp_avg['TPI']) * 3))))
                st.markdown(f'<div class="preview-box"><h1>{win_p:.1f}%</h1><p>Win Probability</p></div>', unsafe_allow_html=True)

    # --- TAB 6: PROGRESS ---
    with tabs[5]:
        f_name = st.selectbox("Track Form", df['player_name'].unique(), key="form_tr")
        f_d = df.loc[df['player_name'] == f_name].iloc[0]
        hist = [f_d['tpi_m5'], f_d['tpi_m4'], f_d['tpi_m3'], f_d['tpi_m2'], f_d['tpi_m1']]
        fig_f = px.line(x=["M-5", "M-4", "M-3", "M-2", "Last"], y=hist, markers=True, title=f"Trend: {f_name}")
        st.plotly_chart(fig_f, use_container_width=True)

    # --- TAB 7: REGIONAL ---
    with tabs[6]:
        st.header("🛰️ Regional Scouting & Foreign Quota")
        my_club = st.selectbox("My Club", df[df['league'] == 'Rwanda Premier']['club'].unique())
        squad = df[df['club'] == my_club]
        foreign_count = len(squad[squad['nationality'] != 'Rwanda'])
        st.metric("Foreign Quota", f"{foreign_count} / 6")
        
        target = st.selectbox("Regional Target", df[df['league'] != 'Rwanda Premier']['player_name'].unique())
        if target:
            t_d = df.loc[df['player_name'] == target].iloc[0]
            st.write(f"### Target Benchmark: {target}")
            fig_sc = go.Figure()
            fig_sc.add_trace(go.Scatterpolar(r=[t_d['Tech_Score'], t_d['Tact_Score'], t_d['Phys_Score'], t_d['Ment_Score']], theta=['Tech', 'Tact', 'Phys', 'Ment'], fill='toself', name=target))
            st.plotly_chart(fig_sc, use_container_width=True)

else:
    st.info("Upload CSV to activate.")
