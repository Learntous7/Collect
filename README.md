# Tor Bridges Collector & Archive

**Last Updated:** 2026-02-06 08:39 UTC

## 📊 Overall Statistics
| Metric | Count | Percentage |
|--------|-------|------------|
| Total Bridges Collected | 293 | 100% |
| Successfully Tested | 181 | 61.8% |
| New Bridges (72h) | 113 | 38.6% |
| History Retention | 30 days | - |

This repository automatically collects, validates, and archives Tor bridges. A GitHub Action runs every hour to fetch new bridges from the official Tor Project.

## ⚠️ Important Notes on IPv6 & WebTunnel
1. **IPv6 Instability:** IPv6 bridges are significantly fewer in number and are often more susceptible to blocking or connection instability compared to IPv4.
2. **WebTunnel Overlap:** WebTunnel bridges often use the same endpoint domain for both IPv4 and IPv6. Consequently, the IPv6 list is frequently identical to or a subset of the IPv4 list.
3. **Recommendation:** For the most reliable connection, **prioritize using IPv4 bridges**. Use IPv6 only if IPv4 is completely inaccessible on your network.

## 🔥 Bridge Lists

### ✅ Tested & Active (Recommended)
These bridges from the archive have passed a TCP/SSL connectivity test (2 retries, 8s timeout) during the last run.

| Transport | IPv4 (Tested) | Count | IPv6 (Tested) | Count | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **obfs4** | [obfs4_tested.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/obfs4_tested.txt) | **68** | [obfs4_ipv6_tested.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/obfs4_ipv6_tested.txt) | **0** | 81.9% |
| **WebTunnel** | [webtunnel_tested.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/webtunnel_tested.txt) | **20** | [webtunnel_ipv6_tested.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/webtunnel_ipv6_tested.txt) | **20** | 76.9% |
| **Vanilla** | [vanilla_tested.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/vanilla_tested.txt) | **73** | [vanilla_ipv6_tested.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/vanilla_ipv6_tested.txt) | **0** | 61.3% |

### 🔥 Fresh Bridges (Last 72 Hours)
Bridges discovered within the last 3 days. Updated every hour.

| Transport | IPv4 (72h) | Count | IPv6 (72h) | Count | New Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **obfs4** | [obfs4_72h.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/obfs4_72h.txt) | **34** | [obfs4_ipv6_72h.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/obfs4_ipv6_72h.txt) | **14** | 41.0% |
| **WebTunnel** | [webtunnel_72h.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/webtunnel_72h.txt) | **9** | [webtunnel_ipv6_72h.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/webtunnel_ipv6_72h.txt) | **9** | 34.6% |
| **Vanilla** | [vanilla_72h.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/vanilla_72h.txt) | **47** | [vanilla_ipv6_72h.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/vanilla_ipv6_72h.txt) | **0** | 39.5% |

### 📁 Full Archive (Accumulative)
History of all collected bridges since the beginning.

| Transport | IPv4 (All Time) | Count | IPv6 (All Time) | Count | Total |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **obfs4** | [obfs4.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/obfs4.txt) | **83** | [obfs4_ipv6.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/obfs4_ipv6.txt) | **39** | **122** |
| **WebTunnel** | [webtunnel.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/webtunnel.txt) | **26** | [webtunnel_ipv6.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/webtunnel_ipv6.txt) | **26** | **52** |
| **Vanilla** | [vanilla.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/vanilla.txt) | **119** | [vanilla_ipv6.txt](https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridges/vanilla_ipv6.txt) | **0** | **119** |

### ⚙️ Technical Details
- **Connection Test:** TCP for obfs4/Vanilla, SSL/TLS for WebTunnel
- **Test Parameters:** 2 retries, 8s timeout
- **Maximum Workers:** 50 concurrent tests
- **History Retention:** 30 days
- **Update Frequency:** Every hour
- **Last Run:** 2026-02-06 08:39 UTC

## 🔥 Disclaimer
This project is for educational and archival purposes. Please use these bridges responsibly.
