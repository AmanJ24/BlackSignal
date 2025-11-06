"""
Mock Data Generator for Dark Web OSINT Tool
Generates realistic fake data for testing and development
"""

import random
from datetime import datetime, timedelta
import hashlib

class MockDataGenerator:
    """Generate realistic mock data for all OSINT features"""

    # Realistic onion domains
    ONION_DOMAINS = [
        'darkfailllnkf4vf.onion',
        'hss3uro2hsxfogfq.onion',
        '3g2upl4pq6kufc4m.onion',
        'thehiddenwiki.onion',
        'tormarket45ads2.onion',
        'alphabay23dfg56.onion',
        'dreammarket67sd.onion',
        'wallstreet42mkt.onion',
        'empiremarketdf3.onion',
        'whitehouse89mkt.onion',
        'darkbay45market.onion',
        'silkroad3dpfsd.onion',
        'agora98marketh.onion',
        'nucleus23market.onion',
        'evolution45dfg.onion',
    ]

    # Realistic vendor names
    VENDOR_NAMES = [
        'CryptoKing',
        'ShadowDealer',
        'DarkVendor',
        'SecureSupply',
        'AnonymousTrader',
        'PhantomSeller',
        'NightMarket',
        'TorTrader',
        'HiddenGoods',
        'CipherMerchant',
        'VoidVendor',
        'GhostSupplier',
        'StealthSeller',
        'UndergroundSource',
        'BlackMarketPro',
    ]

    # Product categories
    PRODUCTS = [
        'Database Dump - Fortune 500 Company',
        'Stolen Credit Cards (Bulk)',
        'RDP Access - Windows Server 2019',
        'Malware-as-a-Service Subscription',
        'DDoS Service (Per Hour)',
        'Phishing Kit - Banking Templates',
        'Ransomware Source Code',
        'Cryptocurrency Tumbling Service',
        'Identity Documents (Fake)',
        'Corporate Email Access',
        'SSH Access - Linux Servers',
        'Botnet Rental (10k bots)',
        'Zero-Day Exploit CVE-2024',
        'Stolen Credentials Database',
        'VPN Accounts (Hacked)',
    ]

    # Threat actor handles
    HANDLES = [
        'LockBit_Affiliate_92',
        'Conti_Recruiter',
        'REvil_Member_45',
        'DarkSide_Operator',
        'BlackCat_Admin',
        'Hive_Affiliate',
        'ALPHV_Member',
        'Maze_Operator_77',
        'NetWalker_Affiliate',
        'Ryuk_Operator',
    ]

    @staticmethod
    def generate_onion_domains(count=50):
        """Generate list of onion domains"""
        domains = MockDataGenerator.ONION_DOMAINS.copy()

        # Generate additional random domains
        for i in range(count - len(domains)):
            random_string = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz234567', k=16))
            domains.append(f"{random_string}.onion")

        return {
            'domains': domains[:count],
            'metadata': {
                'total': count,
                'discovery_date': datetime.now().isoformat(),
                'v2_count': int(count * 0.6),
                'v3_count': int(count * 0.4),
            }
        }

    @staticmethod
    def generate_marketplace_data(count=20):
        """Generate marketplace listings"""
        listings = []

        for i in range(count):
            listing = {
                'title': random.choice(MockDataGenerator.PRODUCTS),
                'vendor': random.choice(MockDataGenerator.VENDOR_NAMES),
                'price_btc': round(random.uniform(0.001, 5.0), 4),
                'price_usd': round(random.uniform(50, 25000), 2),
                'btc_address': MockDataGenerator.generate_bitcoin_address(),
                'rating': round(random.uniform(3.5, 5.0), 1),
                'sales': random.randint(10, 500),
                'description_snippet': 'High quality product. Fast delivery. Escrow accepted.',
                'category': random.choice(['Fraud', 'Malware', 'Access', 'Services', 'Data']),
                'posted_date': (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
            }
            listings.append(listing)

        return {
            'scraped_data': listings,
            'metadata': {
                'total_listings': count,
                'unique_vendors': len(set(l['vendor'] for l in listings)),
                'scrape_timestamp': datetime.now().isoformat(),
            }
        }

    @staticmethod
    def generate_iocs():
        """Generate indicators of compromise"""
        iocs = {
            'ips': [
                f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
                for _ in range(25)
            ],
            'domains': [
                f"{random.choice(['malicious', 'phishing', 'c2', 'evil', 'bad'])}{random.randint(1, 999)}.{random.choice(['com', 'net', 'org', 'ru', 'cn'])}"
                for _ in range(15)
            ],
            'hashes': {
                'md5': [hashlib.md5(str(random.random()).encode()).hexdigest() for _ in range(10)],
                'sha256': [hashlib.sha256(str(random.random()).encode()).hexdigest() for _ in range(10)],
            },
            'btc_addresses': [MockDataGenerator.generate_bitcoin_address() for _ in range(8)],
            'emails': [
                f"{random.choice(['admin', 'support', 'contact', 'sales'])}@{random.choice(['darkweb', 'anonymous', 'secure'])}{random.randint(1, 99)}.{random.choice(['com', 'net', 'org'])}"
                for _ in range(12)
            ],
        }

        total_iocs = len(iocs['ips']) + len(iocs['domains']) + len(iocs['hashes']['md5']) + len(iocs['hashes']['sha256']) + len(iocs['btc_addresses']) + len(iocs['emails'])

        return {
            'iocs': iocs,
            'total_iocs': total_iocs,
            'extraction_timestamp': datetime.now().isoformat(),
            'statistics': {
                'ip_count': len(iocs['ips']),
                'domain_count': len(iocs['domains']),
                'hash_count': len(iocs['hashes']['md5']) + len(iocs['hashes']['sha256']),
                'btc_count': len(iocs['btc_addresses']),
                'email_count': len(iocs['emails']),
            }
        }

    @staticmethod
    def generate_enriched_data(count=15):
        """Generate API-enriched IOC data"""
        enriched = []

        for i in range(count):
            ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

            entry = {
                'ip': ip,
                'geolocation': {
                    'country': random.choice(['Russia', 'China', 'United States', 'Netherlands', 'Germany', 'Ukraine']),
                    'city': random.choice(['Moscow', 'Beijing', 'New York', 'Amsterdam', 'Berlin', 'Kyiv']),
                    'latitude': round(random.uniform(-90, 90), 4),
                    'longitude': round(random.uniform(-180, 180), 4),
                },
                'network': {
                    'asn': random.randint(1000, 65000),
                    'isp': random.choice(['Bulletproof Hosting Ltd', 'Anonymous VPS', 'Offshore Servers', 'Privacy Host']),
                    'organization': random.choice(['Privacy Network', 'Secure Hosting', 'Anonymous Services']),
                },
                'threat_intel': {
                    'reputation_score': random.randint(0, 100),
                    'is_malicious': random.choice([True, False]),
                    'categories': random.sample(['C2', 'Malware', 'Phishing', 'Spam', 'Fraud'], k=random.randint(1, 3)),
                    'total_reports': random.randint(0, 150),
                },
                'ports': random.sample([22, 80, 443, 3389, 8080, 1337, 4444], k=random.randint(2, 4)),
            }
            enriched.append(entry)

        return {
            'enriched_data': enriched,
            'metadata': {
                'total_enriched': count,
                'malicious_count': sum(1 for e in enriched if e['threat_intel']['is_malicious']),
                'enrichment_timestamp': datetime.now().isoformat(),
            }
        }

    @staticmethod
    def generate_threat_analysis():
        """Generate threat analysis results"""
        return {
            'actors': [
                {
                    'handle': handle,
                    'reputation': round(random.uniform(1, 10), 1),
                    'threat_level': random.choice(['Low', 'Medium', 'High', 'Critical']),
                    'activity_count': random.randint(5, 200),
                    'first_seen': (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                    'last_seen': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                }
                for handle in random.sample(MockDataGenerator.HANDLES, k=8)
            ],
            'mitre_tactics': [
                {'tactic': 'Initial Access', 'techniques': ['T1566.001', 'T1190'], 'count': random.randint(5, 20)},
                {'tactic': 'Execution', 'techniques': ['T1059.001', 'T1053'], 'count': random.randint(3, 15)},
                {'tactic': 'Persistence', 'techniques': ['T1543.003', 'T1136'], 'count': random.randint(2, 10)},
                {'tactic': 'Privilege Escalation', 'techniques': ['T1068', 'T1055'], 'count': random.randint(1, 8)},
                {'tactic': 'Defense Evasion', 'techniques': ['T1070', 'T1027'], 'count': random.randint(4, 12)},
                {'tactic': 'Impact', 'techniques': ['T1486', 'T1490'], 'count': random.randint(10, 30)},
            ],
            'affiliate_networks': [
                {
                    'group': random.choice(['LockBit', 'BlackCat', 'Hive', 'Conti']),
                    'affiliates': random.randint(5, 25),
                    'revenue_btc': round(random.uniform(10, 500), 2),
                    'recruitment_active': random.choice([True, False]),
                }
                for _ in range(4)
            ],
        }

    @staticmethod
    def generate_bitcoin_address():
        """Generate realistic-looking Bitcoin address"""
        chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        return '1' + ''.join(random.choices(chars, k=33))

    @staticmethod
    def generate_logs(count=50):
        """Generate realistic log entries"""
        log_templates = [
            ('Connecting to Tor network', 'info'),
            ('Successfully connected to {count} relays', 'success'),
            ('Discovered {count} new .onion domains', 'success'),
            ('Crawling {domain}', 'info'),
            ('Extracting IOCs from marketplace data', 'info'),
            ('Found {count} IP addresses', 'success'),
            ('Enriching {count} indicators with threat intelligence', 'info'),
            ('API rate limit approaching, throttling requests', 'warning'),
            ('Geolocation data retrieved for {ip}', 'info'),
            ('Identified threat actor: {handle}', 'success'),
            ('Mapping to MITRE ATT&CK: {tactic}', 'info'),
            ('Behavioral analysis complete', 'success'),
            ('Reputation score calculated: {score}/10', 'info'),
            ('Affiliate network detected: {group}', 'success'),
            ('Pipeline stage completed', 'success'),
        ]

        logs = []
        base_time = datetime.now() - timedelta(minutes=count)

        for i in range(count):
            template, level = random.choice(log_templates)

            message = template.format(
                count=random.randint(5, 50),
                domain=random.choice(MockDataGenerator.ONION_DOMAINS),
                ip=f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
                handle=random.choice(MockDataGenerator.HANDLES),
                tactic=random.choice(['Initial Access', 'Execution', 'Persistence', 'Impact']),
                score=random.randint(1, 10),
                group=random.choice(['LockBit', 'BlackCat', 'Hive', 'Conti']),
            )

            logs.append({
                'message': message,
                'level': level,
                'timestamp': (base_time + timedelta(seconds=i * 2)).isoformat(),
            })

        return logs


def populate_mock_data():
    """Generate complete mock dataset"""
    generator = MockDataGenerator()

    return {
        'onion_domains': generator.generate_onion_domains(50),
        'marketplace_data': generator.generate_marketplace_data(20),
        'iocs': generator.generate_iocs(),
        'enriched_data': generator.generate_enriched_data(15),
        'threat_analysis': generator.generate_threat_analysis(),
        'logs': generator.generate_logs(50),
    }
