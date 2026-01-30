import os
import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

TARGETS = [
    {"url": "https://bridges.torproject.org/bridges?transport=obfs4", "file": "obfs4.txt", "type": "obfs4", "ip": "IPv4"},
    {"url": "https://bridges.torproject.org/bridges?transport=webtunnel", "file": "webtunnel.txt", "type": "WebTunnel", "ip": "IPv4"},
    {"url": "https://bridges.torproject.org/bridges?transport=vanilla", "file": "vanilla.txt", "type": "Vanilla", "ip": "IPv4"},
    {"url": "https://bridges.torproject.org/bridges?transport=obfs4&ipv6=yes", "file": "obfs4_ipv6.txt", "type": "obfs4", "ip": "IPv6"},
    {"url": "https://bridges.torproject.org/bridges?transport=webtunnel&ipv6=yes", "file": "webtunnel_ipv6.txt", "type": "WebTunnel", "ip": "IPv6"},
    {"url": "https://bridges.torproject.org/bridges?transport=vanilla&ipv6=yes", "file": "vanilla_ipv6.txt", "type": "Vanilla", "ip": "IPv6"},
]

HISTORY_FILE = "bridge_history.json"
RECENT_HOURS = 72
HISTORY_RETENTION_DAYS = 30
REPO_URL = "https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def is_valid_bridge_line(line):
    if "No bridges available" in line:
        return False
    if line.startswith("#"):
        return False
    if len(line) < 10:
        return False
    return bool(re.search(r'\d+\.\d+\.\d+\.\d+|\[.*\]', line))

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        log(f"Error saving history: {e}")

def cleanup_history(history):
    cutoff = datetime.now() - timedelta(days=HISTORY_RETENTION_DAYS)
    new_history = {
        k: v for k, v in history.items() 
        if datetime.fromisoformat(v) > cutoff
    }
    return new_history

def update_readme(stats):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    readme_content = f"""# Tor Bridges Collector & Archive

**Last Updated:** {timestamp}

This repository automatically collects, validates, and archives Tor bridges. A GitHub Action runs every 3 hours to fetch new bridges from the official Tor Project.

## 🔥 Important Notes on IPv6 & WebTunnel

1.  **IPv6 Instability:** IPv6 bridges are significantly fewer in number and are often more susceptible to blocking or connection instability compared to IPv4.
2.  **WebTunnel Overlap:** WebTunnel bridges often use the same endpoint domain for both IPv4 and IPv6. Consequently, the IPv6 list is frequently identical to or a subset of the IPv4 list.
3.  **Recommendation:** For the most reliable connection, **prioritize using IPv4 bridges**. Use IPv6 only if IPv4 is completely inaccessible on your network.

## 🔥 Bridge Lists

### 1. Fresh Bridges (Last 72 Hours)
Use these files for the most reliable connections. These contain bridges discovered within the last 3 days.

| Transport | IPv4 (72h) | Count | IPv6 (72h) | Count |
| :--- | :--- | :--- | :--- | :--- |
| **obfs4** | [obfs4_72h.txt]({REPO_URL}/obfs4_72h.txt) | **{stats.get('obfs4_72h.txt', 0)}** | [obfs4_ipv6_72h.txt]({REPO_URL}/obfs4_ipv6_72h.txt) | **{stats.get('obfs4_ipv6_72h.txt', 0)}** |
| **WebTunnel** | [webtunnel_72h.txt]({REPO_URL}/webtunnel_72h.txt) | **{stats.get('webtunnel_72h.txt', 0)}** | [webtunnel_ipv6_72h.txt]({REPO_URL}/webtunnel_ipv6_72h.txt) | **{stats.get('webtunnel_ipv6_72h.txt', 0)}** |
| **Vanilla** | [vanilla_72h.txt]({REPO_URL}/vanilla_72h.txt) | **{stats.get('vanilla_72h.txt', 0)}** | [vanilla_ipv6_72h.txt]({REPO_URL}/vanilla_ipv6_72h.txt) | **{stats.get('vanilla_ipv6_72h.txt', 0)}** |

### 2. Full Archive (Accumulative)
These files contain the history of all collected bridges.

| Transport | IPv4 (All Time) | Count | IPv6 (All Time) | Count |
| :--- | :--- | :--- | :--- | :--- |
| **obfs4** | [obfs4.txt]({REPO_URL}/obfs4.txt) | **{stats.get('obfs4.txt', 0)}** | [obfs4_ipv6.txt]({REPO_URL}/obfs4_ipv6.txt) | **{stats.get('obfs4_ipv6.txt', 0)}** |
| **WebTunnel** | [webtunnel.txt]({REPO_URL}/webtunnel.txt) | **{stats.get('webtunnel.txt', 0)}** | [webtunnel_ipv6.txt]({REPO_URL}/webtunnel_ipv6.txt) | **{stats.get('webtunnel_ipv6.txt', 0)}** |
| **Vanilla** | [vanilla.txt]({REPO_URL}/vanilla.txt) | **{stats.get('vanilla.txt', 0)}** | [vanilla_ipv6.txt]({REPO_URL}/vanilla_ipv6.txt) | **{stats.get('vanilla_ipv6.txt', 0)}** |

## 🔥 Automation Logic

-   **Schedule:** Runs every 3 hours.
-   **Retention:** 
    -   `*_72h.txt` files contain bridges seen in the last 3 days.
    -   `bridge_history.json` is automatically cleaned to remove entries older than 30 days.

## 🔥 Disclaimer
This project is for educational and archival purposes. Please use these bridges responsibly.
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    log("README.md updated with latest statistics.")

def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    
    history = load_history()
    history = cleanup_history(history)
    
    recent_cutoff_time = datetime.now() - timedelta(hours=RECENT_HOURS)
    stats = {}
    
    log("Starting Bridge Scraper Session...")

    for target in TARGETS:
        url = target["url"]
        filename = target["file"]
        recent_filename = filename.replace(".txt", f"_{RECENT_HOURS}h.txt")
        
        existing_bridges = set()
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if is_valid_bridge_line(line):
                            existing_bridges.add(line)
            except:
                pass

        fetched_bridges = set()
        try:
            response = session.get(url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                bridge_div = soup.find("div", id="bridgelines")
                
                if bridge_div:
                    raw_text = bridge_div.get_text()
                    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
                    
                    for line in lines:
                        if is_valid_bridge_line(line):
                            fetched_bridges.add(line)
                            
                            if line not in history:
                                history[line] = datetime.now().isoformat()
                else:
                    log(f"Warning: No bridge container for {filename}.")
            else:
                log(f"Failed to fetch {url}. Status: {response.status_code}")

        except Exception as e:
            log(f"Connection error for {filename}: {e}")

        all_bridges = existing_bridges.union(fetched_bridges)
        
        if all_bridges:
            with open(filename, "w", encoding="utf-8") as f:
                for bridge in sorted(all_bridges):
                    f.write(bridge + "\n")
            log(f"Processed {filename}: Total {len(all_bridges)}")
        else:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("")

        recent_bridges = []
        for bridge in all_bridges:
            if bridge in history:
                try:
                    first_seen = datetime.fromisoformat(history[bridge])
                    if first_seen > recent_cutoff_time:
                        recent_bridges.append(bridge)
                except ValueError:
                    pass
        
        if recent_bridges:
            with open(recent_filename, "w", encoding="utf-8") as f:
                for bridge in sorted(recent_bridges):
                    f.write(bridge + "\n")
        else:
            with open(recent_filename, "w", encoding="utf-8") as f:
                f.write("")
        
        stats[filename] = len(all_bridges)
        stats[recent_filename] = len(recent_bridges)

    save_history(history)
    update_readme(stats)
    log("Session Finished.")

if __name__ == "__main__":
    main()
