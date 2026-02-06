import asyncio
from dataclasses import dataclass, field
from typing import List, Callable, Any

# --- IMPORT COLLECTORS ---
from collectors.tor.relay_inventory import RelayInventory
from collectors.discovery.onion_discovery import OnionCrawler
from collectors.marketplaces.market_scraper import MarketScraper
from collectors.feeds.stix_taxii_ingest import STIXIngest

# --- IMPORT PROCESSORS ---
from processors.extraction.ioc_extractor import IOCExtractor
from processors.extraction.hash_extractor import HashExtractor
from processors.extraction.ner_extractor import NERExtractor

# --- IMPORT ENRICHMENT ---
from enrichment.api_enrichment import APIEnricher
from enrichment.infrastructure_mapper import InfrastructureMapper
from enrichment.geolocation_correlator import GeoCorrelator

# --- IMPORT ANALYSIS ---
from analysis.behavioral_analysis import BehavioralAnalysis
from analysis.mitre_attack_mapping import MITREMapper
from analysis.affiliate_analysis import AffiliateAnalysis
from analysis.handle_correlation import HandleCorrelation
from analysis.reputation_analysis import ReputationAnalysis

# Config for targets
try:
    from config import settings
except ImportError:
    import config as settings

@dataclass
class PipelineStage:
    name: str
    action: Callable
    depends_on: List[str] = field(default_factory=list)
    category: str = "general"

def get_pipeline_stages() -> dict:
    """
    Returns the definition of the pipeline graph.
    """
    
    # 1. Wrappers to initialize classes with config
    def run_relay(): RelayInventory().run()
    def run_onion(): OnionCrawler(start_urls=settings.ONION_SEEDS).start()
    # For Scraper, we iterate all targets sequentially for now
    def run_market(): 
        for target in settings.MARKET_TARGETS:
            MarketScraper(target).run()
    def run_stix(): STIXIngest().run()
    
    def run_ioc(): IOCExtractor().run()
    def run_hash(): HashExtractor().run()
    def run_ner(): NERExtractor().run()
    
    def run_api_enrich(): APIEnricher().run()
    def run_infra(): InfrastructureMapper().run()
    def run_geo(): GeoCorrelator().run()
    
    def run_behavior(): BehavioralAnalysis().run()
    def run_mitre(): MITREMapper().run()
    def run_affiliate(): AffiliateAnalysis().run()
    def run_handle(): HandleCorrelation().run()
    def run_reputation(): ReputationAnalysis().run()

    # 2. THE DAG DEFINITION
    return {
        # --- COLLECTION (Independent) ---
        "relay_inventory": PipelineStage(
            name="relay_inventory",
            action=run_relay,
            category="collection"
        ),
        "onion_discovery": PipelineStage(
            name="onion_discovery",
            action=run_onion,
            category="collection"
        ),
        "market_scraper": PipelineStage(
            name="market_scraper",
            action=run_market,
            category="collection"
        ),
        "stix_ingest": PipelineStage(
            name="stix_ingest",
            action=run_stix,
            category="collection"
        ),

        # --- PROCESSING (Depends on Collection) ---
        "ioc_extraction": PipelineStage(
            name="ioc_extraction",
            action=run_ioc,
            depends_on=["onion_discovery", "market_scraper", "stix_ingest"],
            category="processing"
        ),
        "hash_extraction": PipelineStage(
            name="hash_extraction",
            action=run_hash,
            depends_on=["market_scraper"],
            category="processing"
        ),
        "ner_extraction": PipelineStage(
            name="ner_extraction",
            action=run_ner,
            depends_on=["market_scraper"],
            category="processing"
        ),

        # --- ENRICHMENT (Depends on Processing) ---
        "api_enrichment": PipelineStage(
            name="api_enrichment",
            action=run_api_enrich,
            depends_on=["ioc_extraction", "hash_extraction"],
            category="enrichment"
        ),
        "infrastructure_mapper": PipelineStage(
            name="infrastructure_mapper",
            action=run_infra,
            depends_on=["ioc_extraction"],
            category="enrichment"
        ),
        "geo_correlation": PipelineStage(
            name="geo_correlation",
            action=run_geo,
            depends_on=["ioc_extraction"],
            category="enrichment"
        ),

        # --- ANALYSIS (Depends on Collection, Processing, Enrichment) ---
        "behavioral_analysis": PipelineStage(
            name="behavioral_analysis",
            action=run_behavior,
            depends_on=["market_scraper"],
            category="analysis"
        ),
        "mitre_mapping": PipelineStage(
            name="mitre_mapping",
            action=run_mitre,
            depends_on=["market_scraper"],
            category="analysis"
        ),
        "affiliate_analysis": PipelineStage(
            name="affiliate_analysis",
            action=run_affiliate,
            depends_on=["market_scraper"],
            category="analysis"
        ),
        "handle_correlation": PipelineStage(
            name="handle_correlation",
            action=run_handle,
            depends_on=["ner_extraction"],
            category="analysis"
        ),
        # Reputation runs last because it aggregates everything
        "reputation_analysis": PipelineStage(
            name="reputation_analysis",
            action=run_reputation,
            depends_on=["behavioral_analysis", "affiliate_analysis", "handle_correlation"],
            category="analysis"
        ),
    }
