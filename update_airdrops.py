import requests
from bs4 import BeautifulSoup
from notion_client import Client
import os
import re

# URLs for scraping
AIRDROPS_IO_URL = "https://airdrops.io/latest/"
CRYPTORANK_URL = "https://cryptorank.io/drophunting"
AIRDROPALERT_URL = "https://airdropalert.com/airdrops/"

# Keywords to filter out junk
EXCLUDE_KEYWORDS = ["zealy", "social", "spam", "fake", "discord", "telegram"]

def scrape_airdrops_io():
    """Scrape airdrop data from airdrops.io. Returns a list of standardized dictionaries."""
    print("Starting to scrape airdrops.io...")
    try:
        response = requests.get(AIRDROPS_IO_URL, timeout=10)
        response.raise_for_status()
        print(f"Successfully fetched page: {AIRDROPS_IO_URL}")
    except requests.RequestException as e:
        print(f"Error fetching airdrops.io URL: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    # TODO: Update the selector based on actual HTML structure
    airdrop_containers = soup.find_all("div", class_="airdrop-item")  # Placeholder
    if not airdrop_containers:
        print("No airdrop containers found on airdrops.io")
        return []

    print(f"Found {len(airdrop_containers)} airdrop containers")
    airdrops = []
    for container in airdrop_containers:
        name = container.find("h2").text.strip() if container.find("h2") else "Unknown"
        task_link = container.find("a")["href"] if container.find("a") else ""
        description = container.find("p").text.strip() if container.find("p") else ""

        # Filter out junk
        if any(keyword.lower() in name.lower() or keyword.lower() in description.lower() for keyword in EXCLUDE_KEYWORDS):
            print(f"Filtered out entry: {name} (contains excluded keywords)")
            continue

        airdrop = {
            "Project Name": name,
            "Task Link": task_link,
            "Status": "Live",
            "Task Type": "Airdrop",
            "Cost": "Free",
            "Time Estimate": "",
            "Task Method": [],
            "Chain": "",
            "Difficulty": "",
            "Progress": "Not Started",
            "Risk Level": "DYOR",
            "Value Estimate": "",
            "Notes": description
        }
        print(f"Adding airdrop from airdrops.io: {name}")
        airdrops.append(airdrop)

    return airdrops

def scrape_cryptorank():
    """Scrape airdrop/testnet data from CryptoRank.io. Returns a list of standardized dictionaries."""
    print("Starting to scrape CryptoRank.io...")
    try:
        response = requests.get(CRYPTORANK_URL, timeout=10)
        response.raise_for_status()
        print(f"Successfully fetched page: {CRYPTORANK_URL}")
    except requests.RequestException as e:
        print(f"Error fetching CryptoRank URL: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    # TODO: Update the selector based on actual HTML structure
    table = soup.find("table")  # Placeholder
    if not table:
        print("No table found on CryptoRank page")
        return []

    print("Table found, extracting rows...")
    rows = table.find("tbody").find_all("tr")
    print(f"Found {len(rows)} rows in the table")

    airdrops = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 6:
            print(f"Skipping row with insufficient cells: {len(cells)}")
            continue

        name = cells[0].find("a").text.strip() if cells[0].find("a") else "Unknown"
        task_link = "https://cryptorank.io" + cells[0].find("a")["href"] if cells[0].find("a") else ""
        task_type_text = cells[1].text.strip()
        status = cells[2].text.strip().split(",")[0].strip()
        reward_type = cells[3].text.strip()

        # Extract Cost and Time Estimate
        cost_match = re.search(r"Cost: \$\s*(\d+)", task_type_text)
        cost = cost_match.group(1) if cost_match else "0"
        time_match = re.search(r"Time: (\d+) min", task_type_text)
        time_minutes = int(time_match.group(1)) if time_match else None
        time_estimate = ""
        if time_minutes:
            if time_minutes < 30:
                time_estimate = "<30 mins"
            elif time_minutes < 60:
                time_estimate = "30–60 mins"
            else:
                time_estimate = "1hr+"

        # Clean task_type_text and extract methods
        task_type_text = re.sub(r"Cost: \$\s*\d+|Time: \d+ min", "", task_type_text).strip()
        methods = [method.strip() for method in task_type_text.split(",") if method.strip()]

        # Determine Task Type
        task_type = "Airdrop"
        if "Testnet" in methods:
            task_type = "Testnet"
        elif "Mainnet" in methods:
            task_type = "Mainnet"

        # Filter out junk
        if any(keyword.lower() in name.lower() for keyword in EXCLUDE_KEYWORDS) or \
           any(any(keyword.lower() in method.lower() for keyword in EXCLUDE_KEYWORDS) for method in methods):
            print(f"Filtered out entry: {name} (contains excluded keywords)")
            continue

        airdrop = {
            "Project Name": name,
            "Task Link": task_link,
            "Status": status if status in ["Live", "Upcoming", "Ended"] else "Live",
            "Task Type": task_type,
            "Cost": "Minimal Gas" if int(cost) > 0 else "Free",
            "Time Estimate": time_estimate,
            "Task Method": methods if methods else ["Hold"],
            "Chain": "",
            "Difficulty": "",
            "Progress": "Not Started",
            "Risk Level": "DYOR",
            "Value Estimate": "",
            "Notes": f"Reward Type: {reward_type}" if reward_type else ""
        }
        print(f"Adding airdrop from CryptoRank: {name}")
        airdrops.append(airdrop)

    return airdrops

def scrape_airdropalert():
    """Scrape airdrop data from AirdropAlert. Returns a list of standardized dictionaries."""
    print("Starting to scrape AirdropAlert...")
    try:
        response = requests.get(AIRDROPALERT_URL, timeout=10)
        response.raise_for_status()
        print(f"Successfully fetched page: {AIRDROPALERT_URL}")
    except requests.RequestException as e:
        print(f"Error fetching AirdropAlert URL: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    # TODO: Update the selector based on actual HTML structure
    airdrop_cards = soup.find_all("div", class_="airdrop-card")  # Placeholder
    if not airdrop_cards:
        print("No airdrop cards found on AirdropAlert")
        return []

    print(f"Found {len(airdrop_cards)} airdrop cards")
    airdrops = []
    for card in airdrop_cards:
        name = card.find("h3").text.strip() if card.find("h3") else "Unknown"
        task_link = card.find("a")["href"] if card.find("a") else ""
        description = card.find("p").text.strip() if card.find("p") else ""

        # Filter out junk
        if any(keyword.lower() in name.lower() or keyword.lower() in description.lower() for keyword in EXCLUDE_KEYWORDS):
            print(f"Filtered out entry: {name} (contains excluded keywords)")
            continue

        airdrop = {
            "Project Name": name,
            "Task Link": task_link,
            "Status": "Live",
            "Task Type": "Airdrop",
            "Cost": "Free",
            "Time Estimate": "",
            "Task Method": [],
            "Chain": "",
            "Difficulty": "",
            "Progress": "Not Started",
            "Risk Level": "DYOR",
            "Value Estimate": "",
            "Notes": description
        }
        print(f"Adding airdrop from AirdropAlert: {name}")
        airdrops.append(airdrop)

    return airdrops

def update_notion(airdrops):
    """Update the Notion database with the scraped airdrop data."""
    print("Starting to update Notion...")
    try:
        notion = Client(auth=os.environ["NOTION_TOKEN"])
        database_id = os.environ["DATABASE_ID"]
        print(f"Connected to Notion, using database ID: {database_id}")

        for airdrop in airdrops:
            page = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Project Name": {"title": [{"text": {"content": airdrop["Project Name"]}}]},
                    "Chain": {"select": {"name": airdrop["Chain"]}} if airdrop["Chain"] else {"select": {}},
                    "Task Type": {"select": {"name": airdrop["Task Type"]}},
                    "Cost": {"select": {"name": airdrop["Cost"]}},
                    "Time Estimate": {"select": {"name": airdrop["Time Estimate"]}} if airdrop["Time Estimate"] else {"select": {}},
                    "Difficulty": {"select": {"name": airdrop["Difficulty"]}} if airdrop["Difficulty"] else {"select": {}},
                    "Task Method": {"multi_select": [{"name": method} for method in airdrop["Task Method"]]} if airdrop["Task Method"] else {"multi_select": []},
                    "Progress": {"select": {"name": airdrop["Progress"]}},
                    "Status": {"select": {"name": airdrop["Status"]}},
                    "Risk Level": {"select": {"name": airdrop["Risk Level"]}},
                    "Value Estimate": {"select": {"name": airdrop["Value Estimate"]}} if airdrop["Value Estimate"] else {"select": {}},
                    "Task Link": {"url": airdrop["Task Link"]},
                    "Notes": {"rich_text": [{"text": {"content": airdrop["Notes"]}}]} if airdrop["Notes"] else {"rich_text": []}
                }
            }
            print(f"Creating Notion page for: {airdrop['Project Name']}")
            notion.pages.create(**page)
        print(f"Successfully updated Notion with {len(airdrops)} entries")
    except Exception as e:
        print(f"Error updating Notion: {e}")

def main():
    """Main function to scrape from all sources and update Notion."""
    print("Starting main execution...")
    all_airdrops = []

    # Scrape from each source
    all_airdrops.extend(scrape_airdrops_io())
    all_airdrops.extend(scrape_cryptorank())
    all_airdrops.extend(scrape_airdropalert())

    print(f"Total airdrops after scraping from all sources: {len(all_airdrops)}")

    if all_airdrops:
        update_notion(all_airdrops)
    else:
        print("No airdrops to update after filtering")

if __name__ == "__main__":
    main()
