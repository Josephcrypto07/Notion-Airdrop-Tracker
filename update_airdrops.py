from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
from notion_client import Client
import os
import time

# URLs
AIRDROPS_IO_URL = "https://airdrops.io/latest/"
CRYPTORANK_URL = "https://cryptorank.io/drophunting"
AIRDROPALERT_URL = "https://airdropalert.com/airdrops/"

def setup_chrome():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return chrome_options

def scrape_airdrops_io():
    print("Scraping airdrops.io...")
    driver = None
    try:
        driver = webdriver.Chrome(options=setup_chrome())
        driver.get(AIRDROPS_IO_URL)
        
        # Wait for dynamic content
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.airdrop-item"))
        )
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        containers = soup.find_all("div", class_="airdrop-item")
        
        airdrops = []
        for container in containers:
            name = container.find("h3").get_text(strip=True) if container.find("h3") else "Unknown"
            link = container.find("a", href=True)["href"] if container.find("a") else ""
            
            airdrops.append({
                "Project Name": name,
                "Task Link": link,
                "Chain": "Unknown",
                "Task Type": "Airdrop",
                "Time Estimate": "<30 mins",
                "Status": "Live",
                "Risk Level": "DYOR"
            })
        return airdrops
    except Exception as e:
        print(f"Airdrops.io error: {e}")
        return []
    finally:
        if driver:
            driver.quit()

def scrape_cryptorank():
    print("Scraping CryptoRank...")
    try:
        response = requests.get(CRYPTORANK_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table tr:has(td)")
        
        airdrops = []
        for row in rows:
            cells = row.find_all("td")
            name = cells[0].get_text(strip=True)
            chain_img = cells[0].find("img")
            chain = chain_img["alt"] if chain_img else "Unknown"
            
            airdrops.append({
                "Project Name": name,
                "Chain": chain,
                "Task Type": "Airdrop",
                "Time Estimate": "30–60 mins",
                "Status": "Live",
                "Risk Level": "Medium"
            })
        return airdrops
    except Exception as e:
        print(f"CryptoRank error: {e}")
        return []

def update_notion(airdrops):
    notion = Client(auth=os.environ["NOTION_TOKEN"])
    database_id = os.environ["DATABASE_ID"]
    
    for entry in airdrops:
        properties = {
            "Project Name": {"title": [{"text": {"content": entry["Project Name"]}}},
            "Chain": {"select": {"name": entry["Chain"]}},
            "Task Type": {"select": {"name": entry["Task Type"]}},
            "Time Estimate": {"select": {"name": entry["Time Estimate"]}},
            "Status": {"select": {"name": entry["Status"]}},
            "Risk Level": {"select": {"name": entry["Risk Level"]}},
        }
        notion.pages.create(parent={"database_id": database_id}, properties=properties)

def main():
    all_airdrops = []
    all_airdrops.extend(scrape_airdrops_io())
    all_airdrops.extend(scrape_cryptorank())
    
    if all_airdrops:
        update_notion(all_airdrops)
        print(f"Added {len(all_airdrops)} entries to Notion")
    else:
        print("No data scraped")

if __name__ == "__main__":
    main()
