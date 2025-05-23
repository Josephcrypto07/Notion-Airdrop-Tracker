from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
from notion_client import Client
import os
import re
import time

# URLs for scraping
AIRDROPS_IO_URL = "https://airdrops.io/latest/"
CRYPTORANK_URL = "https://cryptorank.io/drophunting"
AIRDROPALERT_URL = "https://airdropalert.com/airdrops/"

# Keywords to filter out junk
EXCLUDE_KEYWORDS = ["zealy", "social", "spam", "fake", "discord", "telegram"]

def scrape_airdrops_io():
    print("Starting to scrape airdrops.io with Selenium...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(AIRDROPS_IO_URL)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)  # Increased to ensure dynamic content loads
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # TODO: Update this selector based on actual dynamic HTML (inspect airdrops.io)
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
                "Chain": "Unknown",
                "Difficulty": "",
                "Progress": "Not Started",
                "Risk Level": "DYOR",
                "Value Estimate": "",
                "Notes": description
            }
            print(f"Adding airdrop from airdrops.io: {name}")
            airdrops.append(airdrop)
    except Exception as e:
        print(f"Error scraping airdrops.io with Selenium: {e}")
        return []
    finally:
        driver.quit()
    return airdrops

def scrape_cryptorank():
    print("Starting to scrape CryptoRank.io...")
    try:
        response = requests.get(CRYPTORANK_URL, timeout=10)
        response.raise_for_status()
        print(f"Successfully fetched page: {CRYPTORANK_URL}")
    except requests.RequestException as e:
        print(f"Error fetching CryptoRank URL: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", lambda tag: tag.name == "table" and any(th.get_text().strip() == "Name" for th in tag.find_all("th")))
    if not table:
        print("No table found on CryptoRank page")
        return []

    print("Table found, extracting rows...")
    rows = table.find("tbody").find_all("tr") if table.find("tbody") else table.find_all("tr")
    print(f"Found {len(rows)} rows in the table")

    airdrops = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 6:
            print(f"Skipping row with insufficient cells: {len(cells)}")
            continue

        name_cell = cells[0]
        name_a = name_cell.find("a")
        name = name_a.text.strip() if name_a else "Unknown"
        task_link = "https://cryptorank.io" + name_a["href"] if name_a and "href" in name_a.attrs else ""
        task_type_text = cells[1].text.strip()
        status = cells[2].text.strip()
        reward_type = cells[3].text.strip()
        raise_funds = cells[4].text.strip()
        x_score = cells[5].text.strip()

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

        task_type_text = re.sub(r"Cost: \$\s*\d+|Time: \d+ min", "", task_type_text).strip()
        methods = [method.strip() for method in task_type_text.split(",") if method.strip()]
        task_type = "Airdrop"
        if "Testnet" in methods:
            task_type = "Testnet"
        elif "Mainnet" in methods:
            task_type = "Mainnet"

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
            "Chain": "Unknown",
            "Difficulty": "",
            "Progress": "Not Started",
            "Risk Level": "DYOR",
            "Value Estimate": "",
            "Notes": f"Reward Type: {reward_type}, Raise/Funds: {raise_funds}, X Score: {x_score}"
        }
        print(f"Adding airdrop from CryptoRank: {name}")
        airdrops.append(airdrop)
    return airdrops

def scrape_airdropalert():
    print("Starting to scrape AirdropAlert...")
    try:
        response = requests.get(AIRDROPALERT_URL, timeout=10)
        response.raise_for_status()
        print(f"Successfully fetched page: {AIRDROPALERT_URL}")
    except requests.RequestException as e:
        print(f"Error fetching AirdropAlert URL: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    # Updated selector to target h2 with links
    airdrop_listings = soup.find_all("h2", string=lambda text: text and any(text.strip().lower() not in EXCLUDE_KEYWORDS for _ in [0]))
    airdrops = []
    for listing in airdrop_listings:
        a_tag = listing.find("a")
        if a_tag:
            name = a_tag.text.strip()
            task_link = a_tag["href"] if "href" in a_tag.attrs else ""
            description_p = listing.find_next("p")
            description = description_p.text.strip() if description_p else ""
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
                "Chain": "Unknown",
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
                    "Chain": {"select": {"name": airdrop["Chain"]}},
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
    print("Starting main execution...")
    all_airdrops = []
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
