# Tor Bridges Collector & Archive

This repository automatically collects, validates, and archives Tor bridges. A GitHub Action runs hourly to fetch new bridges from the official Tor Project and appends unique entries to the lists.


## 📂 Bridge Lists (Raw Links)

Use these direct links to import bridges into Tor Browser, Orbot, or other clients:

| Transport Type | IPv4 | IPv6 |
| :--- | :--- | :--- |
| **obfs4** | [obfs4.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/obfs4.txt) | [obfs4_ipv6.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/obfs4_ipv6.txt) |
| **WebTunnel** | [webtunnel.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/webtunnel.txt) | [webtunnel_ipv6.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/webtunnel_ipv6.txt) |
| **Vanilla** | [vanilla.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/vanilla.txt) | [vanilla_ipv6.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/vanilla_ipv6.txt) |

## ⚙️ Automation

- **Frequency:** Runs every hour via GitHub Actions.
- **Logic:** Fetches source > Compares with existing archive > Appends only new/unique bridges.
- **Source:** `bridges.torproject.org`

## ⚠️ Disclaimer

This project is for educational and archival purposes. I am not affiliated with the Tor Project. Please use these bridges responsibly to bypass censorship.
