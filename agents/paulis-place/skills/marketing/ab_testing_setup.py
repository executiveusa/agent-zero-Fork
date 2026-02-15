"""
A/B Testing Setup Skill for Agent Zero
Creates A/B test variants for marketing campaigns
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ABTestVariant:
    """A single A/B test variant"""
    variant_id: str
    element: str
    original: str
    variant: str
    hypothesis: str
    priority: int


class ABTestingSkill:
    """
    Skill for setting up A/B tests for marketing campaigns.
    
    Capabilities:
    - Create hero headline variants
    - Generate CTA button tests
    - Test value proposition framing
    - Prioritize testing order
    """
    
    name = "ab_testing_setup"
    description = "Create A/B test variants for marketing campaigns"
    
    def __init__(self):
        self.test_types = [
            "hero_headline",
            "cta_button",
            "problem_section",
            "value_proposition",
            "social_proof",
            "pricing_display"
        ]
    
    def create_hero_test(self, original: str, avatar: Dict[str, Any]) -> List[ABTestVariant]:
        """Create A/B test variants for hero section"""
        variants = []
        
        # Variant A: Direct benefit focus
        variants.append(ABTestVariant(
            variant_id="hero_a",
            element="hero_headline",
            original=original,
            variant=f"Transform Your {avatar.get('goal', 'Business')} in 30 Days",
            hypothesis="Direct benefit messaging resonates more with action-oriented users",
            priority=1
        ))
        
        # Variant B: Problem-solution focus
        variants.append(ABTestVariant(
            variant_id="hero_b",
            element="hero_headline",
            original=original,
            variant=f"Stop Struggling with {avatar.get('pain_point', 'Manual Work')}. Start Winning.",
            hypothesis="Problem-aware messaging attracts users who know their pain",
            priority=2
        ))
        
        # Variant C: Social proof focus
        variants.append(ABTestVariant(
            variant_id="hero_c",
            element="hero_headline",
            original=original,
            variant=f"Join 10,000+ {avatar.get('identity', 'Professionals')} Who Transformed Their Results",
            hypothesis="Social proof builds trust and reduces friction",
            priority=3
        ))
        
        return variants
    
    def create_cta_test(self, original: str, context: str) -> List[ABTestVariant]:
        """Create A/B test variants for CTA buttons"""
        variants = []
        
        variants.append(ABTestVariant(
            variant_id="cta_a",
            element="cta_button",
            original=original,
            variant="Start Free Trial",
            hypothesis="Low-commitment language reduces friction",
            priority=1
        ))
        
        variants.append(ABTestVariant(
            variant_id="cta_b",
            element="cta_button",
            original=original,
            variant="Get Instant Access",
            hypothesis="Urgency and instant gratification drive clicks",
            priority=2
        ))
        
        variants.append(ABTestVariant(
            variant_id="cta_c",
            element="cta_button",
            original=original,
            variant="See It In Action",
            hypothesis="Demonstration focus reduces perceived risk",
            priority=3
        ))
        
        return variants
    
    def prioritize_tests(self, tests: List[ABTestVariant]) -> List[ABTestVariant]:
        """Prioritize A/B tests based on expected impact"""
        return sorted(tests, key=lambda t: t.priority)
    
    def generate_test_report(self, tests: List[ABTestVariant]) -> str:
        """Generate a markdown report of all tests"""
        report = "# A/B Testing Plan\n\n"
        report += "## Test Variants\n\n"
        
        for test in tests:
            report += f"### {test.variant_id.upper()}\n"
            report += f"- **Element:** {test.element}\n"
            report += f"- **Original:** {test.original}\n"
            report += f"- **Variant:** {test.variant}\n"
            report += f"- **Hypothesis:** {test.hypothesis}\n"
            report += f"- **Priority:** {test.priority}\n\n"
        
        return report


# Skill registration
skill = ABTestingSkill()