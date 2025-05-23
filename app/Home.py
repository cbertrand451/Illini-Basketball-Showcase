import streamlit as st
import pickle

st.set_page_config(page_title="Illini Basketball Hub", layout="wide")

st.title("Fighting Illini Men's Basketball Database")
st.subheader(":orange[An Interactive Experience into the UIUC Roster]")
st.caption('By Colin Bertrand')
"---"
st.subheader("Where to Start")
st.markdown("There are many tools available on this site. Check out these pages to explore the statistics and players that go into the UIUC Men's basketball roster.")

null1, col1, mid1, col2, mid2, col3, null2 = st.columns([0.75, 2, 0.25, 2, 0.25, 2, 0.75])
with col1:
    st.subheader("Team Overview", divider='blue')
    st.markdown("Choose a season and explore team statistics from that year. These include season averages and shooting " \
    "percentages to roster details like height, weight, hometown, and class balance. Compare a specific year's roster to " \
    "the all-time Illinois average or to another selected season. All statistics are supported with interactive visuals that " \
    "highlight the rich history of Illini basketball.")
with col2:
    st.subheader("Player Dashboard", divider='orange')
    st.markdown("Select any player from the history of the Illinois men's basketball team. Each player's headshot and " \
    "summary information are scraped from the official Fighting Illini website. The player's hometown is displayed on " \
    "an interactive map. Explore season-by-season stat lines, including a custom efficiency score based on John Hollinger’s " \
    "basketball rating formula. A radar chart visualizes the player’s stats compared to team averages from the same season.")
with col3:
    st.subheader("Efficiency Predictor", divider='blue')
    st.markdown("This tool enables users to select a player and input projected variables such as minutes played, usage rate, " \
    "and other in-game factors. A predictive model then estimates key performance metrics — including points, rebounds, and " \
    "assists per game (PPG, RPG, APG). Users can explore 'what-if' scenarios to assess how changes in playtime or role might " \
    "impact a player's statistical output and on-court effectiveness.")
"---"

st.header("Fighting Illini Men's Basketball History")
with open('data\processed\mbb_history.json', 'rb') as f:
    titles_dict = pickle.load(f)


col1, col2 = st.columns([2, 3])

for title, df in titles_dict.items():
    if len(df) == 1:
        with col1:
            st.subheader(f':orange[{title}]')
            st.markdown(df[0][0])
            "---"
    else:
        st.subheader(f':orange[{title}]')
        df.index = range(1, len(df) + 1)
        df.index.name = 'Rank'
        i1 = title.split('By')[1].strip()
        for col in df:
            if col == 0:
                df = df.drop(columns=[col])
            if col == 1:
                df = df.rename(columns={1: i1})
            if col == 2 and ('-' in df[col].iloc[0]):
                df = df.rename(columns={2:'W/L'})
            else:
                df = df.rename(columns={col:'Year'})
        
        st.table(df)
        "---"