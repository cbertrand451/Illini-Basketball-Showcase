import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import plotly.express as px
import plotly.graph_objects as go
from utils import player_scrape_header_info
import re
from geopy.geocoders import Nominatim
import time
import pydeck as pdk
from colors import ILLINOIS_COLORS, ILLINOIS_BLUE, ILLINOIS_GRAY, ILLINOIS_ORANGE



st.set_page_config(page_title="Team Overviews", layout="wide")
st.title("Team Overviews")
st.subheader(":orange[Featuring Detailed Team Information]")
"---"

seasons = []
for i in range(2024,1978, -1):
    next_year_short = str((i + 1) % 100).zfill(2)
    season_str = f"{i}-{next_year_short}"
    seasons.append(season_str)

season_stats = pd.read_csv('data/processed/season_stats.csv')

#fix Altair encoding issues
column_mapping = {
    'FG: Made-Attempted': 'FG Made-Attempted',
    'FG: Percentage': 'FG Percentage', 
    'FG: Per Game': 'FG Per Game',
    '3PT: Made-Attempted': '3PT Made-Attempted',
    '3PT: Percentage': '3PT Percentage',
    '3PT: Per Game': '3PT Per Game', 
    'FT: Made-Attempted': 'FT Made-Attempted',
    'FT: Percentage': 'FT Percentage',
    'FT: Per Game': 'FT Per Game'
}

#rename columns
season_stats = season_stats.rename(columns=column_mapping)

# Update stats options with cleaned names
stats_options = ['Total Points', 'Points Per Game', 'Scoring Margin', 'FG Made-Attempted', 
                 'FG Percentage', 'FG Per Game', '3PT Made-Attempted', '3PT Percentage', 
                 '3PT Per Game', 'FT Made-Attempted', 'FT Percentage', 'FT Per Game', 
                 'Total Rebounds', 'Rebounds Per Game', 'Rebound Margin', 'Total Assists', 
                 'Assists Per Game', 'Total Turnovers', 'Turnovers Per Game', 'Turnovers Margin', 
                 'Assist/Turnover Ratio', 'Points Off Turnovers', 'Total Steals', 'Steals Per Game', 
                 'Total Blocks', 'Blocks Per Game', 'Total Attendance', 'Attendance Per Game']

st.header('Hi')
bar, options = st.columns(2)

with bar:
    stat_bar = st.selectbox('Select a Statistic', stats_options)
with options:
    teams_options = st.pills('Choose teams to display', ['Illinois', 'Opponents'], default='Illinois', selection_mode='multi')

df_illinois = season_stats[season_stats['Team'] == 'Illinois']
df_opponents = season_stats[season_stats['Team'] == 'Opponents']

# Check if both teams are selected
if len(teams_options) == 2:
    if 'Season' in season_stats.columns:
        # Sort both datasets by season
        df_illinois = df_illinois.sort_values(by='Season', ascending=True)
        df_opponents = df_opponents.sort_values(by='Season', ascending=True)
        
        st.subheader(f"{stat_bar} Over Time")
        

        
        # Properly merge the data by season
        chart_data = pd.merge(
            df_illinois[['Season', stat_bar]], 
            df_opponents[['Season', stat_bar]], 
            on='Season', 
            suffixes=('_Illinois', '_Opponents')
        )
        
        # Rename columns for the chart
        chart_data = chart_data.rename(columns={
            f'{stat_bar}_Illinois': 'Illinois',
            f'{stat_bar}_Opponents': 'Opponents'
        }).set_index('Season')
        
        st.line_chart(chart_data, color=[ILLINOIS_ORANGE, ILLINOIS_BLUE])
    else:
        st.error("No common seasons found between Illinois and Opponents data.")
    
# Check if only Illinois is selected
elif 'Illinois' in teams_options and 'Opponents' not in teams_options:
    if 'Season' in df_illinois.columns:
        df_illinois = df_illinois.sort_values(by='Season', ascending=True)
        st.subheader(f"{stat_bar} Over Time")
        st.line_chart(df_illinois.set_index('Season')[stat_bar], color=ILLINOIS_ORANGE)
    else:
        st.error("No 'Season' column found in the dataset.")
# Check if only Opponents is selected
elif 'Opponents' in teams_options and 'Illinois' not in teams_options:
    if 'Season' in df_opponents.columns:
        df_opponents = df_opponents.sort_values(by='Season', ascending=True)
        st.subheader(f"{stat_bar} Over Time")
        st.line_chart(df_opponents.set_index('Season')[stat_bar], color=ILLINOIS_BLUE)
    else:
        st.error("No 'Season' column found in the dataset.")
# Handle case when no teams are selected
elif len(teams_options) == 0:
    st.warning("Please select at least one team to display.")


year_bar = st.selectbox('Select a Year for Details', seasons)
df_selected_ill = df_illinois[df_illinois['Season'] == year_bar]
if not df_selected_ill.empty:
    st.subheader(f"Season Details for {year_bar}")
    
    #show stats as rows instead of columns
    df_display = df_selected_ill.T
    df_display.columns = ['Value']
    df_display = df_display.reset_index()
    df_display.columns = ['Statistic', 'Value']
    
    #remove the index column 
    df_display = df_display[df_display['Statistic'] != 'Unnamed: 0']
    
    #use custom column widths
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Statistic": st.column_config.TextColumn(
                "Statistic",
                width="medium",
                help="Team statistic name"
            ),
            "Value": st.column_config.TextColumn(
                "Value", 
                width="small",
                help="Statistic value"
            )
        }
    )
else:
    st.error("No data available for that season.")

"---"

#Roster Analysis Section for Selected Year
st.header("Roster Analysis")
st.markdown(f"Detailed roster analysis for the **{year_bar}** season.")


#load player data
@st.cache_data
def load_player_data():
    with open('data/processed/player_list.json', 'r') as f:
        return json.load(f)

player_data = load_player_data()

#get players for the selected year
@st.cache_data
def get_season_players(selected_season):
    season_players = []
    for player_name, player_info in player_data.items():
        if selected_season in player_info[1]:  
            season_players.append({
                'name': player_name,
                'url': player_info[0],
                'seasons': player_info[1]
            })
    return season_players

season_players = get_season_players(year_bar)

if season_players:
    # Get jersey numbers for players
    roster_data = []
    for player in season_players:
        try:
            player_details = player_scrape_header_info(player['url'])
            jersey_number = player_details.get('Jersey Number', 'N/A')
            roster_data.append({
                '#': jersey_number,
                'name': player['name']
            })
        except:
            roster_data.append({
                '#': 'N/A',
                'name': player['name']
            })
    
    roster_df = pd.DataFrame(roster_data)
    roster_df = roster_df.sort_values('#', key=lambda x: pd.to_numeric(x, errors='coerce').fillna(999))
    roster_df = roster_df.set_index('#')
    roster_df.columns = ['Player']
    st.dataframe(roster_df, use_container_width=True)

    st.subheader(f"{year_bar} Roster ({len(season_players)} Players)")
    
    # Roster Size
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Roster Size", len(season_players))
    

    # Class Distribution Analysis
    #st.subheader("Class Year Distribution")
    
    @st.cache_data
    def get_class_data_for_season(selected_season):
        class_data = []
        for player in season_players:
            try:
                player_details = player_scrape_header_info(player['url'])
                if 'Class' in player_details:
                    class_data.append({
                        'name': player['name'],
                        'class': player_details['Class']
                    })
            except:
                continue
        return class_data
    
    class_data = get_class_data_for_season(year_bar)
    
    if class_data:
        class_df = pd.DataFrame(class_data)
        class_counts = class_df['class'].value_counts().reset_index()
        class_counts.columns = ['Class', 'Count']
        
        # Create two equal columns for class analysis
        cola, colb = st.columns(2)
        
        with cola:
            # Create class distribution chart with custom colors
            fig = px.pie(class_counts, values='Count', names='Class',
                         title=f'Class Distribution - {year_bar} Season',
                         color_discrete_sequence=ILLINOIS_COLORS)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                title_font_size=20,
                title_font_color=ILLINOIS_BLUE,
                font=dict(color=ILLINOIS_BLUE)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with colb:
            # Show class breakdown table
            st.markdown("**Class Breakdown:**")
            st.dataframe(class_counts, use_container_width=True, hide_index=True)
        
        # Calculate class statistics
        with col2:
            st.metric("Most Common Class", class_counts.iloc[0]['Class'] if not class_counts.empty else "N/A")
        with col3:
            st.metric("Class Diversity", len(class_counts))
        
    else:
        st.warning("Class data not available for this season.")
    
    # Geographic Distribution
    st.subheader(f"{year_bar} Geographic Distribution")
    
    @st.cache_data
    def get_geographic_data_for_season(selected_season):
        geo_data = []
        for player in season_players:
            try:
                player_details = player_scrape_header_info(player['url'])
                if 'Hometown' in player_details:
                    hometown = player_details['Hometown']
                    is_illinois = 'Ill.' in hometown or 'Illinois' in hometown
                    geo_data.append({
                        'name': player['name'],
                        'hometown': hometown,
                        'is_illinois': is_illinois
                    })
            except:
                continue
        return geo_data
    
    geo_data = get_geographic_data_for_season(year_bar)
    
    if geo_data:
        geo_df = pd.DataFrame(geo_data)
        
        # Geocode hometowns to get lat/lon
        geolocator = Nominatim(user_agent="illini-basketball-app")
        def get_lat_lon(hometown):
            try:
                location = geolocator.geocode(hometown)
                time.sleep(1)  # To avoid hitting the rate limit
                if location:
                    return location.latitude, location.longitude
            except:
                return None, None
            return None, None

        geo_df[['lat', 'lon']] = geo_df['hometown'].apply(
            lambda x: pd.Series(get_lat_lon(x))
        )

        # Drop rows where geocoding failed
        geo_df = geo_df.dropna(subset=['lat', 'lon'])

        if not geo_df.empty:
            st.markdown("**Player Hometowns Map:**")
            #color code if in state or not (same as illinois orange and blue)
            geo_df['color'] = geo_df['is_illinois'].map(lambda x: [255, 95, 5, 160] if x else [19, 41, 75, 160])
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=geo_df,
                get_position='[lon, lat]',
                get_color='color',
                get_radius=5,
                pickable=True,
                radius_units='meters',
                tooltip=True
            )
            #center the map on the mean location
            view_state = pdk.ViewState(
                latitude=geo_df['lat'].mean(),
                longitude=geo_df['lon'].mean(),
                zoom=1,
                pitch=0
            )
            st.pydeck_chart(pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                map_style="mapbox://styles/mapbox/light-v9",
                tooltip={
                    "html": "<b>{name}</b><br/>{hometown}",
                    "style": {"color": "white"}
                }
            ))
        else:
            st.warning("Could not geocode any hometowns for this season.")
    else:
        st.warning("Geographic data not available for this season.")
    
    # Height and Weight Analysis
    st.subheader(f"{year_bar} Height and Weight Analysis")
    
    @st.cache_data
    def get_physical_data_for_season(selected_season):
        physical_data = []
        for player in season_players:
            try:
                player_details = player_scrape_header_info(player['url'])
                if 'Height' in player_details and 'Weight' in player_details:
                    height_str = player_details['Height']
                    weight_str = player_details['Weight']
                    
                    # Convert height to inches
                    if '-' in height_str:
                        feet, inches = height_str.split('-')
                        height_inches = int(feet) * 12 + int(inches)
                    else:
                        height_inches = None
                    
                    # Convert weight to integer
                    try:
                        weight_lbs = int(weight_str)
                    except:
                        weight_lbs = None
                    
                    if height_inches and weight_lbs:
                        physical_data.append({
                            'name': player['name'],
                            'height_inches': height_inches,
                            'height_feet': height_inches // 12,
                            'height_inches_remainder': height_inches % 12,
                            'weight_lbs': weight_lbs,
                            'height_display': height_str
                        })
            except:
                continue
        return physical_data
    
    physical_data = get_physical_data_for_season(year_bar)
    
    if physical_data:
        physical_df = pd.DataFrame(physical_data)
        
        # Check if we have valid data with height_inches column
        if not physical_df.empty and 'height_inches' in physical_df.columns:
            # Calculate averages
            avg_height = physical_df['height_inches'].mean()
            avg_weight = physical_df['weight_lbs'].mean()
            
            # Display physical statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Avg Height", f"{avg_height:.1f} inches")
            with col2:
                st.metric("Avg Weight", f"{avg_weight:.1f} lbs")
            with col3:
                min_height = physical_df['height_inches'].min()
                st.metric("Shortest Player", f"{min_height} inches")
            with col4:
                max_height = physical_df['height_inches'].max()
                st.metric("Tallest Player", f"{max_height} inches")
            
            # Height distribution chart with custom colors
            fig = px.histogram(physical_df, x='height_inches', nbins=10,
                              title=f'Height Distribution - {year_bar} Season',
                              labels={'height_inches': 'Height (inches)', 'count': 'Number of Players'},
                              color_discrete_sequence=[ILLINOIS_ORANGE])
            fig.update_layout(
                title_font_size=20,
                title_font_color=ILLINOIS_BLUE,
                font=dict(color=ILLINOIS_BLUE),
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(gridcolor='lightgray'),
                yaxis=dict(gridcolor='lightgray')
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Weight distribution chart with custom colors
            fig2 = px.histogram(physical_df, x='weight_lbs', nbins=10,
                               title=f'Weight Distribution - {year_bar} Season',
                               labels={'weight_lbs': 'Weight (lbs)', 'count': 'Number of Players'},
                               color_discrete_sequence=[ILLINOIS_BLUE])
            fig2.update_layout(
                title_font_size=20,
                title_font_color=ILLINOIS_BLUE,
                font=dict(color=ILLINOIS_BLUE),
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(gridcolor='lightgray'),
                yaxis=dict(gridcolor='lightgray')
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            # Show detailed player physical stats
            st.markdown("**Player Physical Characteristics:**")
            display_df = physical_df[['name', 'height_display', 'weight_lbs', 'height_inches'   ]].copy()
            display_df.columns = ['Player', 'Height', 'Weight (lbs)', 'Height_inches']
            display_df = display_df.sort_values('Height_inches', ascending=False)
            display_df.index.name = '#'
            st.dataframe(display_df[['Player', 'Height', 'Weight (lbs)']], use_container_width=True)
        else:
            st.warning("Physical data is incomplete for this season.")
    else:
        st.warning("Physical data not available for this season.")
    
 
else:
    st.warning(f"No roster data available for the {year_bar} season.")

st.markdown("---")
st.markdown("*Note: Roster analysis is based on available player data. Some information may be incomplete for older seasons.*")


