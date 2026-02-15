"""
Paid Ads Skill for Agent Zero
Creates and manages paid advertising campaigns
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class AdPlatform(Enum):
    META = "meta"
    GOOGLE = "google"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"


class AdFormat(Enum):
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    STORY = "story"


@dataclass
class AdCreative:
    """A single ad creative"""
    creative_id: str
    platform: AdPlatform
    format: AdFormat
    headline: str
    primary_text: str
    cta: str
    targeting: Dict[str, Any]
    budget: float


@dataclass
class AdCampaign:
    """A complete ad campaign"""
    campaign_id: str
    name: str
    objective: str
    creatives: List[AdCreative]
    budget: float
    duration_days: int


class PaidAdsSkill:
    """
    Skill for creating and managing paid ad campaigns.
    
    Capabilities:
    - Create Meta (Facebook/Instagram) campaigns
    - Generate ad creatives
    - Define targeting strategies
    - Set up campaign structure
    """
    
    name = "paid_ads"
    description = "Create and manage paid advertising campaigns"
    
    def __init__(self):
        self.platforms = list(AdPlatform)
        self.formats = list(AdFormat)
    
    def create_meta_campaign(self, offer: Dict[str, Any], avatar: Dict[str, Any]) -> AdCampaign:
        """Create a Meta ads campaign"""
        creatives = []
        
        # Creative 1: Problem-aware angle
        creatives.append(AdCreative(
            creative_id="meta_1",
            platform=AdPlatform.META,
            format=AdFormat.VIDEO,
            headline=f"Stop Struggling with {avatar.get('pain_point', 'This Problem')}",
            primary_text=f"""
Are you tired of {avatar.get('frustration', 'dealing with this issue')}?

{avatar.get('identity', 'People like you')} are discovering a better way.

{offer.get('benefit', 'Transform your results')} with {offer.get('name', 'our solution')}.

Click below to learn more.
""",
            cta="Learn More",
            targeting={
                "interests": avatar.get("interests", ["AI", "Technology", "Business"]),
                "behaviors": ["Engaged Shoppers", "Small Business Owners"],
                "age_range": avatar.get("age_range", "25-55"),
                "locations": avatar.get("locations", ["US"])
            },
            budget=20.0
        ))
        
        # Creative 2: Solution-aware angle
        creatives.append(AdCreative(
            creative_id="meta_2",
            platform=AdPlatform.META,
            format=AdFormat.CAROUSEL,
            headline=f"The {avatar.get('identity', 'Professional')}\'s Guide to {avatar.get('goal', 'Success')}",
            primary_text=f"""
Discover how {avatar.get('identity', 'professionals')} are:

✅ {offer.get('benefit_1', 'Saving time')}
✅ {offer.get('benefit_2', 'Getting better results')}
✅ {offer.get('benefit_3', 'Growing faster')}

See how it works →
""",
            cta="See How",
            targeting={
                "interests": avatar.get("interests", ["AI", "Technology"]),
                "lookalike": ["Email List", "Website Visitors"],
                "age_range": avatar.get("age_range", "25-55")
            },
            budget=20.0
        ))
        
        # Creative 3: Transformation angle
        creatives.append(AdCreative(
            creative_id="meta_3",
            platform=AdPlatform.META,
            format=AdFormat.VIDEO,
            headline=f"From {avatar.get('before_state', 'Struggling')} to {avatar.get('after_state', 'Thriving')} in {offer.get('timeframe', '30 Days')}",
            primary_text=f"""
Watch how {avatar.get('case_study_name', 'Sarah')} transformed her results:

Before: {avatar.get('before_state', 'Struggling')}
After: {avatar.get('after_state', 'Thriving')}

The secret? {offer.get('name', 'Our solution')}

Your transformation starts here.
""",
            cta="Get Started",
            targeting={
                "retargeting": ["Website Visitors 7 Days", "Video Viewers"],
                "age_range": avatar.get("age_range", "25-55")
            },
            budget=15.0
        ))
        
        return AdCampaign(
            campaign_id=f"campaign_{offer.get('name', 'offer').lower().replace(' ', '_')}",
            name=f"{offer.get('name', 'Offer')} Campaign",
            objective="CONVERSIONS",
            creatives=creatives,
            budget=50.0,
            duration_days=7
        )
    
    def create_targeting_strategy(self, avatar: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive targeting strategy"""
        return {
            "primary_audiences": [
                {
                    "name": "Interest-Based",
                    "targeting": {
                        "interests": avatar.get("interests", []),
                        "behaviors": ["Engaged Shoppers"],
                        "demographics": {
                            "age": avatar.get("age_range", "25-55"),
                            "locations": avatar.get("locations", ["US"])
                        }
                    }
                },
                {
                    "name": "Lookalike",
                    "targeting": {
                        "lookalike_sources": ["Email List", "Purchase History"],
                        "lookalike_size": "1-5%"
                    }
                }
            ],
            "secondary_audiences": [
                {
                    "name": "Retargeting",
                    "targeting": {
                        "website_visitors": "7-30 days",
                        "video_viewers": "50%+ watched",
                        "engaged_users": "Any interaction"
                    }
                }
            ],
            "excluded_audiences": [
                "Existing Customers",
                "Recent Purchasers (30 days)"
            ]
        }
    
    def generate_campaign_report(self, campaign: AdCampaign) -> str:
        """Generate a markdown report of the campaign"""
        report = f"# Ad Campaign: {campaign.name}\n\n"
        report += f"- **Campaign ID:** {campaign.campaign_id}\n"
        report += f"- **Objective:** {campaign.objective}\n"
        report += f"- **Budget:** ${campaign.budget}/day\n"
        report += f"- **Duration:** {campaign.duration_days} days\n\n"
        
        report += "## Ad Creatives\n\n"
        
        for creative in campaign.creatives:
            report += f"### {creative.creative_id.upper()}\n\n"
            report += f"- **Platform:** {creative.platform.value}\n"
            report += f"- **Format:** {creative.format.value}\n"
            report += f"- **Headline:** {creative.headline}\n"
            report += f"- **CTA:** {creative.cta}\n"
            report += f"- **Budget:** ${creative.budget}/day\n\n"
            report += f"**Primary Text:**\n```\n{creative.primary_text}\n```\n\n"
            report += f"**Targeting:**\n```json\n{creative.targeting}\n```\n\n"
            report += "---\n\n"
        
        return report


# Skill registration
skill = PaidAdsSkill()