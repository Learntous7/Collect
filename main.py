import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

TARGETS = [
    {"url": "https://bridges.torproject.org/bridges?transport=obfs4", "file": "obfs4.txt"},
    {"url": "https://bridges.torproject.org/bridges?transport=webtunnel", "file": "webtunnel.txt"},
    {"url": "https://bridges.torproject.org/bridges?transport=vanilla", "file": "vanilla.txt"},
    {"url": "https://bridges.torproject.org/bridges?transport=obfs4&ipv6=yes", "file": "obfs4_ipv6.txt"},
    {"url": "https://bridges.torproject.org/bridges?transport=webtunnel&ipv6=yes", "file": "webtunnel_ipv6.txt"},
    {"url": "https://bridges.torproject.org/bridges?transport=vanilla&ipv6=yes", "file": "vanilla_ipv6.txt"},
]

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    total_new_bridges_session = 0

    log("Starting Bridge Scraper Session...")

    for target in TARGETS:
        url = target["url"]
        filename = target["file"]
        existing_bridges = set()
        
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    for line in f:
                        clean_line = line.strip()
                        if clean_line:
                            existing_bridges.add(clean_line)
            except Exception as e:
                log(f"Error reading {filename}: {e}")

        initial_count = len(existing_bridges)
        fetched_bridges = set()
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                bridge_div = soup.find("div", id="bridgelines")
                
                if bridge_div:
                    raw_text = bridge_div.get_text()
                    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
                    
                    for line in lines:
                        if not line.startswith("#"):
                            fetched_bridges.add(line)
                else:
                    log(f"Warning: No bridge container found for {filename} (CAPTCHA likely).")
            else:
                log(f"Failed to fetch {url}. Status: {response.status_code}")

        except Exception as e:
            log(f"Connection error for {filename}: {e}")

        new_entries = fetched_bridges - existing_bridges
        count_new = len(new_entries)
        total_new_bridges_session += count_new

        if count_new > 0:
            existing_bridges.update(new_entries)
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    for bridge in sorted(existing_bridges):
                        f.write(bridge + "\n")
                log(f"SUCCESS: {filename} | Fetched: {len(fetched_bridges)} | New: {count_new} | Total Archived: {len(existing_bridges)}")
            except Exception as e:
                log(f"Error writing to {filename}: {e}")
        else:
            if len(fetched_bridges) > 0:
                log(f"Info: {filename} | Fetched: {len(fetched_bridges)} | No new unique bridges found.")
            else:
                log(f"Info: {filename} | No bridges retrieved.")

    log(f"Session Finished. Total new bridges added across all files: {total_new_bridges_session}")

if __name__ == "__main__":
    main()
