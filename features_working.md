### **Feature 1: Tor Relay Enumeration**

*   **Purpose:** To get a live list of all the public servers (relays) that make up the Tor network.
*   **How it Works:**
    1.  It uses the `stem` Python library, which is a specialized tool for communicating with a running Tor instance.
    2.  It connects to your local Tor service through the **Control Port** (port 9051).
    3.  After authenticating with your Tor password, it sends a command (`get_network_statuses()`) to ask Tor for its current view of the entire network.
    4.  It loops through the hundreds or thousands of relays in the response and extracts key details for each one: its unique `fingerprint`, its `nickname`, its IP `address`, and its `flags` (e.g., if it's a fast relay, an exit node, etc.).
*   **Input:** A running Tor instance with the Control Port correctly configured.
*   **Output:** A JSON file named `output/feature_1_tor_relays.json`.
*   **Role in Pipeline:** **Situational Awareness.** This is an independent data collection step that provides a snapshot of the Tor network's health and composition at a given moment.

### **Feature 2: .onion Domain Discovery**

*   **Purpose:** To automatically discover new and active `.onion` websites by starting from a small list of known sites.
*   **How it Works:**
    1.  It starts with a hardcoded list of "seed" URLs (onion search engines like Ahmia).
    2.  For each URL, it uses a `subprocess` to call the `curl` command-line tool, configured to route its traffic through your local Tor **SOCKS Proxy** (port 9050). This fetches the raw HTML of the onion site.
    3.  It then uses the `BeautifulSoup` library to parse this HTML.
    4.  It performs two extraction methods:
        *   It finds all hyperlink tags (`<a href="...">`) and pulls out any that point to another `.onion` address.
        *   It also scans the entire visible text of the page with a regex pattern to find onion addresses that might not be hyperlinked.
    5.  It adds all newly found domains to a master list and recursively repeats the process for the new links, up to a defined `max_depth`.
*   **Input:** A hardcoded list of seed URLs within the script.
*   **Output:** A JSON report named `output/feature_2_onion_domains.json` containing a structured list of all unique domains discovered.
*   **Role in Pipeline:** **Primary Data Collection.** This feature generates the initial targets (the onion sites) that will be scraped for intelligence in the next step.

### **Feature 3: Marketplace Scraper**

*   **Purpose:** To visit a specific `.onion` marketplace URL and extract structured information from its listings, such as product titles, vendor names, and prices.
*   **How it Works:**
    1.  It uses the `requests` library configured with a robust **retry strategy** to handle the unreliability of the Tor network.
    2.  All requests are routed through the Tor SOCKS proxy.
    3.  It fetches the HTML of a hardcoded `TARGET_URL`.
    4.  It uses `BeautifulSoup` with a resilient, multi-selector approach. It first tries a list of common CSS selectors (e.g., `div.product`, `article.post`) to find the main listing blocks.
    5.  For each block it finds, it uses another list of selectors to try and extract the `title`, `vendor_handle`, and `price`.
    6.  Crucially, it also extracts the **full raw text** of each listing (`full_text_content`), which is the primary input for many of the later analysis features.
*   **Input:** A hardcoded `TARGET_URL` within the script.
*   **Output:** A JSON file named `output/feature_3_marketplace_scrape.json` containing a list of all the scraped items.
*   **Role in Pipeline:** **Primary Intelligence Collection.** This is the most critical data source for the rest of the pipeline. Its output is the raw material that will be analyzed by almost every subsequent feature.

### **Feature 4: API Enrichment**

*   **Purpose:** To take a list of basic Indicators of Compromise (IOCs) and enrich them with contextual information from various free threat intelligence APIs.
*   **How it Works:**
    1.  It defines functions for different IOC types: `enrich_ip`, `enrich_domain`, and `enrich_hash`.
    2.  **For IPs:** It queries IP-API (for geolocation), BGPView (for network/ASN info), and AbuseIPDB (for abuse scores).
    3.  **For Domains:** It queries OTX AlienVault for any associated threat intelligence pulses.
    4.  **For Hashes:** It queries VirusTotal (for malware detection ratios) and OTX AlienVault.
    5.  It carefully manages API rate limits by including a `time.sleep()` delay between requests to each service.
*   **Input:** A predefined list of IOCs in the `main` block (in a real pipeline, this would come from the output of Feature 6).
*   **Output:** A JSON file named `output/feature_4_api_enrichment.json` containing the original IOC plus all the data returned from the external APIs.
*   **Role in Pipeline:** **Enrichment.** This script takes basic data and adds valuable context, turning a simple IP address into a detailed profile.

### **Feature 5: STIX/TAXII Feed Parsing**

*   **Purpose:** To connect to public threat intelligence feeds and pull down the latest reported malicious indicators.
*   **How it Works:**
    1.  It maintains a dictionary of known feed sources (e.g., Abuse.ch URLhaus, Malware Bazaar).
    2.  It iterates through each source and uses the `requests` library to fetch the data. It correctly handles the specific requirements of each API (e.g., sending a POST request to Malware Bazaar).
    3.  It has dedicated parsing functions (`parse_abuse_ch_malware`, `parse_abuse_ch_urlhaus`) to transform the unique JSON structure of each feed into a standardized format.
    4.  Finally, it runs an IOC extraction process on the collected indicators to create a clean, consolidated list of new IPs, domains, hashes, and URLs.
*   **Input:** A hardcoded dictionary of threat feed URLs.
*   **Output:** A JSON report named `output/feature_5_stix_taxii_feeds.json` containing all parsed indicators and a summary of extracted IOCs.
*   **Role in Pipeline:** **Data Collection.** This feature acts as another source of raw intelligence, supplementing the data found by the scraper.

### **Feature 6: IOC Extraction**

*   **Purpose:** To parse raw, unstructured text and pull out any and all potential Indicators of Compromise.
*   **How it Works:**
    1.  It defines a comprehensive dictionary of **compiled regex patterns**, one for each IOC type (IPs, hashes, BTC addresses, emails, CVEs, etc.).
    2.  It takes a block of text as input.
    3.  It systematically runs every regex pattern against the text, collecting all matches.
    4.  It then runs a `validate_iocs` method that applies secondary checks to filter out common false positives (e.g., removing private IP addresses like 192.168.1.1).
*   **Input:** Raw text (in the `main` block, this is a sample string; in the full pipeline, it would be the `full_text_content` from the `marketplace_scraper.py` output).
*   **Output:** A JSON file named `output/feature_6_extracted_iocs.json` containing a dictionary of all valid IOCs, grouped by type.
*   **Role in Pipeline:** **Extraction.** This is a fundamental "parsing" step. It takes the unstructured text from Feature 3 and turns it into structured, machine-readable data that can be used by the enrichment features (4, 9, 10).

### **Feature 7: Named Entity Recognition (NER)**

*   **Purpose:** To read a block of text and identify key named entities like people, organizations, and groups (e.g., "Russian hackers," "Conti group").
*   **How it Works:**
    1.  It uses the `spaCy` library, a powerful Natural Language Processing (NLP) framework.
    2.  It loads a pre-trained English language model (`en_core_web_sm`).
    3.  It processes the input text through the NLP pipeline.
    4.  It then iterates through the entities (`doc.ents`) identified by the model and filters for specific types: `PERSON` (people), `ORG` (organizations), and `NORP` (nationalities, religious, or political groups).
*   **Input:** Raw text from a sample file (in the pipeline, this would come from the marketplace scraper).
*   **Output:** A JSON file named `output/feature_7_ner_analysis.json` listing the entities found, grouped by type.
*   **Role in Pipeline:** **Extraction & Analysis.** This script extracts human-centric intelligence from the raw text, providing context about *who* is involved, which complements the technical data from the IOC extractor.

### **Feature 8: Hash Extraction & Analysis**

*   **Purpose:** To specifically find file hashes in text and enrich them with malware intelligence from VirusTotal.
*   **How it Works:**
    1.  It uses regex to extract MD5, SHA1, and SHA256 hashes from a block of text.
    2.  For each unique hash found, it makes an API call to the VirusTotal v3 API.
    3.  It parses the VirusTotal response to get the most important data point: the "last analysis stats" (how many antivirus engines flagged the file as malicious, suspicious, or harmless).
    4.  It includes robust rate-limiting (`time.sleep(16)`) to stay within the free API's limit of 4 requests per minute.
*   **Input:** Text data from a sample file. In the pipeline, this would be the output of the scraper.
*   **Output:** A JSON report named `output/feature_8_hash_analysis.json` containing the hashes found and their corresponding VirusTotal enrichment data.
*   **Role in Pipeline:** **Extraction & Enrichment.** This is a specialized version of Features 4 and 6, focusing solely on the high-value task of identifying and vetting potential malware.

### **Feature 9: Infrastructure Mapping**

*   **Purpose:** To perform a deep analysis of an IP address by correlating data from multiple sources to build a detailed infrastructure profile and risk assessment.
*   **How it Works:**
    1.  It takes a list of IP addresses as input.
    2.  For each IP, it queries three different APIs:
        *   **BGPView:** To get Autonomous System (AS) number, network owner, and description.
        *   **Shodan:** (If API key is provided) To get open ports, running services, and known vulnerabilities.
        *   **AbuseIPDB:** (If API key is provided) To get the "abuse confidence score" and usage type (e.g., "Data Center," "VPN").
    3.  It then runs an `_analyze_infrastructure` method that synthesizes these results into a single risk score and a human-readable risk level (e.g., "HIGH", "MEDIUM").
*   **Input:** A list of IP addresses (in the pipeline, this would come from the `feature_6_extracted_iocs.json` file).
*   **Output:** A JSON report named `output/feature_9_infrastructure_mapping.json` with a detailed profile and risk analysis for each IP.
*   **Role in Pipeline:** **High-Level Analysis & Enrichment.** This feature provides deep context on the operational infrastructure used by threat actors.

### **Feature 10: Geolocation Correlation**

*   **Purpose:** To analyze IP addresses specifically for geographic patterns and risks.
*   **How it Works:**
    1.  It takes a list of IP addresses as input.
    2.  For each IP, it queries the free **IP-API** service to get country, city, and ISP information.
    3.  It then runs an `_analyze_geolocation` method that checks for two main risk factors:
        *   Is the IP's country on a predefined list of `HIGH_RISK_COUNTRIES`?
        *   Is the ISP a known `VPN_PROVIDER`?
    4.  It generates a list of risk factors based on these checks.
*   **Input:** A list of IP addresses (from the IOC extractor).
*   **Output:** A JSON report named `output/feature_10_geolocation_correlation.json` with the geo-data and risk factors for each IP.
*   **Role in Pipeline:** **Analysis & Enrichment.** This provides geographic context, which is a crucial piece of the intelligence puzzle.

### **Feature 11: Handle Correlation**

*   **Purpose:** To identify known threat actors by correlating vendor handles scraped from marketplaces with a local database of known aliases.
*   **How it Works:**
    1.  It first loads a local file, `known_handles.json`, which acts as a simple database of known threat actors and their associated groups/risks.
    2.  It takes a list of handles (e.g., vendor names from the scraper) as input.
    3.  It performs a case-insensitive check for each input handle against the keys in the known handles database.
    4.  If a match is found, it tags the handle as "known" and includes the details from the database. Otherwise, it's tagged as "unknown."
*   **Input:** A list of handles (in the pipeline, this would be the `vendor_handle` field from the scraper's output).
*   **Output:** A JSON file named `output/feature_11_handle_correlation.json` listing each handle and its status.
*   **Role in Pipeline:** **Analysis & Correlation.** This is a critical step for attribution, linking anonymous-looking vendor names to well-known threat actor profiles.

### **Feature 12: Behavioral Analysis**

*   **Purpose:** To move beyond simple IOCs and analyze the *behavior* of vendors over time to identify sophisticated or high-risk actors.
*   **How it Works:**
    1.  It ingests a list of marketplace posts (from the scraper).
    2.  It groups all posts by `vendor_handle`.
    3.  For each vendor, it performs multiple analyses:
        *   **Posting Patterns:** Calculates the average time between posts, the most active day/hour, and how many marketplaces they operate on.
        *   **Sentiment Analysis:** Uses the `TextBlob` library to calculate the average polarity (positive/negative) and subjectivity of their posts.
        *   **Risk Profiling:** Scans their posts for keywords related to high-risk activities (ransomware, exploits), recruitment (RaaS), and trust-building (escrow).
    4.  It combines the scores from all these analyses into a final `overall_threat_level` (e.g., "CRITICAL", "HIGH").
*   **Input:** The JSON output from Feature 3 (Marketplace Scraper).
*   **Output:** A detailed JSON report named `output/feature_12_behavioral_analysis.json` containing a complete behavioral profile for every vendor.
*   **Role in Pipeline:** **High-Level Intelligence Generation.** This is one of the most advanced features, turning raw posts into a nuanced understanding of a vendor's operational patterns and threat level.

### **Feature 13: Reputation Scoring**

*   **Purpose:** To calculate a simple, quantifiable reputation score for vendors based on community feedback and history.
*   **How it Works:**
    1.  It takes a list of vendor objects, each containing fields like `positive_feedback`, `negative_feedback`, and `first_seen`.
    2.  It applies a weighted formula:
        *   Starts with a neutral score of 50.
        *   Adds points for positive feedback.
        *   Subtracts *more* points for negative feedback.
        *   Applies a bonus or penalty based on the ratio of positive to total feedback.
        *   Adds a small bonus based on the vendor's age (longevity).
    3.  The final score is capped between 0 and 100 and assigned a human-readable level (e.g., "Trusted", "Risky").
*   **Input:** A JSON file containing vendor data with feedback counts (e.g., `vendor_data.json`).
*   **Output:** A JSON file named `output/feature_13_reputation_scores.json` with the calculated score and level for each vendor.
*   **Role in Pipeline:** **Analysis.** This feature provides a quick, at-a-glance metric for assessing vendor trustworthiness.

### **Feature 14: MITRE ATT&CK Mapping**

*   **Purpose:** To map unstructured descriptions of threat activity to the standardized, globally recognized MITRE ATT&CK framework.
*   **How it Works:**
    1.  It loads a local JSON file (`mitre_attack_data.json`) that contains a curated list of ATT&CK techniques and associated keywords (e.g., T1566 -> "spear-phishing").
    2.  It takes a block of text as input.
    3.  It iterates through every technique in its dataset and uses regex to check if any of the associated keywords are present in the input text.
    4.  It compiles a list of all matching TTPs (Tactics, Techniques, and Procedures).
*   **Input:** Raw text (in the pipeline, this would be the `full_text_content` from the scraper or other text-based features).
*   **Output:** A JSON file named `output/feature_14_mitre_attack_mappings.json` listing the TTPs that match the input text.
*   **Role in Pipeline:** **High-Level Intelligence Generation.** This feature is crucial for standardizing your findings. It translates informal chatter ("he used a phishing link") into a formal intelligence report ("T1566: Phishing").

### **Feature 15: Affiliate Analysis**

*   **Purpose:** To specifically look for signs of organized Ransomware-as-a-Service (RaaS) or other affiliate-based criminal enterprises.
*   **How it Works:**
    1.  It takes a list of marketplace posts as input.
    2.  It performs three main analyses:
        *   **BTC Reuse Analysis:** It finds all Bitcoin addresses mentioned and identifies which addresses are used by multiple different authors, suggesting a central payment system.
        *   **Author Pattern Analysis:** It scores authors based on their use of recruitment keywords (e.g., "join our team," "partner") and payment terms (e.g., "commission," "profit share").
        *   **Hierarchy Analysis:** It scans posts for words that imply a management structure (e.g., "admin," "manager," "leader").
    3.  It combines these findings to generate an overall risk level and a list of key findings that summarize the evidence for a RaaS operation.
*   **Input:** The JSON output from Feature 3 (Marketplace Scraper).
*   **Output:** A JSON report named `output/feature_15_affiliate_analysis.json` detailing the evidence for affiliate program activity.
*   **Role in Pipeline:** **High-Level Intelligence Generation.** This is a specialized analysis feature designed to answer a very specific and important intelligence question: "Is this just one person, or is it an organized criminal group?"
