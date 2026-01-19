import pandas as pd

def calculate_player_performance(data):
    # 1. Define Pillar Weights
    weights = {'technical': 0.35, 'tactical': 0.25, 'physical': 0.25, 'mental': 0.15}
    
    # 2. Normalize raw stats to a 0-100 scale (Example for a Striker)
    # In a real scenario, 'max_val' would be the league record/benchmark
    data['tech_score'] = ((data['goals_per_90'] / 1.0) * 60 + (data['shot_conv_rate'] / 30) * 40)
    data['tact_score'] = (data['pressing_efficiency'] + data['positioning_rating']) / 2
    data['phys_score'] = ((data['sprint_speed'] / 35) * 100)
    data['ment_score'] = (data['composure'] + data['big_game_impact']) / 2

    # 3. Calculate Final TPI
    data['TPI'] = (
        (data['tech_score'] * weights['technical']) +
        (data['tact_score'] * weights['tactical']) +
        (data['phys_score'] * weights['physical']) +
        (data['ment_score'] * weights['mental'])
    )
    
    return data

# Sample Usage
raw_stats = pd.DataFrame({
    'player': ['Striker A'],
    'goals_per_90': [0.65],
    'shot_conv_rate': [22],
    'pressing_efficiency': [75],
    'positioning_rating': [80],
    'sprint_speed': [32.5],
    'composure': [85],
    'big_game_impact': [70]
})

final_report = calculate_player_performance(raw_stats)
print(final_report[['player', 'TPI']])
