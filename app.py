import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #F1F3F5; border-right: 1px solid #DEE2E6; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E9ECEF; border-radius: 8px; }
    .player-card { border: 2px solid #E9ECEF; padding: 20px; border-radius: 15px; background: white; margin-bottom: 20px; }
    .status-critical { color: #dc3545; font-weight: bold; }
    .suggestion-box { background-color: #F0FFF4; border-left: 5px solid #38A169; padding: 15px; border-radius: 5px; }
    .preview-box { background-color: #1B263B; padding: 25px; border-radius: 15px; color: white; text-align: center; }
    .momentum-up { color: #28a745; font-weight: bold; }
    .momentum-down { color: #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    current_year = 2026
    
    # Comprehensive numeric safety check
    numeric_cols = ['pass_accuracy', 'dribble_success', 'interceptions', 'positioning_rating', 
                    'sprint_speed', 'stamina', 'composure', 'big_game_impact', 'market_value', 
                    'age', 'contract_end_year', 'mins_played', 'goals', 'assists',
                    'tpi_m1', 'tpi_m2', 'tpi_m3', 'tpi_m4', 'tpi_m5']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0
    
    # Core Logic
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
    except:
        st.sidebar.warning("Cloud Sync Offline.")
else:
    file = st.sidebar.file_uploader("Upload CSV", type="csv")
    if file: df_raw = pd.read_csv(file)

if df_raw is not None:
    df, team_avg = calculate_analytics(df_raw)
    
    # TABS
    tabs = st.tabs(["👤 Profile", "📊 Comparison", "📋 Squad Health", "🌍 War Room", "🔥 Match Day", "📈 Progress Tracker"])

    # --- TAB 1: PROFILE (HARD-FIXED STATE) ---
    with tabs[0]:
        # Force a unique key and pull current choice directly
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique(), key="active_profile_selector")
        
        # USE LOC for unambiguous data retrieval
        p_d = df.loc[df['player_name'] == p_name].iloc[0]
        
        st.markdown('<div class="player-card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1: 
            if pd.notna(p_d.get('club_logo_url')) and p_d['club_logo_url'] != "":
                st.image(p_d['club_logo_url'], width=100)
        with c2: 
            if pd.notna(p_d.get('photo_url')) and p_d['photo_url'] != "":
                st.image(p_d['photo_url'], width=150)
            else: st.image("https://via.placeholder.com/150?text=Photo", width=150)
        with c3:
            st.header(p_name)
            st.subheader(f"{p_d.get('club')} | {p_d.get('nationality')}")
            st.write(f"**Total Career Minutes:** {int(p_d.get('mins_played', 0)):,} mins")
            if p_d['Years_Left'] <= 0: st.markdown('<p class="status-critical">⚠️ CONTRACT RISK</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Goals", int(p_d.get('goals', 0)))
        m2.metric("TPI Index", f"{p_d['TPI']:.1f}")
        m3.metric("Market Value", f"${int(p_d.get('market_value', 0)):,}")

    # --- TAB 2: COMPARISON ---
    with tabs[1]:
        st.subheader("Performance Comparison")
        col1, col2 = st.columns(2)
        p1 = col1.selectbox("Primary Player", df['player_name'].unique(), key="c1_fix")
        comp_on = col2.checkbox("Enable Comparison Mode", key="cc_fix")
        p1_data = df.loc[df['player_name'] == p1].iloc[0]
        cats = ['Technical', 'Tactical', 'Physical', 'Mental']
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=cats, y=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']], name=p1, marker_color='#212529'))
        if comp_on:
            p2 = st.selectbox("Compare With", df['player_name'].unique(), index=1, key="c2_fix")
            p2_data = df.loc[df['player_name'] == p2].iloc[0]
            fig.add_trace(go.Bar(x=cats, y=[p2_data['Tech_Score'], p2_data['Tact_Score'], p2_data['Phys_Score'], p2_data['Ment_Score']], name=p2, marker_color='#D00000'))
        
        # TEAM AVERAGE OVERLAY
        fig.add_trace(go.Scatter(x=cats, y=[team_avg['Tech'], team_avg['Tact'], team_avg['Phys'], team_avg['Ment']], 
                                 mode='lines+markers', name='Team Average', line=dict(color='#007BFF', width=4, dash='dash'), marker=dict(size=12, symbol='diamond')))
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 3: SQUAD HEALTH ---
    with tabs[2]:
        st.header("📋 Squad Readiness & Talent Map")
        low = df[df['Phys_Score'] < 65]
        for _, p in low.iterrows(): st.error(f"🚨 **Injury Risk:** {p['player_name']} ({p['Phys_Score']:.1f}%)")
        fig_health = px.scatter(df, x="Phys_Score", y="TPI", text="player_name", size="market_value", color="TPI", title="Talent Map: Readiness vs. Performance")
        st.plotly_chart(fig_health, use_container_width=True)

    # --- TAB 4: WAR ROOM ---
    with tabs[3]:
        st.subheader("Decision Support: Opportunity & Replacement")
        fig_war = px.scatter(df, x="contract_end_year", y="TPI", size="market_value", color="Transfer_Prob", text="player_name", title="Performance vs. Contract Expiry")
        st.plotly_chart(fig_war, use_container_width=True)
        st.divider()
        at_risk = df[df['Years_Left'] <= 1].sort_values(by='TPI', ascending=False)
        if not at_risk.empty:
            target = st.selectbox("Replace Expiring Player", at_risk['player_name'].unique(), key="war_select")
            t_data = df.loc[df['player_name'] == target].iloc[0]
            sugs = df[(df['player_name']!=target) & (df['TPI']>=t_data['TPI']-10) & (df['Years_Left']>1)].head(3)
            if not sugs.empty:
                st.markdown(f'<div class="suggestion-box"><b>Replacements for {target}:</b><br>' + 
                            "<br>".join([f"✅ {r['player_name']} - TPI: {r['TPI']:.1f}, Value: ${int(r['market_value']):,}" for _, r in sugs.iterrows()]) + '</div>', unsafe_allow_html=True)

    # --- TAB 5: MATCH DAY ---
    with tabs[4]:
        st.header("🔥 Match Day Command")
        starting_xi = st.multiselect("Pick 11 Players", df['player_name'].unique(), max_selections=11, key="xi_sel")
        if len(starting_xi) > 0:
            xi_df = df[df['player_name'].isin(starting_xi)]
            xi_avg = xi_df[['Tech_Score', 'Tact_Score', 'Phys_Score', 'Ment_Score', 'TPI']].mean()
            opp = st.selectbox("Opponent", df['club'].unique(), key="opp_sel")
            opp_df = df[df['club'] == opp]
            opp_avg = opp_df[['Tech_Score', 'Tact_Score', 'Phys_Score', 'Ment_Score', 'TPI']].mean()
            
            win_p = max(5, min(95, (50 + ((xi_avg['TPI'] - opp_avg['TPI']) * 3))))
            st.markdown(f'<div class="preview-box"><h1>{win_p:.1f}%</h1><p>Win Probability</p></div>', unsafe_allow_html=True)
            
            fig_rad = go.Figure()
            fig_rad.add_trace(go.Scatterpolar(r=[xi_avg['Tech_Score'], xi_avg['Tact_Score'], xi_avg['Phys_Score'], xi_avg['Ment_Score']], theta=['Tech', 'Tact', 'Phys', 'Ment'], fill='toself', name='Our XI'))
            fig_rad.add_trace(go.Scatterpolar(r=[opp_avg['Tech_Score'], opp_avg['Tact_Score'], opp_avg['Phys_Score'], opp_avg['Ment_Score']], theta=['Tech', 'Tact', 'Phys', 'Ment'], fill='toself', name=opp))
            st.plotly_chart(fig_rad, use_container_width=True)

    # --- TAB 6: PROGRESS TRACKER ---
    with tabs[5]:
        st.header("📈 Season Momentum")
        f_name = st.selectbox("Select Player", df['player_name'].unique(), key="form_sel")
        f_d = df.loc[df['player_name'] == f_name].iloc[0]
        
        hist = [f_d['tpi_m5'], f_d['tpi_m4'], f_d['tpi_m3'], f_d['tpi_m2'], f_d['tpi_m1']]
        matches = ["M-5", "M-4", "M-3", "M-2", "Last Match"]
        
        fig_trend = px.line(x=matches, y=hist, markers=True, title=f"Trend: {f_name}")
        st.plotly_chart(fig_trend, use_container_width=True)

else:
    st.info("Upload the CSV to begin.")
