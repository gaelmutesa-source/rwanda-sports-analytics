import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide", page_icon="🛰️")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #F1F3F5; border-right: 1px solid #DEE2E6; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E9ECEF; border-radius: 8px; }
    .player-card { border: 2px solid #E9ECEF; padding: 20px; border-radius: 15px; background: white; margin-bottom: 20px; }
    .quota-box { background-color: #FFF5F5; border: 1px solid #FEB2B2; padding: 10px; border-radius: 5px; color: #C53030; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    
    # Required Columns for Consistency
    cols = ['pass_accuracy', 'dribble_success', 'interceptions', 'positioning_rating', 
            'sprint_speed', 'stamina', 'composure', 'big_game_impact', 'market_value', 
            'age', 'contract_end_year', 'tpi_m1', 'tpi_m2', 'tpi_m3', 'tpi_m4', 'tpi_m5']
    
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0
            
    if 'league' not in df.columns: df['league'] = 'Rwanda Premier'
    if 'nationality' not in df.columns: df['nationality'] = 'Unknown'

    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*weights['Technical'] + df['Tact_Score']*weights['Tactical'] + 
                 df['Phys_Score']*weights['Physical'] + df['Ment_Score']*weights['Mental'])
    
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
    except:
        st.sidebar.warning("Cloud Sync Offline.")
else:
    file = st.sidebar.file_uploader("Upload Master CSV", type="csv")
    if file: df_raw = pd.read_csv(file)

if df_raw is not None:
    df, team_avg = calculate_analytics(df_raw)
    
    tabs = st.tabs(["👤 Profile", "📊 Comparison", "📋 Health", "🌍 War Room", "📈 Progress", "🛰️ Regional Scouting"])

    # --- TABS 0-4 MAINTAINED FOR STABILITY ---
    with tabs[0]:
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique(), key="prof_fixed_v3")
        p_d = df.loc[df['player_name'] == p_name].iloc[0]
        st.markdown(f'<div class="player-card"><h2>{p_name}</h2><b>{p_d.get("club")} | {p_d.get("league")}</b></div>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("TPI Index", f"{p_d['TPI']:.1f}")
        m2.metric("Market Value", f"${int(p_d.get('market_value', 0)):,}")
        m3.metric("Nationality", p_d.get('nationality'))

    # --- TAB 5: REGIONAL SCOUTING REPORT (NEW) ---
    with tabs[5]:
        st.header("🛰️ Regional Scouting & Foreign Quota Tracker")
        
        # 1. Foreign Quota Logic (FERWAFA Rules: Max 6 foreign players in matchday squad)
        st.subheader("🛡️ Squad Regulation Check")
        my_club = st.selectbox("Select Your Club to Check Quota", df[df['league'] == 'Rwanda Premier']['club'].unique())
        squad = df[df['club'] == my_club]
        foreigners = squad[squad['nationality'] != 'Rwanda']
        quota_count = len(foreigners)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("Foreign Players", f"{quota_count} / 6")
            if quota_count >= 6:
                st.markdown('<div class="quota-box">⚠️ QUOTA FULL: You must sell a foreign player before signing a regional target.</div>', unsafe_allow_html=True)
            else:
                st.success(f"Slots Available: {6 - quota_count}")

        # 2. Regional Target Comparison
        st.divider()
        st.subheader("🔍 External Target Benchmark")
        target_name = st.selectbox("Select Regional Target (KE/TZ/UG)", df[df['league'] != 'Rwanda Premier']['player_name'].unique())
        t_d = df.loc[df['player_name'] == target_name].iloc[0]
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"### Target: {target_name}")
            st.write(f"**Club:** {t_d['club']} ({t_d['league']})")
            st.write(f"**TPI:** {t_d['TPI']:.1f}")
            st.progress(t_d['TPI']/100)
        
        with col_b:
            # Benchmark target against your team's average
            fig_scout = go.Figure()
            fig_scout.add_trace(go.Scatterpolar(
                r=[t_d['Tech_Score'], t_d['Tact_Score'], t_d['Phys_Score'], t_d['Ment_Score']],
                theta=['Tech', 'Tact', 'Phys', 'Ment'], fill='toself', name=target_name, line_color='#E53E3E'
            ))
            fig_scout.add_trace(go.Scatterpolar(
                r=[team_avg['Tech'], team_avg['Tact'], team_avg['Phys'], team_avg['Ment']],
                theta=['Tech', 'Tact', 'Phys', 'Ment'], fill='toself', name=f"{my_club} Avg", line_color='#3182CE'
            ))
            st.plotly_chart(fig_scout, use_container_width=True)
            
        st.info(f"💡 **Verdict:** {target_name} is performing at {((t_d['TPI']/team_avg['TPI'])-1)*100:+.1f}% relative to your current squad average.")

else:
    st.info("Upload the Master CSV to activate Regional Scouting.")
