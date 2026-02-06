import os
import requests
import json
import re
import socket
import concurrent.futures
import time
import ipaddress
import ssl
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
MAX_WORKERS = 80
CONNECTION_TIMEOUT = 20
MAX_RETRIES = 5
SSL_TIMEOUT = 8

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
    return True

def extract_connection_info(bridge_line):
    bridge_line = bridge_line.strip()
    
    if not bridge_line or len(bridge_line) < 5:
        return None, None, None
    
    transport = None
    host = None
    port = None
    
    if bridge_line.startswith("obfs4"):
        transport = "obfs4"
        parts = bridge_line.split()
        if len(parts) >= 2:
            host_port = parts[1]
            if host_port.startswith("["):
                match = re.search(r'\[(.*?)\]:(\d+)', host_port)
                if match:
                    host = match.group(1)
                    port = int(match.group(2))
            else:
                match = re.search(r'([^:]+):(\d+)', host_port)
                if match:
                    host = match.group(1)
                    port = int(match.group(2))
    
    elif bridge_line.startswith("webtunnel"):
        transport = "webtunnel"
        parts = bridge_line.split()
        if len(parts) >= 2:
            host_port = parts[1]
            if host_port.startswith("["):
                match = re.search(r'\[(.*?)\]:(\d+)', host_port)
                if match:
                    host = match.group(1)
                    port = int(match.group(2))
            else:
                match = re.search(r'([^:]+):(\d+)', host_port)
                if match:
                    host = match.group(1)
                    port = int(match.group(2))
        
        if not port:
            port = 443
    
    else:
        transport = "vanilla"
        parts = bridge_line.split()
        if len(parts) >= 1:
            host_port = parts[0]
            if host_port.startswith("["):
                match = re.search(r'\[(.*?)\]:(\d+)', host_port)
                if match:
                    host = match.group(1)
                    port = int(match.group(2))
            else:
                match = re.search(r'([^:]+):(\d+)', host_port)
                if match:
                    host = match.group(1)
                    port = int(match.group(2))
    
    return host, port, transport

def test_webtunnel_ssl(host, port, timeout):
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        sock = socket.create_connection((host, port), timeout=timeout)
        ssl_sock = context.wrap_socket(sock, server_hostname=host)
        ssl_sock.settimeout(SSL_TIMEOUT)
        
        ssl_sock.send(b"GET / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
        response = ssl_sock.recv(1024)
        
        ssl_sock.close()
        return True
    except Exception as e:
        return False

def test_tcp_connection(host, port, timeout, transport):
    for attempt in range(MAX_RETRIES):
        try:
            log(f"  Testing {host}:{port} ({transport}) - Attempt {attempt + 1}/{MAX_RETRIES}")
            
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.settimeout(3)
            
            if transport == "webtunnel":
                try:
                    sock.send(b"GET / HTTP/1.0\r\n\r\n")
                    response = sock.recv(1024)
                    if response:
                        sock.close()
                        return True
                except:
                    pass
            
            sock.close()
            return True
            
        except socket.timeout:
            log(f"  Timeout connecting to {host}:{port}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
            continue
        except ConnectionRefusedError:
            log(f"  Connection refused by {host}:{port}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(0.5)
            continue
        except OSError as e:
            log(f"  OS error connecting to {host}:{port}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(0.5)
            continue
        except Exception as e:
            log(f"  Error connecting to {host}:{port}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(0.5)
            continue
    
    return False

def test_single_bridge(bridge_line):
    host, port, transport = extract_connection_info(bridge_line)
    
    if not host or not port:
        log(f"  Invalid bridge format: {bridge_line[:50]}...")
        return False
    
    log(f"Testing bridge: {bridge_line[:80]}...")
    
    try:
        ip_obj = ipaddress.ip_address(host)
        is_ipv6 = isinstance(ip_obj, ipaddress.IPv6Address)
    except ValueError:
        try:
            resolved = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            if not resolved:
                log(f"  Could not resolve host: {host}")
                return False
            is_ipv6 = any(addr[0] == socket.AF_INET6 for addr in resolved)
        except:
            log(f"  DNS resolution failed for: {host}")
            return False
    
    timeout = CONNECTION_TIMEOUT
    
    if transport == "webtunnel":
        if test_tcp_connection(host, port, timeout, transport) or test_webtunnel_ssl(host, port, timeout):
            log(f"  ✓ WebTunnel {host}:{port} is working")
            return True
    else:
        if test_tcp_connection(host, port, timeout, transport):
            log(f"  ✓ {transport} {host}:{port} is working")
            return True
    
    log(f"  ✗ {transport} {host}:{port} failed all connection attempts")
    return False

def test_bridge_batch(bridge_list, target_name):
    if not bridge_list:
        log(f"No bridges to test for {target_name}")
        return []
    
    log(f"\n{'='*60}")
    log(f"STARTING CONNECTIVITY TESTS FOR: {target_name}")
    log(f"Total bridges to test: {len(bridge_list)}")
    log(f"{'='*60}")
    
    successful = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_bridge = {executor.submit(test_single_bridge, bridge): bridge for bridge in bridge_list}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_bridge)):
            bridge = future_to_bridge[future]
            try:
                if future.result():
                    successful.append(bridge)
            except Exception as e:
                log(f"Exception testing bridge: {e}")
            
            if (i + 1) % 10 == 0:
                log(f"Progress: {i + 1}/{len(bridge_list)} tested, {len(successful)} successful so far")
    
    log(f"\nTest results for {target_name}:")
    log(f"  Total tested: {len(bridge_list)}")
    log(f"  Successful: {len(successful)}")
    log(f"  Failed: {len(bridge_list) - len(successful)}")
    
    if successful:
        log(f"Sample of working bridges ({min(5, len(successful))} of {len(successful)}):")
        for i, bridge in enumerate(successful[:5]):
            log(f"  {i+1}. {bridge[:100]}...")
    
    return successful

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

This repository automatically collects, validates, and archives Tor bridges. A GitHub Action runs every 1 hours to fetch new bridges from the official Tor Project.

## 🔥 Important Notes on IPv6 & WebTunnel

1.  **IPv6 Instability:** IPv6 bridges are significantly fewer in number and are often more susceptible to blocking or connection instability compared to IPv4.
2.  **WebTunnel Overlap:** WebTunnel bridges often use the same endpoint domain for both IPv4 and IPv6. Consequently, the IPv6 list is frequently identical to or a subset of the IPv4 list.
3.  **Recommendation:** For the most reliable connection, **prioritize using IPv4 bridges**. Use IPv6 only if IPv4 is completely inaccessible on your network.

## 🔥 Bridge Lists

### ✅ Tested & Active (Recommended)
These bridges from the archive have passed a TCP connectivity test (5 retries, 20s timeout) during the last run.

| Transport | IPv4 (Tested) | Count | IPv6 (Tested) | Count |
| :--- | :--- | :--- | :--- | :--- |
| **obfs4** | [obfs4_tested.txt]({REPO_URL}/obfs4_tested.txt) | **{stats.get('obfs4_tested.txt', 0)}** | [obfs4_ipv6_tested.txt]({REPO_URL}/obfs4_ipv6_tested.txt) | **{stats.get('obfs4_ipv6_tested.txt', 0)}** |
| **WebTunnel** | [webtunnel_tested.txt]({REPO_URL}/webtunnel_tested.txt) | **{stats.get('webtunnel_tested.txt', 0)}** | [webtunnel_ipv6_tested.txt]({REPO_URL}/webtunnel_ipv6_tested.txt) | **{stats.get('webtunnel_ipv6_tested.txt', 0)}** |
| **Vanilla** | [vanilla_tested.txt]({REPO_URL}/vanilla_tested.txt) | **{stats.get('vanilla_tested.txt', 0)}** | [vanilla_ipv6_tested.txt]({REPO_URL}/vanilla_ipv6_tested.txt) | **{stats.get('vanilla_ipv6_tested.txt', 0)}** |

### 🔥 Fresh Bridges (Last 72 Hours)
Bridges discovered within the last 3 days.

| Transport | IPv4 (72h) | Count | IPv6 (72h) | Count |
| :--- | :--- | :--- | :--- | :--- |
| **obfs4** | [obfs4_72h.txt]({REPO_URL}/obfs4_72h.txt) | **{stats.get('obfs4_72h.txt', 0)}** | [obfs4_ipv6_72h.txt]({REPO_URL}/obfs4_ipv6_72h.txt) | **{stats.get('obfs4_ipv6_72h.txt', 0)}** |
| **WebTunnel** | [webtunnel_72h.txt]({REPO_URL}/webtunnel_72h.txt) | **{stats.get('webtunnel_72h.txt', 0)}** | [webtunnel_ipv6_72h.txt]({REPO_URL}/webtunnel_ipv6_72h.txt) | **{stats.get('webtunnel_ipv6_72h.txt', 0)}** |
| **Vanilla** | [vanilla_72h.txt]({REPO_URL}/vanilla_72h.txt) | **{stats.get('vanilla_72h.txt', 0)}** | [vanilla_ipv6_72h.txt]({REPO_URL}/vanilla_ipv6_72h.txt) | **{stats.get('vanilla_ipv6_72h.txt', 0)}** |

### 🔥 Full Archive (Accumulative)
History of all collected bridges.

| Transport | IPv4 (All Time) | Count | IPv6 (All Time) | Count |
| :--- | :--- | :--- | :--- | :--- |
| **obfs4** | [obfs4.txt]({REPO_URL}/obfs4.txt) | **{stats.get('obfs4.txt', 0)}** | [obfs4_ipv6.txt]({REPO_URL}/obfs4_ipv6.txt) | **{stats.get('obfs4_ipv6.txt', 0)}** |
| **WebTunnel** | [webtunnel.txt]({REPO_URL}/webtunnel.txt) | **{stats.get('webtunnel.txt', 0)}** | [webtunnel_ipv6.txt]({REPO_URL}/webtunnel_ipv6.txt) | **{stats.get('webtunnel_ipv6.txt', 0)}** |
| **Vanilla** | [vanilla.txt]({REPO_URL}/vanilla.txt) | **{stats.get('vanilla.txt', 0)}** | [vanilla_ipv6.txt]({REPO_URL}/vanilla_ipv6.txt) | **{stats.get('vanilla_ipv6.txt', 0)}** |


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
    
    log("\n" + "="*80)
    log("STARTING TOR BRIDGES COLLECTOR SESSION")
    log("="*80)

    for target in TARGETS:
        url = target["url"]
        filename = target["file"]
        recent_filename = filename.replace(".txt", f"_{RECENT_HOURS}h.txt")
        tested_filename = filename.replace(".txt", "_tested.txt")
        transport_type = target["type"]
        ip_version = target["ip"]
        
        log(f"\n{'='*60}")
        log(f"PROCESSING: {transport_type} - {ip_version}")
        log(f"URL: {url}")
        log(f"{'='*60}")
        
        existing_bridges = set()
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if is_valid_bridge_line(line):
                            existing_bridges.add(line)
                log(f"Loaded {len(existing_bridges)} existing bridges from {filename}")
            except Exception as e:
                log(f"Error loading existing bridges: {e}")

        fetched_bridges = set()
        try:
            log(f"Fetching bridges from {url}")
            response = session.get(url, timeout=45)
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
                    
                    log(f"Fetched {len(fetched_bridges)} new bridges from Tor Project")
                else:
                    log(f"Warning: No bridge container for {filename}.")
            else:
                log(f"Failed to fetch {url}. Status: {response.status_code}")

        except Exception as e:
            log(f"Connection error for {filename}: {e}")

        all_bridges = list(existing_bridges.union(fetched_bridges))
        
        log(f"Total bridges for {filename}: {len(all_bridges)}")
        
        if all_bridges:
            with open(filename, "w", encoding="utf-8") as f:
                for bridge in sorted(all_bridges):
                    f.write(bridge + "\n")
            log(f"Saved {len(all_bridges)} bridges to {filename}")
        else:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("")
            log(f"No bridges available for {filename}")

        recent_bridges = []
        for bridge in all_bridges:
            if bridge in history:
                try:
                    first_seen = datetime.fromisoformat(history[bridge])
                    if first_seen > recent_cutoff_time:
                        recent_bridges.append(bridge)
                except ValueError:
                    pass
        
        log(f"Recent bridges (last {RECENT_HOURS}h): {len(recent_bridges)}")
        
        if recent_bridges:
            with open(recent_filename, "w", encoding="utf-8") as f:
                for bridge in sorted(recent_bridges):
                    f.write(bridge + "\n")
            log(f"Saved {len(recent_bridges)} recent bridges to {recent_filename}")
        else:
            with open(recent_filename, "w", encoding="utf-8") as f:
                f.write("")
        
        tested_bridges = test_bridge_batch(all_bridges, f"{transport_type} {ip_version}")
        
        if tested_bridges:
            with open(tested_filename, "w", encoding="utf-8") as f:
                for bridge in sorted(tested_bridges):
                    f.write(bridge + "\n")
            log(f"Saved {len(tested_bridges)} working bridges to {tested_filename}")
        else:
            with open(tested_filename, "w", encoding="utf-8") as f:
                f.write("")
            log(f"No working bridges found for {filename}")

        stats[filename] = len(all_bridges)
        stats[recent_filename] = len(recent_bridges)
        stats[tested_filename] = len(tested_bridges)
        
        log(f"\nSummary for {transport_type} - {ip_version}:")
        log(f"  Archive: {stats[filename]} bridges")
        log(f"  Recent ({RECENT_HOURS}h): {stats[recent_filename]} bridges")
        log(f"  Working: {stats[tested_filename]} bridges")
        log(f"{'='*60}")

    log(f"\n{'='*80}")
    log("SESSION SUMMARY")
    log(f"{'='*80}")
    
    summary_table = []
    summary_table.append("Type               | IPv4 Total | IPv4 Recent | IPv4 Working | IPv6 Total | IPv6 Recent | IPv6 Working")
    summary_table.append("-" * 95)
    
    for transport in ["obfs4", "WebTunnel", "Vanilla"]:
        ipv4_total = stats.get(f"{transport.lower()}.txt", 0)
        ipv4_recent = stats.get(f"{transport.lower()}_{RECENT_HOURS}h.txt", 0)
        ipv4_working = stats.get(f"{transport.lower()}_tested.txt", 0)
        ipv6_total = stats.get(f"{transport.lower()}_ipv6.txt", 0)
        ipv6_recent = stats.get(f"{transport.lower()}_ipv6_{RECENT_HOURS}h.txt", 0)
        ipv6_working = stats.get(f"{transport.lower()}_ipv6_tested.txt", 0)
        
        summary_table.append(f"{transport:<18} | {ipv4_total:>10} | {ipv4_recent:>11} | {ipv4_working:>12} | {ipv6_total:>10} | {ipv6_recent:>11} | {ipv6_working:>12}")
    
    for line in summary_table:
        log(line)
    
    save_history(history)
    update_readme(stats)
    
    log(f"\n{'='*80}")
    log("SESSION COMPLETED")
    log(f"{'='*80}")

if __name__ == "__main__":
    main()
