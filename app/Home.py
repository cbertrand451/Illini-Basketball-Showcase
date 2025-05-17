import streamlit as st

st.set_page_config(page_title="Illini Basketball Hub", layout="wide")

st.title("Fighting Illini Men's Basketball Database")
st.subheader(":orange[An Interactive Experience into the UIUC Roster]")
"---"
st.subheader("Where to Start")
st.markdown("There are many tools available on this site. Check out these pages to explore the statistics and players that go into the UIUC Men's basketball roster.")

null1, col1, mid1, col2, mid2, col3, null2 = st.columns([0.75, 2, 0.25, 2, 0.25, 2, 0.75])
with col1:
    st.subheader("Team Overview", divider='blue')
    st.markdown("Choose a Season and explore the statistics relating to the team from that year. Basic insights like season averages and percentages, " \
    "but also roster statistics like height/weight, location, and class balances. Compare a specific roster with the entire UIUC history basketball " \
    "average, or chose another year to coompare to. Statistics are backed up with interactive visuals that display the history of the team!")
with col2:
    st.subheader("Player Dashboard", divider='orange')

with col3:
    st.subheader("Performance Predictor", divider='blue')