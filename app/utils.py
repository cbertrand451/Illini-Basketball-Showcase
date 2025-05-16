import requests
from bs4 import BeautifulSoup
import pandas as pd

def player_scrape_header_info(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    data = {}

    jersey_tag = soup.find("span", class_="sidearm-roster-player-jersey-number")
    if jersey_tag:
        data["Jersey Number"] = jersey_tag.get_text(strip=True)

    # First & Last Name
    first_name = soup.find("span", class_="sidearm-roster-player-first-name")
    last_name = soup.find("span", class_="sidearm-roster-player-last-name")
    if first_name and last_name:
        data["First Name"] = first_name.get_text(strip=True)
        data["Last Name"] = last_name.get_text(strip=True)
        data["Full Name"] = f"{data['First Name']} {data['Last Name']}"

    # Image URL
    image_div = soup.find("div", class_="sidearm-roster-player-image")
    if image_div:
        img_tag = image_div.find("img")
        if img_tag and img_tag.get("src"):
            data["Image URL"] = img_tag["src"]

    # Social links (Instagram, NIL)
    social_links = soup.find_all("a", class_="sidearm-roster-player-social-link")
    for link in social_links:
        href = link.get("href", "")
        if "instagram.com" in href:
            data["Instagram URL"] = href
        elif "opndr.se" in href:
            data["NIL URL"] = href

    # Player metadata from the fields section
    field_items = soup.select("div.sidearm-roster-player-fields li")
    for item in field_items:
        label_span = item.find("span", class_="sidearm-roster-player-field-label")
        value_span = label_span.find_next_sibling("span") if label_span else None
        if label_span and value_span:
            key = label_span.get_text(strip=True)
            value = value_span.get_text(strip=True)
            data[key] = value

    stats_section = soup.find("div", id="sidearm-roster-player-stats")
    if stats_section:
        table = stats_section.find("table")
        if table:
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            rows = []
            for row in table.find_all("tr")[1:]:  # skip header
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if cells:
                    row_dict = dict(zip(headers, cells))
                    rows.append(row_dict)
            data["Stats"] = rows

    return data


def scrape_season_stats_w_players(season="2023-24"):
    url = f"https://fightingillini.com/sports/mens-basketball/stats/{season}"
    res = requests.get(url)
    if res.status_code != 200:
        print(f"Failed for {season}")
        return None, None

    soup = BeautifulSoup(res.text, "html.parser")

    # Get team stats section
    team_section = soup.find("section", id="team")
    if team_section is None:
        print(f"Could not find team stats section for {season}")
        return None, None
    team_table = team_section.find("table")
    team_stats = extract_stat_table(team_table, season)

    # Get player stats section
    player_section = soup.find("section", id="individual-overall")
    if player_section is None:
        print(f"Could not find player stats section for {season}")
        return team_stats, None
    player_table = player_section.find("table")
    player_stats = extract_player_table(player_table, season)

    return team_stats, player_stats


def extract_stat_table(table, season):
    rows = []
    for tr in table.find_all("tr")[1:]:  # skip header row
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue  # skip malformed rows

        # First column = stat label
        stat_span = tds[0].find("span", class_="hide-on-small-down")
        stat = stat_span.get_text(strip=True) if stat_span else tds[0].get_text(strip=True)

        illinois = tds[1].get_text(strip=True) if len(tds) > 1 else None
        opponents = tds[2].get_text(strip=True) if len(tds) > 2 else None

        rows.append({
            "Statistic": stat,
            "Illinois": illinois,
            "Opponents": opponents,
            "Season": season
        })

    return pd.DataFrame(rows)



def extract_player_table(table, season):
    headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]
    rows = []

    for tr in table.find("tbody").find_all("tr"):
        tds = tr.find_all("td")
        if not tds or len(tds) < 2:
            continue

        row_data = {}
        for i in range(min(len(headers), len(tds))):
            header = headers[i]

            if header == "Player":
                name_tag = tds[i].find("a")
                raw_name = name_tag.get_text(strip=True) if name_tag else tds[i].get_text(strip=True)

                # Convert "Last, First" → "First Last"
                if "," in raw_name:
                    last, first = raw_name.split(",", 1)
                    formatted_name = first.strip() + " " + last.strip()
                else:
                    formatted_name = raw_name.strip()

                row_data["Player"] = formatted_name
            else:
                row_data[header] = tds[i].get_text(strip=True)

        row_data["Season"] = season
        rows.append(row_data)

    return pd.DataFrame(rows)