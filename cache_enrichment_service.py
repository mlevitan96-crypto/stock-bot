#!/usr/bin/env python3
"""
Cache Enrichment Service
=========================
Automatically enriches UW cache with computed signals (iv_term_skew, smile_slope, insider)
and persists them back to the cache so they're always available.

Runs periodically to ensure all signals are computed and stored.
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

DATA_DIR = Path("data")
STATE_DIR = Path("state")
LOGS_DIR = Path("logs")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [CACHE-ENRICH] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "cache_enrichment.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CacheEnrichmentService:
    """Service that enriches cache with computed signals."""
    
    def __init__(self):
        self.cache_file = DATA_DIR / "uw_flow_cache.json"
        self.enrichment_interval = 60  # Run every 60 seconds
        
    def enrich_cache(self) -> Dict[str, Any]:
        """Enrich the entire cache with computed signals."""
        if not self.cache_file.exists():
            logger.warning("Cache file not found")
            return {}
        
        try:
            # Load cache
            with self.cache_file.open("r") as f:
                cache_data = json.load(f)
            
            # Import enrichment
            import uw_enrichment_v2 as uw_enrich
            enricher = uw_enrich.UWEnricher()
            
            # Features to compute
            features = [
                "iv_term_skew", 
                "smile_slope", 
                "put_call_skew",
                "toxicity", 
                "event_alignment", 
                "freshness"
            ]
            
            enriched_count = 0
            updated_count = 0
            
            # Enrich each symbol
            for symbol, data in cache_data.items():
                if symbol.startswith("_"):
                    continue  # Skip metadata
                
                if not isinstance(data, dict):
                    continue
                
                try:
                    # Compute enrichment
                    enriched = enricher.enrich_symbol(symbol, data, features)
                    
                    # Update cache with computed signals
                    needs_update = False
                    
                    # Always compute and set iv_term_skew and smile_slope if missing
                    if "iv_term_skew" not in cache_data[symbol] or cache_data[symbol].get("iv_term_skew") is None:
                        if "iv_term_skew" in enriched and enriched["iv_term_skew"] is not None:
                            cache_data[symbol]["iv_term_skew"] = enriched["iv_term_skew"]
                            needs_update = True
                        else:
                            # Compute directly if not in enriched
                            computed_skew = enricher.compute_iv_term_skew(symbol, data)
                            cache_data[symbol]["iv_term_skew"] = computed_skew
                            needs_update = True
                    
                    if "smile_slope" not in cache_data[symbol] or cache_data[symbol].get("smile_slope") is None:
                        if "smile_slope" in enriched and enriched["smile_slope"] is not None:
                            cache_data[symbol]["smile_slope"] = enriched["smile_slope"]
                            needs_update = True
                        else:
                            # Compute directly if not in enriched
                            computed_slope = enricher.compute_smile_slope(symbol, data)
                            cache_data[symbol]["smile_slope"] = computed_slope
                            needs_update = True
                    
                    # Ensure insider exists (even if empty/default)
                    if "insider" not in cache_data[symbol] or not cache_data[symbol]["insider"]:
                        cache_data[symbol]["insider"] = {
                            "sentiment": "NEUTRAL",
                            "net_buys": 0,
                            "net_sells": 0,
                            "total_usd": 0.0,
                            "conviction_modifier": 0.0
                        }
                        needs_update = True
                    
                    if needs_update:
                        updated_count += 1
                    
                    enriched_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error enriching {symbol}: {e}")
                    continue
            
            # Write enriched cache back (always write to ensure signals are persisted)
            # Even if no updates, we should ensure all signals are present
            if updated_count > 0 or enriched_count > 0:
                # Atomic write
                temp_file = self.cache_file.with_suffix(".json.tmp")
                with temp_file.open("w") as f:
                    json.dump(cache_data, f, indent=2)
                temp_file.replace(self.cache_file)
                logger.info(f"Enriched {enriched_count} symbols, updated {updated_count} with computed signals")
            else:
                # No updates needed, but log that we checked
                logger.debug(f"Checked {enriched_count} symbols, all signals already present")
            
            return cache_data
            
        except Exception as e:
            logger.error(f"Error enriching cache: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def run_once(self):
        """Run enrichment once."""
        logger.info("Starting cache enrichment cycle")
        enriched = self.enrich_cache()
        logger.info(f"Cache enrichment complete: {len([k for k in enriched.keys() if not k.startswith('_')])} symbols")
        return enriched
    
    def run_continuous(self):
        """Run enrichment continuously."""
        logger.info("Cache enrichment service starting (continuous mode)")
        while True:
            try:
                self.run_once()
                time.sleep(self.enrichment_interval)
            except KeyboardInterrupt:
                logger.info("Cache enrichment service stopped")
                break
            except Exception as e:
                logger.error(f"Error in enrichment loop: {e}")
                time.sleep(self.enrichment_interval)

def main():
    """Main entry point."""
    import sys
    service = CacheEnrichmentService()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        service.run_continuous()
    else:
        service.run_once()

if __name__ == "__main__":
    main()
