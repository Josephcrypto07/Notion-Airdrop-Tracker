import requests
from bs4 import BeautifulSoup
from notion_client import Client
import os
import re

# URLs for scraping (starting with CryptoRank.io)
CRYPTORANK_URL = "https://cryptorank.io/drophunting"

# Keywords to filter out junk
EXCLUDE_KEYWORDS = ["zealy", "social", "spam", "fake", "discord", "telegram"]

def scrape_cryptorank():
    """
    Scrape airdrop/testnet data from CryptoRank.io.
    Returns a list of dictionaries with data mapped to Notion columns.
    """
    try:
        response = requests.get(CRYPTORANK_URL, timeout=10)
        response.raise_for_status()  # Raises an error for bad HTTP responses
    except requests.RequestException as e:
        print(f"Error fetching CryptoRank URL: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")  # Adjust if the HTML structure changes
    if not table:
        print("No table found on CryptoRank page")
        return []

    rows = table.find("tbody").find_all("tr")
    airdrops = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 6:  # Ensure there are enough cells
            continue

        # Extract data from table cells
        name = cells[0].find("a").text.strip() if cells[0].find("a") else "Unknown"
        task_link = "https://cryptorank.io" + cells[0].find("a")["href"] if cells[0].find("a") else ""
        task_type_text = cells[1].text.strip()  # Contains tasks like "Social/Gaming"
        status = cells[2].text.strip().split(",")[0].strip()  # e.g., "Confirmed"
        reward_type = cells[3].text.strip()  # e.g., "Tokens"

        # Determine Cost and Time Estimate using regex
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
        task_type = "Airdrop"  # Default
        if "Testnet" in methods:
            task_type = "Testnet"
        elif "Mainnet" in methods:
            task_type = "Mainnet"

        # Filter out junk
        if any(keyword.lower() in name.lower() for keyword in EXCLUDE_KEYWORDS) or \
           any(any(keyword.lower() in method.lower() for keyword in EXCLUDE_KEYWORDS) for method in methods):
            continue

        # Map to Notion columns
        airdrop = {
            "Project Name": name,
            "Task Link": task_link,
            "Status": status if status in ["Live", "Upcoming", "Ended"] else "Live",
            "Task Type": task_type,
            "Cost": "Minimal Gas" if int(cost) > 0 else "Free",
            "Time Estimate": time_estimate,
            "Task Method": methods if methods else ["Hold"],  # Default method if none found
            "Chain": "",  # To be determined (can add logic later)
            "Difficulty": "",  # To be determined
            "Progress": "Not Started",
            "Risk Level": "DYOR",
            "Value Estimate": "",  # To be determined
            "Notes": f"Reward Type: {reward_type}" if reward_type else ""
        }
        airdrops.append(airdrop)

    return airdrops

def update_notion(airdrops):
    """
    Update the Notion database with the scraped airdrop data.
    """
    try:
        notion = Client(auth=os.environ["NOTION_TOKEN"])
        database_id = os.environ["DATABASE_ID"]

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
                    "Task Method": {"multi_select": [{"name": method} for method in airdrop["Task Method"]]},
                    "Progress": {"select": {"name": airdrop["Progress"]}},
                    "Status": {"select": {"name": airdrop["Status"]}},
                    "Risk Level": {"select": {"name": airdrop["Risk Level"]}},
                    "Value Estimate": {"select": {"name": airdrop["Value Estimate"]}} if airdrop["Value Estimate"] else {"select": {}},
                    "Task Link": {"url": airdrop["Task Link"]},
                    "Notes": {"rich_text": [{"text": {"content": airdrop["Notes"]}}]} if airdrop["Notes"] else {"rich_text": []}
                }
            }
            notion.pages.create(**page)
        print(f"Successfully updated Notion with {len(airdrops)} entries.")
    except Exception as e:
        print(f"Error updating Notion: {e}")

def main():
    """
    Main function to orchestrate scraping and updating.
    """
    # Scrape data
    airdrops = scrape_cryptorank()
    print(f"Scraped {len(airdrops)} entries from CryptoRank")

    # Update Notion if there’s data
    if airdrops:
        update_notion(airdrops)
    else:
        print("No airdrops to update after filtering")

if __name__ == "__main__":
    main()
