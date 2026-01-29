import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import datetime

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #F1F3F5; border-right: 1px solid #DEE2E6; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E9ECEF; border-radius: 8px; }
    .player-card { border: 2px solid #E9ECEF; padding: 20px; border-radius: 15px; background: white; margin-bottom: 20px; }
    .label-box { background-color: #EBF8FF; border-left: 5px solid #3182CE; padding: 12px; margin-bottom: 15px; border-radius: 4px; }
    .pitch-box { background-color: #1B263B; padding: 25px; border-radius: 15px; color: white; text-align: center; }
    .input-card { background-color: #FDF2F2; border: 1px solid #FEB2B2; padding: 20px; border-radius: 10px; }
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

    # Pillar Scores
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

if 'df' not in st.session_state:
    if source == "Cloud Database":
        try: st.session_state.df = pd.read_csv(DEFAULT_URL)
        except: st.sidebar.warning("Cloud Offline. Using dummy data.")
    else:
        file = st.sidebar.file_uploader("Upload CSV", type="csv")
        if file: st.session_state.df = pd.read_csv(file)

if 'df' in st.session_state:
    df, team_avg = calculate_analytics(st.session_state.df)
    
    tabs = st.tabs(["👤 Profile", "📊 Comparison", "📋 Health", "🔥 Match Day", "📈 Progress", "🛰️ Regional", "💎 Pitch Mode", "📥 Data Entry"])

    # (Previous Tabs maintained for consistency)
    with tabs[0]: # Profile
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique(), key="prof_s")
        p_d = df.loc[df['player_name'] == p_name].iloc[0]
        st.markdown(f'<div class="player-card"><h2>{p_name}</h2><b>{p_d["club"]}</b></div>', unsafe_allow_html=True)

    with tabs[1]: # Comparison
        st.markdown('<div class="label-box">💡 Compare players against the <b>League Average Line</b>.</div>', unsafe_allow_html=True)
        p1 = st.selectbox("Player", df['player_name'].unique(), key="c1")
        p1_d = df.loc[df['player_name'] == p1].iloc[0]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[p1_d['Tech_Score'], p1_d['Tact_Score'], p1_d['Phys_Score'], p1_d['Ment_Score']], name=p1))
        fig.add_trace(go.Scatter(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[team_avg['Tech'], team_avg['Tact'], team_avg['Phys'], team_avg['Ment']], mode='lines+markers', name='Avg', line=dict(dash='dash')))
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 6: PITCH MODE ---
    with tabs[6]:
        st.header("💎 Executive Pitch: The Cost of Inaction")
        pitch_club = st.selectbox("Select Club to Audit", df[df['league']=='Rwanda Premier']['club'].unique(), key="pitch_c")
        c_data = df[df['club'] == pitch_club]
        
        # Financial Gap Calculation
        avg_val_per_tpi = df['market_value'].sum() / df['TPI'].sum()
        c_data['Leaked_Value'] = (c_data['market_value'] - (c_data['TPI'] * avg_val_per_tpi)).clip(lower=0)
        total_leak = c_data['Leaked_Value'].sum()
        
        st.markdown(f'<div class="pitch-box"><h1>${int(total_leak):,}</h1><p>Annual Leaked Value in Recruitment Inefficiency</p></div>', unsafe_allow_html=True)
        fig_pitch = px.scatter(c_data, x="TPI", y="market_value", text="player_name", size="market_value", color="Leaked_Value", title="Value vs. Performance Audit")
        st.plotly_chart(fig_pitch, use_container_width=True)

    # --- TAB 7: DATA INPUT HELPER ---
    with tabs[7]:
        st.header("📥 Manual Match Data Entry")
        st.markdown('<div class="label-box">Use this form to update your database after scouting a match.</div>', unsafe_allow_html=True)
        
        with st.form("match_entry"):
            col_in1, col_in2 = st.columns(2)
            player_to_update = col_in1.selectbox("Select Player", df['player_name'].unique())
            new_tpi = col_in2.number_input("Last Match TPI Performance (0-100)", 0.0, 100.0, 75.0)
            
            new_goals = col_in1.number_input("Goals Scored", 0, 5, 0)
            new_assists = col_in2.number_input("Assists", 0, 5, 0)
            
            submit = st.form_submit_button("Append Match Data to Session")
            
            if submit:
                # Update logic for "Consistency": Shift old TPIs to the right
                idx = df[df['player_name'] == player_to_update].index[0]
                st.session_state.df.at[idx, 'tpi_m5'] = st.session_state.df.at[idx, 'tpi_m4']
                st.session_state.df.at[idx, 'tpi_m4'] = st.session_state.df.at[idx, 'tpi_m3']
                st.session_state.df.at[idx, 'tpi_m3'] = st.session_state.df.at[idx, 'tpi_m2']
                st.session_state.df.at[idx, 'tpi_m2'] = st.session_state.df.at[idx, 'tpi_m1']
                st.session_state.df.at[idx, 'tpi_m1'] = new_tpi
                
                # Accumulate season totals
                st.session_state.df.at[idx, 'goals'] += new_goals
                st.session_state.df.at[idx, 'assists'] += new_assists
                
                st.success(f"Successfully updated {player_to_update}. Download CSV in sidebar to save permanently.")

    # Sidebar Export Feature
    st.sidebar.divider()
    csv_data = st.session_state.df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("💾 Download Master CSV", data=csv_data, file_name="rpl_master_updated.csv", mime='text/csv')

else:
    st.info("Please upload your Master CSV to initialize the platform.")
