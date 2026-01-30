import os
import requests
from bs4 import BeautifulSoup

TARGETS = [
    {"url": "https://bridges.torproject.org/bridges?transport=obfs4", "file": "obfs4.txt"},
    {"url": "https://bridges.torproject.org/bridges?transport=webtunnel", "file": "webtunnel.txt"},
    {"url": "https://bridges.torproject.org/bridges?transport=vanilla", "file": "vanilla.txt"},
    {"url": "https://bridges.torproject.org/bridges?transport=obfs4&ipv6=yes", "file": "obfs4_ipv6.txt"},
    {"url": "https://bridges.torproject.org/bridges?transport=webtunnel&ipv6=yes", "file": "webtunnel_ipv6.txt"},
    {"url": "https://bridges.torproject.org/bridges?transport=vanilla&ipv6=yes", "file": "vanilla_ipv6.txt"},
]

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

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
            except Exception:
                pass

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                bridge_div = soup.find("div", id="bridgelines")
                
                if bridge_div:
                    raw_text = bridge_div.get_text()
                    new_lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
                    
                    updated = False
                    for line in new_lines:
                        if not line.startswith("#") and line not in existing_bridges:
                            existing_bridges.add(line)
                            updated = True
                    
                    if updated or not os.path.exists(filename):
                        with open(filename, "w", encoding="utf-8") as f:
                            for bridge in sorted(existing_bridges):
                                f.write(bridge + "\n")
        except Exception:
            pass

if __name__ == "__main__":
    main()
