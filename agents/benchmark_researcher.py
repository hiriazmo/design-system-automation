"""
Benchmark Research Agent
=========================
Fetches LIVE data from design system documentation sites
using Firecrawl, with 24-hour caching.

This agent:
1. Fetches official documentation from design system sites
2. Extracts typography, spacing, color specifications using LLM
3. Caches results for 24 hours
4. Compares user's tokens to researched benchmarks
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Callable
import hashlib


# =============================================================================
# DESIGN SYSTEM SOURCES (Official Documentation URLs)
# =============================================================================

DESIGN_SYSTEM_SOURCES = {
    "material_design_3": {
        "name": "Material Design 3",
        "short_name": "Material 3",
        "vendor": "Google",
        "urls": {
            "typography": "https://m3.material.io/styles/typography/type-scale-tokens",
            "spacing": "https://m3.material.io/foundations/layout/understanding-layout/spacing",
            "colors": "https://m3.material.io/styles/color/the-color-system/key-colors-tones",
        },
        "best_for": ["Android apps", "Web apps", "Enterprise software"],
        "icon": "🟢",
    },
    "apple_hig": {
        "name": "Apple Human Interface Guidelines",
        "short_name": "Apple HIG",
        "vendor": "Apple",
        "urls": {
            "typography": "https://developer.apple.com/design/human-interface-guidelines/typography",
            "spacing": "https://developer.apple.com/design/human-interface-guidelines/layout",
        },
        "best_for": ["iOS apps", "macOS apps", "Premium consumer products"],
        "icon": "🍎",
    },
    "shopify_polaris": {
        "name": "Shopify Polaris",
        "short_name": "Polaris",
        "vendor": "Shopify",
        "urls": {
            "typography": "https://polaris.shopify.com/design/typography",
            "spacing": "https://polaris.shopify.com/design/spacing",
            "colors": "https://polaris.shopify.com/design/colors",
        },
        "best_for": ["E-commerce", "Admin dashboards", "Merchant tools"],
        "icon": "🛒",
    },
    "atlassian_design": {
        "name": "Atlassian Design System",
        "short_name": "Atlassian",
        "vendor": "Atlassian",
        "urls": {
            "typography": "https://atlassian.design/foundations/typography",
            "spacing": "https://atlassian.design/foundations/spacing",
            "colors": "https://atlassian.design/foundations/color",
        },
        "best_for": ["Productivity tools", "Dense interfaces", "Enterprise B2B"],
        "icon": "🔵",
    },
    "ibm_carbon": {
        "name": "IBM Carbon Design System",
        "short_name": "Carbon",
        "vendor": "IBM",
        "urls": {
            "typography": "https://carbondesignsystem.com/guidelines/typography/overview",
            "spacing": "https://carbondesignsystem.com/guidelines/spacing/overview",
            "colors": "https://carbondesignsystem.com/guidelines/color/overview",
        },
        "best_for": ["Enterprise software", "Data-heavy applications", "IBM products"],
        "icon": "🔷",
    },
    "tailwind_css": {
        "name": "Tailwind CSS",
        "short_name": "Tailwind",
        "vendor": "Tailwind Labs",
        "urls": {
            "typography": "https://tailwindcss.com/docs/font-size",
            "spacing": "https://tailwindcss.com/docs/customizing-spacing",
            "colors": "https://tailwindcss.com/docs/customizing-colors",
        },
        "best_for": ["Web applications", "Startups", "Rapid prototyping"],
        "icon": "🌊",
    },
    "ant_design": {
        "name": "Ant Design",
        "short_name": "Ant Design",
        "vendor": "Ant Group",
        "urls": {
            "typography": "https://ant.design/docs/spec/font",
            "spacing": "https://ant.design/docs/spec/layout",
            "colors": "https://ant.design/docs/spec/colors",
        },
        "best_for": ["Enterprise B2B", "Admin panels", "Chinese market"],
        "icon": "🐜",
    },
    "chakra_ui": {
        "name": "Chakra UI",
        "short_name": "Chakra",
        "vendor": "Chakra UI",
        "urls": {
            "typography": "https://chakra-ui.com/docs/styled-system/theme#typography",
            "spacing": "https://chakra-ui.com/docs/styled-system/theme#spacing",
            "colors": "https://chakra-ui.com/docs/styled-system/theme#colors",
        },
        "best_for": ["React applications", "Startups", "Accessible products"],
        "icon": "⚡",
    },
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BenchmarkData:
    """Researched benchmark data from a design system."""
    key: str
    name: str
    short_name: str
    vendor: str
    icon: str
    
    # Extracted specifications
    typography: dict = field(default_factory=dict)
    # Expected: {scale_ratio, base_size, sizes[], font_family, line_height_body}
    
    spacing: dict = field(default_factory=dict)
    # Expected: {base, scale[], grid}
    
    colors: dict = field(default_factory=dict)
    # Expected: {palette_size, uses_ramps, ramp_steps}
    
    # Metadata
    fetched_at: str = ""
    confidence: str = "low"  # high, medium, low
    source_urls: list = field(default_factory=list)
    best_for: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "name": self.name,
            "short_name": self.short_name,
            "vendor": self.vendor,
            "icon": self.icon,
            "typography": self.typography,
            "spacing": self.spacing,
            "colors": self.colors,
            "fetched_at": self.fetched_at,
            "confidence": self.confidence,
            "best_for": self.best_for,
        }


@dataclass
class BenchmarkComparison:
    """Comparison result between user's tokens and a benchmark."""
    benchmark: BenchmarkData
    similarity_score: float  # Lower = more similar
    
    # Individual comparisons
    type_ratio_diff: float
    base_size_diff: int
    spacing_grid_diff: int
    
    # Match percentages
    type_match_pct: float
    spacing_match_pct: float
    overall_match_pct: float
    
    def to_dict(self) -> dict:
        return {
            "name": self.benchmark.name,
            "short_name": self.benchmark.short_name,
            "icon": self.benchmark.icon,
            "similarity_score": round(self.similarity_score, 2),
            "overall_match_pct": round(self.overall_match_pct, 1),
            "comparison": {
                "type_ratio": {
                    "diff": round(self.type_ratio_diff, 3),
                    "match_pct": round(self.type_match_pct, 1),
                },
                "base_size": {
                    "diff": self.base_size_diff,
                },
                "spacing_grid": {
                    "diff": self.spacing_grid_diff,
                    "match_pct": round(self.spacing_match_pct, 1),
                },
            },
            "benchmark_values": {
                "type_ratio": self.benchmark.typography.get("scale_ratio"),
                "base_size": self.benchmark.typography.get("base_size"),
                "spacing_grid": self.benchmark.spacing.get("base"),
            },
            "best_for": self.benchmark.best_for,
            "confidence": self.benchmark.confidence,
        }


# =============================================================================
# CACHE MANAGER
# =============================================================================

class BenchmarkCache:
    """Manages 24-hour caching of benchmark research results."""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "..", "storage")
        self.cache_file = os.path.join(cache_dir, "benchmark_cache.json")
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
    
    def _load_cache(self) -> dict:
        """Load cache from file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_cache(self, cache: dict):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
        except Exception:
            pass
    
    def get(self, key: str) -> Optional[BenchmarkData]:
        """Get cached benchmark if valid (< 24 hours old)."""
        cache = self._load_cache()
        
        if key not in cache:
            return None
        
        entry = cache[key]
        fetched_at = datetime.fromisoformat(entry.get("fetched_at", "2000-01-01"))
        
        # Check if expired (24 hours)
        if datetime.now() - fetched_at > timedelta(hours=24):
            return None
        
        # Reconstruct BenchmarkData
        source = DESIGN_SYSTEM_SOURCES.get(key, {})
        return BenchmarkData(
            key=key,
            name=entry.get("name", source.get("name", key)),
            short_name=entry.get("short_name", source.get("short_name", key)),
            vendor=entry.get("vendor", source.get("vendor", "")),
            icon=entry.get("icon", source.get("icon", "📦")),
            typography=entry.get("typography", {}),
            spacing=entry.get("spacing", {}),
            colors=entry.get("colors", {}),
            fetched_at=entry.get("fetched_at", ""),
            confidence=entry.get("confidence", "low"),
            source_urls=entry.get("source_urls", []),
            best_for=entry.get("best_for", source.get("best_for", [])),
        )
    
    def set(self, key: str, data: BenchmarkData):
        """Cache benchmark data."""
        cache = self._load_cache()
        cache[key] = data.to_dict()
        self._save_cache(cache)
    
    def get_cache_status(self) -> dict:
        """Get status of all cached items."""
        cache = self._load_cache()
        status = {}
        
        for key in DESIGN_SYSTEM_SOURCES.keys():
            if key in cache:
                fetched_at = datetime.fromisoformat(cache[key].get("fetched_at", "2000-01-01"))
                age_hours = (datetime.now() - fetched_at).total_seconds() / 3600
                is_valid = age_hours < 24
                status[key] = {
                    "cached": True,
                    "valid": is_valid,
                    "age_hours": round(age_hours, 1),
                }
            else:
                status[key] = {"cached": False, "valid": False}
        
        return status


# =============================================================================
# FALLBACK DATA (Used when research fails)
# =============================================================================

FALLBACK_BENCHMARKS = {
    "material_design_3": {
        "typography": {"scale_ratio": 1.2, "base_size": 16, "font_family": "Roboto", "line_height_body": 1.5},
        "spacing": {"base": 8, "scale": [0, 4, 8, 12, 16, 24, 32, 48, 64], "grid": "8px"},
        "colors": {"palette_size": 13, "uses_ramps": True},
    },
    "apple_hig": {
        "typography": {"scale_ratio": 1.19, "base_size": 17, "font_family": "SF Pro", "line_height_body": 1.47},
        "spacing": {"base": 4, "scale": [0, 4, 8, 12, 16, 20, 24, 32, 40], "grid": "4px"},
        "colors": {"palette_size": 9, "uses_ramps": True},
    },
    "shopify_polaris": {
        "typography": {"scale_ratio": 1.25, "base_size": 16, "font_family": "Inter", "line_height_body": 1.5},
        "spacing": {"base": 4, "scale": [0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64], "grid": "4px"},
        "colors": {"palette_size": 11, "uses_ramps": True},
    },
    "atlassian_design": {
        "typography": {"scale_ratio": 1.14, "base_size": 14, "font_family": "Inter", "line_height_body": 1.43},
        "spacing": {"base": 8, "scale": [0, 4, 8, 12, 16, 24, 32, 40, 48], "grid": "8px"},
        "colors": {"palette_size": 15, "uses_ramps": True},
    },
    "ibm_carbon": {
        "typography": {"scale_ratio": 1.25, "base_size": 14, "font_family": "IBM Plex Sans", "line_height_body": 1.5},
        "spacing": {"base": 8, "scale": [0, 2, 4, 8, 12, 16, 24, 32, 40, 48], "grid": "8px"},
        "colors": {"palette_size": 12, "uses_ramps": True},
    },
    "tailwind_css": {
        "typography": {"scale_ratio": 1.25, "base_size": 16, "font_family": "system-ui", "line_height_body": 1.5},
        "spacing": {"base": 4, "scale": [0, 1, 2, 4, 6, 8, 10, 12, 14, 16, 20, 24, 28, 32], "grid": "4px"},
        "colors": {"palette_size": 22, "uses_ramps": True},
    },
    "ant_design": {
        "typography": {"scale_ratio": 1.14, "base_size": 14, "font_family": "system-ui", "line_height_body": 1.57},
        "spacing": {"base": 8, "scale": [0, 4, 8, 12, 16, 20, 24, 32, 40, 48], "grid": "8px"},
        "colors": {"palette_size": 13, "uses_ramps": True},
    },
    "chakra_ui": {
        "typography": {"scale_ratio": 1.25, "base_size": 16, "font_family": "system-ui", "line_height_body": 1.5},
        "spacing": {"base": 4, "scale": [0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 56, 64], "grid": "4px"},
        "colors": {"palette_size": 15, "uses_ramps": True},
    },
}


# =============================================================================
# BENCHMARK RESEARCHER
# =============================================================================

class BenchmarkResearcher:
    """
    Research agent that fetches live design system specifications.
    
    Uses Firecrawl to fetch documentation and LLM to extract specs.
    Results are cached for 24 hours.
    """
    
    def __init__(self, firecrawl_client=None, hf_client=None):
        """
        Initialize researcher.
        
        Args:
            firecrawl_client: Firecrawl API client for fetching docs
            hf_client: HuggingFace client for LLM extraction
        """
        self.firecrawl = firecrawl_client
        self.hf_client = hf_client
        self.cache = BenchmarkCache()
    
    async def research_benchmark(
        self,
        system_key: str,
        log_callback: Callable = None,
        force_refresh: bool = False,
    ) -> BenchmarkData:
        """
        Research a specific design system.
        
        Args:
            system_key: Key from DESIGN_SYSTEM_SOURCES
            log_callback: Function to log progress
            force_refresh: Bypass cache and fetch fresh
            
        Returns:
            BenchmarkData with extracted specifications
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)
        
        if system_key not in DESIGN_SYSTEM_SOURCES:
            raise ValueError(f"Unknown design system: {system_key}")
        
        source = DESIGN_SYSTEM_SOURCES[system_key]
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached = self.cache.get(system_key)
            if cached:
                log(f"   ├─ {source['icon']} {source['short_name']}: Using cached data ✅")
                return cached
        
        log(f"   ├─ {source['icon']} {source['short_name']}: Fetching documentation...")
        
        # Try to fetch and extract
        raw_content = ""
        confidence = "low"
        
        if self.firecrawl:
            try:
                # Fetch typography docs
                typo_url = source["urls"].get("typography")
                if typo_url:
                    log(f"   │  ├─ Fetching {typo_url[:50]}...")
                    typo_content = await self._fetch_url(typo_url)
                    if typo_content:
                        raw_content += f"\n\n=== TYPOGRAPHY ===\n{typo_content[:4000]}"
                        confidence = "medium"
                
                # Fetch spacing docs
                spacing_url = source["urls"].get("spacing")
                if spacing_url:
                    log(f"   │  ├─ Fetching spacing docs...")
                    spacing_content = await self._fetch_url(spacing_url)
                    if spacing_content:
                        raw_content += f"\n\n=== SPACING ===\n{spacing_content[:3000]}"
                        if confidence == "medium":
                            confidence = "high"
            
            except Exception as e:
                log(f"   │  ├─ ⚠️ Fetch error: {str(e)[:50]}")
        
        # Extract specs with LLM (or use fallback)
        if raw_content and self.hf_client:
            log(f"   │  ├─ Extracting specifications...")
            extracted = await self._extract_specs_with_llm(source["name"], raw_content)
        else:
            log(f"   │  ├─ Using fallback data (fetch unavailable)")
            extracted = FALLBACK_BENCHMARKS.get(system_key, {})
            confidence = "fallback"
        
        # Build result
        result = BenchmarkData(
            key=system_key,
            name=source["name"],
            short_name=source["short_name"],
            vendor=source["vendor"],
            icon=source["icon"],
            typography=extracted.get("typography", FALLBACK_BENCHMARKS.get(system_key, {}).get("typography", {})),
            spacing=extracted.get("spacing", FALLBACK_BENCHMARKS.get(system_key, {}).get("spacing", {})),
            colors=extracted.get("colors", FALLBACK_BENCHMARKS.get(system_key, {}).get("colors", {})),
            fetched_at=datetime.now().isoformat(),
            confidence=confidence,
            source_urls=list(source["urls"].values()),
            best_for=source["best_for"],
        )
        
        # Cache result
        self.cache.set(system_key, result)
        
        ratio = result.typography.get("scale_ratio", "?")
        base = result.typography.get("base_size", "?")
        grid = result.spacing.get("base", "?")
        log(f"   │  └─ ✅ ratio={ratio}, base={base}px, grid={grid}px [{confidence}]")
        
        return result
    
    async def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL content using Firecrawl."""
        if not self.firecrawl:
            return None
        
        try:
            # Firecrawl scrape
            result = self.firecrawl.scrape_url(
                url,
                params={"formats": ["markdown"]}
            )
            
            if result and result.get("markdown"):
                return result["markdown"]
            elif result and result.get("content"):
                return result["content"]
            
        except Exception as e:
            pass
        
        return None
    
    async def _extract_specs_with_llm(self, system_name: str, raw_content: str) -> dict:
        """Extract structured specs from documentation using LLM."""
        if not self.hf_client:
            return {}
        
        prompt = f"""Extract the design system specifications from this documentation.

DESIGN SYSTEM: {system_name}

DOCUMENTATION:
{raw_content[:6000]}

Return ONLY a JSON object with these exact fields (use null if not found):
{{
  "typography": {{
    "scale_ratio": <number like 1.2 or 1.25>,
    "base_size": <number in px>,
    "font_family": "<font name>",
    "sizes": [<list of sizes in px>],
    "line_height_body": <number like 1.5>
  }},
  "spacing": {{
    "base": <base unit in px like 4 or 8>,
    "scale": [<spacing values>],
    "grid": "<description>"
  }},
  "colors": {{
    "palette_size": <number>,
    "uses_ramps": <true/false>
  }}
}}

Return ONLY valid JSON, no explanation."""

        try:
            response = await self.hf_client.complete_async(
                agent_name="benchmark_extractor",
                system_prompt="You are a design system specification extractor. Extract only the factual specifications.",
                user_message=prompt,
                max_tokens=600,
                json_mode=True,
            )
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        
        except Exception as e:
            pass
        
        return {}
    
    async def research_selected_benchmarks(
        self,
        selected_keys: list[str],
        log_callback: Callable = None,
    ) -> list[BenchmarkData]:
        """
        Research multiple selected design systems.
        
        Args:
            selected_keys: List of system keys to research
            log_callback: Function to log progress
            
        Returns:
            List of BenchmarkData
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)
        
        log("")
        log("═" * 60)
        log("🔬 LAYER 2: BENCHMARK RESEARCH (Firecrawl + Cache)")
        log("═" * 60)
        log("")
        log(f"   Selected systems: {', '.join(selected_keys)}")
        log("")
        
        results = []
        
        for key in selected_keys:
            if key in DESIGN_SYSTEM_SOURCES:
                try:
                    result = await self.research_benchmark(key, log_callback)
                    results.append(result)
                except Exception as e:
                    log(f"   ├─ ⚠️ Error researching {key}: {e}")
                    # Use fallback
                    source = DESIGN_SYSTEM_SOURCES[key]
                    fallback = FALLBACK_BENCHMARKS.get(key, {})
                    results.append(BenchmarkData(
                        key=key,
                        name=source["name"],
                        short_name=source["short_name"],
                        vendor=source["vendor"],
                        icon=source["icon"],
                        typography=fallback.get("typography", {}),
                        spacing=fallback.get("spacing", {}),
                        colors=fallback.get("colors", {}),
                        fetched_at=datetime.now().isoformat(),
                        confidence="fallback",
                        best_for=source["best_for"],
                    ))
        
        log("")
        log(f"   ✅ Researched {len(results)}/{len(selected_keys)} design systems")
        
        return results
    
    def compare_to_benchmarks(
        self,
        your_ratio: float,
        your_base_size: int,
        your_spacing_grid: int,
        benchmarks: list[BenchmarkData],
        log_callback: Callable = None,
    ) -> list[BenchmarkComparison]:
        """
        Compare user's tokens to researched benchmarks.
        
        Args:
            your_ratio: Detected type scale ratio
            your_base_size: Detected base font size
            your_spacing_grid: Detected spacing grid base
            benchmarks: List of researched BenchmarkData
            log_callback: Function to log progress
            
        Returns:
            List of BenchmarkComparison sorted by similarity
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)
        
        log("")
        log("   📊 BENCHMARK COMPARISON")
        log("   " + "─" * 40)
        log(f"   Your values: ratio={your_ratio:.2f}, base={your_base_size}px, grid={your_spacing_grid}px")
        log("")
        
        comparisons = []
        
        for b in benchmarks:
            b_ratio = b.typography.get("scale_ratio", 1.25)
            b_base = b.typography.get("base_size", 16)
            b_grid = b.spacing.get("base", 8)
            
            # Calculate differences
            ratio_diff = abs(your_ratio - b_ratio)
            base_diff = abs(your_base_size - b_base)
            grid_diff = abs(your_spacing_grid - b_grid)
            
            # Calculate match percentages
            type_match = max(0, 100 - (ratio_diff * 100))  # 0.1 diff = 90% match
            spacing_match = max(0, 100 - (grid_diff * 10))  # 4px diff = 60% match
            
            # Weighted similarity score (lower = more similar)
            similarity = (ratio_diff * 10) + (base_diff * 0.5) + (grid_diff * 0.3)
            
            # Overall match percentage
            overall_match = (type_match * 0.5) + (spacing_match * 0.3) + (100 - base_diff * 5) * 0.2
            overall_match = max(0, min(100, overall_match))
            
            comparisons.append(BenchmarkComparison(
                benchmark=b,
                similarity_score=similarity,
                type_ratio_diff=ratio_diff,
                base_size_diff=base_diff,
                spacing_grid_diff=grid_diff,
                type_match_pct=type_match,
                spacing_match_pct=spacing_match,
                overall_match_pct=overall_match,
            ))
        
        # Sort by similarity (lower = better)
        comparisons.sort(key=lambda x: x.similarity_score)
        
        # Log results
        medals = ["🥇", "🥈", "🥉"]
        for i, c in enumerate(comparisons[:5]):
            medal = medals[i] if i < 3 else "  "
            b = c.benchmark
            log(f"   {medal} {b.icon} {b.short_name}: {c.overall_match_pct:.0f}% match (score: {c.similarity_score:.2f})")
            log(f"      └─ ratio={b.typography.get('scale_ratio')}, base={b.typography.get('base_size')}px, grid={b.spacing.get('base')}px")
        
        return comparisons


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_available_benchmarks() -> list[dict]:
    """Get list of available design systems for UI dropdown."""
    return [
        {
            "key": key,
            "name": source["name"],
            "short_name": source["short_name"],
            "icon": source["icon"],
            "vendor": source["vendor"],
            "best_for": source["best_for"],
        }
        for key, source in DESIGN_SYSTEM_SOURCES.items()
    ]


def get_benchmark_choices() -> list[tuple[str, str]]:
    """Get choices for Gradio dropdown."""
    return [
        (f"{source['icon']} {source['short_name']} ({source['vendor']})", key)
        for key, source in DESIGN_SYSTEM_SOURCES.items()
    ]
