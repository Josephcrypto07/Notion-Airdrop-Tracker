import requests
from bs4 import BeautifulSoup
from notion_client import Client
import os
import re

def scrape_cryptorank():
    url = "[invalid url, do not cite]
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")  # Adjust if needed
    if table:
        rows = table.find("tbody").find_all("tr")
        airdrops = []
        exclude_keywords = ["Zealy", "social spam", "fake"]  # Add more as needed
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 6:
                name = cells[0].find("a").text.strip() if cells[0].find("a") else "Unknown"
                task_link = "[invalid url, do not cite] + cells[0].find("a")["href"] if cells[0].find("a") else ""
                task_type_text = cells[1].text.strip()
                cost_match = re.search(r"Cost: \$\s*(\d+)", task_type_text)
                cost = cost_match.group(1) if cost_match else None
                time_match = re.search(r"Time: (\d+) min", task_type_text)
                time_minutes = int(time_match.group(1)) if time_match else None
                if time_minutes:
                    if time_minutes < 30:
                        time_estimate = "<30 mins"
                    elif time_minutes < 60:
                        time_estimate = "30–60 mins"
                    else:
                        time_estimate = "1hr+"
                else:
                    time_estimate = ""
                task_type_text = re.sub(r"Cost: \$\s*\d+|Time: \d+ min", "", task_type_text).strip()
                methods = [method.strip() for method in task_type_text.split(",") if method.strip()]
                status = cells[2].text.strip().split(",")[0].strip()
                reward_type = cells[3].text.strip()
                # Determine Task Type
                if "Testnet" in methods:
                    task_type = "Testnet"
                elif "Mainnet" in methods:
                    task_type = "Mainnet"
                else:
                    task_type = "Airdrop"
                # Check for exclude keywords
                if any(keyword.lower() in name.lower() for keyword in exclude_keywords) or any(any(keyword.lower() in method.lower() for keyword in exclude_keywords) for method in methods):
                    continue
                airdrop = {
                    "Project Name": name,
                    "Task Link": task_link,
                    "Status": status,
                    "Task Type": task_type,
                    "Cost": "Minimal Gas" if cost and int(cost) > 0 else "Free",
                    "Time Estimate": time_estimate,
                    "Task Method": methods,
                    "Chain": "",
                    "Difficulty": "",
                    "Progress": "Not Started",
                    "Risk Level": "DYOR",
                    "Value Estimate": "",
                    "Notes": "",
                }
                airdrops.append(airdrop)
        return airdrops
    else:
        return []

def update_notion(airdrops):
    notion = Client(auth=os.environ["NOTION_TOKEN"])
    database_id = os.environ["DATABASE_ID"]
    for airdrop in airdrops:
        page = {
            "parent": {"database_id": database_id},
            "properties": {
                "Project Name": {"title": [{"text": {"content": airdrop["Project Name"]}}]},
                "Chain": {"select": {}},
                "Task Type": {"select": {"name": airdrop["Task Type"]}},
                "Cost": {"select": {"name": airdrop["Cost"]}},
                "Time Estimate": {"select": {"name": airdrop["Time Estimate"]}} if airdrop["Time Estimate"] else {"select": {}},
                "Difficulty": {"select": {}},
                "Task Method": {"multi_select": [{"name": method} for method in airdrop["Task Method"]]} if airdrop["Task Method"] else {"multi_select": []},
                "Progress": {"select": {"name": airdrop["Progress"]}},
                "Status": {"select": {"name": airdrop["Status"]}},
                "Risk Level": {"select": {"name": airdrop["Risk Level"]}},
                "Value Estimate": {"select": {}},
                "Task Link": {"url": airdrop["Task Link"]} if airdrop["Task Link"] else {"url": ""},
                "Notes": {"rich_text": []},
            }
        }
        notion.pages.create(**page)

if __name__ == "__main__":
    airdrops = scrape_cryptorank()
    update_notion(airdrops)
