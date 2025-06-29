import streamlit as st
import json
from geopy.geocoders import Nominatim
import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
from sklearn.preprocessing import StandardScaler
import re
from utils import player_scrape_header_info, scrape_season_stats_w_players, extract_stat_table, extract_player_table, extract_background_image_url, fix_df
from colors import ILLINOIS_BLUE, ILLINOIS_ORANGE, ILLINOIS_GRAY

#setting up page configs
st.set_page_config(page_title="Player Dashboard", 
                   layout="wide")

st.title('Player Dashboard')
st.subheader(":orange[Featuring Detailed Player Information]")
"---"
#loading the player list
with open('data/processed/player_list.json', 'r') as f:
    data = json.load(f)
# all of the player names
player_options = list(data.keys())
col1, col2, col3 = st.columns([1, 1.5, 1])
with col1:
    bar = st.selectbox("Search for a Player", player_options)
# links
player_url = data[bar][0]
# list of years the player played
player_yrs = data[bar][1]
#st.markdown(player_url)
# the basic info on the person
player_info = player_scrape_header_info(player_url)
del player_info['First Name']
del player_info['Last Name']
#st.markdown(player_info)
with col1:
    if ('Image URL' in player_info):
        st.image(player_info['Image URL'], use_container_width=True)
        del player_info['Image URL']
    elif (extract_background_image_url(player_url) is not None):
        player_info['Image URL'] = extract_background_image_url(player_url)
        if player_info['Image URL'] != 'https://s3.amazonaws.com/assets.sidearmsports.com/images/generic_image_missing.png':
            st.image(player_info['Image URL'], use_container_width=True)
        else:
            st.image('data/images/MBB_logo.webp', caption='Image not found')
        del player_info['Image URL']
    if ('Instagram URL' in player_info):
        st.link_button('Instagram URL', player_info['Instagram URL'], use_container_width=True)
        del player_info['Instagram URL']
    if ('NIL URL' in player_info):
        st.link_button('NIL URL', player_info['NIL URL'], use_container_width=True)
        del player_info['NIL URL']
with col2:
    if ('Jersey Number' in player_info):
        st.header(f":orange[{player_info['Jersey Number']}] - {player_info['Full Name']}")
        del player_info['Jersey Number']
        full_name = player_info['Full Name']
        del player_info['Full Name']
    else:
        st.header(player_info['Full Name'])
        full_name = player_info['Full Name']
        del player_info['Full Name']
    if ('Class' in player_info):
        st.subheader(player_info['Class'])
        del player_info['Class']
    with st.container(border=True):
        for key in player_info:
            st.markdown(f"{key}: {player_info[key]}")
    st.subheader(f'Years @ UIUC: {len(player_yrs)}')
with col3:
    if 'Hometown' in player_info:
        geolocator = Nominatim(user_agent="streamlit-geocoder")
        location = geolocator.geocode(player_info['Hometown'])

        if location:
            df = pd.DataFrame([{
                'city': player_info['Hometown'],
                'lat': location.latitude,
                'lon': location.longitude
            }])

            # Create the pydeck layer with custom color
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position='[lon, lat]',
                get_color='[255, 95, 5, 160]',
                get_radius=8,
                radius_units='pixels',
                
                pickable=True
            )

            # Define the map view
            view_state = pdk.ViewState(
                latitude=location.latitude,
                longitude=location.longitude,
                zoom=10,
                pitch=0
            )

            # Display map
            st.pydeck_chart(pdk.Deck(
                layers=[layer], 
                initial_view_state=view_state, 
                map_style="mapbox://styles/mapbox/light-v9",
                ))
            st.caption(f"{full_name}'s Hometown")

        else:
            st.markdown('Hometown not found')
    else:
        st.markdown('Hometown not found')

'---'
col1, col2 = st.columns([1, 3])
with col1:
    yr = st.selectbox("Choose Year", player_yrs)        
year_n = float(yr[0:4])
if year_n >= 1979:
    # team dataset and player dataset
    df_team, df_players = scrape_season_stats_w_players(yr)
    df_players = fix_df(df_players)
    #dropping the 'TM' row
    df_players = df_players.drop(df_players.index[-1])
    # getting rid of the useless columns
    df_players = df_players.drop(columns=['#', 'Bio Link'])

    # numeric columns
    stats = ['GP', 'GS', 'Minutes TOT', 
                             'Minutes AVG', 'FGM', 'FGA', 'FG%', '3PT', '3PTA', 
                             '3PT%', 'FTM', 'FTA', 'FT%', 'PTS', 'Scoring AVG', 
                             'OFF', 'DEF', 'Rebounds TOT', 'Rebounds AVG', 'PF', 
                             'AST', 'TO', 'STL', 'BLK']
    #change those columns to be numeric dtypes
    df_players[stats] = df_players[stats].apply(pd.to_numeric, errors='coerce')

    df_players['EFF'] = round((df_players['PTS'] + df_players['Rebounds TOT'] + df_players['AST'] + 
                                df_players['STL'] + df_players['BLK'] - (df_players['FGA'] 
                                - df_players['FGM']) - (df_players['FTA'] - df_players['FTM']) - df_players['TO']) / df_players['GP'], 3)
    
    stats = ['GP', 'GS', 'Minutes TOT', 
                             'Minutes AVG', 'FGM', 'FGA', 'FG%', '3PT', '3PTA', 
                             '3PT%', 'FTM', 'FTA', 'FT%', 'PTS', 'Scoring AVG', 
                             'OFF', 'DEF', 'Rebounds TOT', 'Rebounds AVG', 'PF', 
                             'AST', 'TO', 'STL', 'BLK', 'EFF']
    # tool to standardize the data
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df_players[stats])
    #standardized dataset
    df_scaled = pd.DataFrame(scaled, columns=stats)
    df_scaled['Player'] = df_players['Player'].values
    #creating an argument case
    filtered = df_scaled[df_scaled['Player'] == full_name]
    if not filtered.empty:
        player_row = filtered.iloc[0]
    else:
        st.subheader(f"{full_name} was not found in the {yr} dataset...")
        st.markdown("This is likely due to a [redshirted season](https://en.wikipedia.org/wiki/Redshirt_(college_sports)). " \
                    "This may also be due to season injury or special case. Sorry for the inconvenience!")
        st.stop()
    #get the row of the person that user chose
    player_row = df_scaled[df_scaled['Player'] == full_name].iloc[0]
    team_avg = df_scaled[stats].mean()
    #did this so I could diplsay the normal data under the visual
    n_team_avg = round(df_players[stats].mean(), 3)

    #with col2:
        
    #Build radar plot
    fig = go.Figure()

    #Team average line
    fig.add_trace(go.Scatterpolar(
        r=team_avg.values,
        theta=stats,
        fill='toself',
        name='Team Average', 
        line_color=ILLINOIS_GRAY
    ))

    #Player line
    fig.add_trace(go.Scatterpolar(
        r=player_row[stats].values,
        theta=stats,
        fill='toself',
        name=full_name, 
        line_color=ILLINOIS_ORANGE
    ))

    #Layout
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        title="Player vs Team Average (Standardized)",
        showlegend=True, 
        width=450, 
        height=700
    )

    player_row_n = df_players[df_players['Player'] == full_name].iloc[0]

    with col2:
        st.markdown("")
        st.subheader(f"Efficiency Rating: {player_row_n['EFF']:.2f}")
    cola, colb = st.columns(2)
    #heres the chart
    with cola:
        st.plotly_chart(fig, use_container_width=True)
    #creating the team average row data
    n_team_avg['Player'] = 'Team Average'
    #reate comparison dataframe with player and team average
    player_data = df_players[df_players['Player'] == full_name].iloc[0]
    comparison_df = pd.DataFrame({
        'Statistic': player_data.index,
        'Player': player_data.values,
        'Team Average': [n_team_avg.get(col, '') for col in player_data.index]
    })
    df_display = comparison_df[comparison_df['Statistic'] != 'Player']

    #show the df
    with colb:
        st.dataframe(df_display, use_container_width=True, hide_index=True, column_config={
        "Statistic": st.column_config.TextColumn(
            "Statistic",
            width="medium",
            help="Statistic name"
        ),
    })

    #in case people dont know the abbreviations
    definitions = st.toggle("Show Terms Key")
    if definitions:
        st.markdown('**GP**: Games Played')
        st.markdown('**GS**: Games Started')
        st.markdown('**Minutes**: Minutes Played')
        st.markdown('**FG**: Field Goals Made')
        st.markdown('**3PT**: 3-Point Field Goals Made')
        st.markdown('**FT**: Free Throws Made')
        st.markdown('**Scoring**: Field Goal Percentage (decimal)')
        st.markdown('**Rebounds**: Total Rebounds')
        st.markdown('**PF**: Personal Fouls')
        st.markdown('**AST**: Assists')
        st.markdown('**TO**: Turnovers')
        st.markdown('**STL**: Steals')
        st.markdown('**BLK**: Blocks')
        st.markdown('**TOT**: Total')
        st.markdown('**AVG**: Average Per Game')
        st.markdown('**FGM**: Field Goals Made')
        st.markdown('**FGA**: Field Goals Attempted')
        st.markdown('**FG%**: Field Goal Percentage')
        st.markdown('**3PTA**: 3-Point Attempts')
        st.markdown('**3PT%**: 3-Point Percentage')
        st.markdown('**FTM**: Free Throws Made')
        st.markdown('**FTA**: Free Throws Attempted')
        st.markdown('**FT%**: Free Throw Percentage')
        st.markdown('**EFF**: Efficiency Rating')

else:
    st.subheader("Statistical Data only available for 1979-80 -> present. You're too far back!", divider='orange')