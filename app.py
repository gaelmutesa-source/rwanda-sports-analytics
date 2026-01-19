import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(page_title="Rwanda Sports Analytics", layout="wide")

st.title("⚽ Rwanda Football Performance Index")
st.sidebar.header("Control Panel")

# 1. File Uploader
uploaded_file = st.sidebar.file_uploader("Upload Match Data (CSV or Excel)", type=["csv", "xlsx"])

def calculate_tpi(df):
    # Weights for the 4 Pillars
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    
    # Simple scoring logic (assuming columns exist in your data)
    # This is where your "Secret Sauce" formulas live
    df['Tech_Score'] = df.get('pass_accuracy', 50) * 0.6 + df.get('dribble_success', 50) * 0.4
    df['Tact_Score'] = df.get('interceptions', 5) * 10
    df['Phys_Score'] = df.get('sprint_speed', 25) * 3
    df['Ment_Score'] = df.get('composure', 70)
    
    df['TPI'] = (df['Tech_Score'] * weights['Technical'] + 
                 df['Tact_Score'] * weights['Tactical'] + 
                 df['Phys_Score'] * weights['Physical'] + 
                 df['Ment_Score'] * weights['Mental'])
    return df

if uploaded_file:
    # Load Data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    df = calculate_tpi(df)

    # 2. Player Selection
    player_list = df['player_name'].unique()
    selected_player = st.selectbox("Select Player to Analyze", player_list)
    
    player_data = df[df['player_name'] == selected_player].iloc[0]

    # 3. Radar Chart (The Professional "Scouting" View)
    categories = ['Technical', 'Tactical', 'Physical', 'Mental']
    values = [player_data['Tech_Score'], player_data['Tact_Score'], 
              player_data['Phys_Score'], player_data['Ment_Score']]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name=selected_player))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Total Performance Index (TPI)", f"{player_data['TPI']:.1f}")
        st.write(f"**Position:** {player_data.get('position', 'N/A')}")
    with col2:
        st.plotly_chart(fig)

else:
    st.info("Waiting for data upload. Please upload a CSV file with columns: player_name, pass_accuracy, dribble_success, etc.")
