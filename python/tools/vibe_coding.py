"""
Vibe Coding Framework

Enables agents to write code based on creative vibes, feelings, and intuitive concepts
rather than formal specifications. Translates emotional/creative descriptions into executable code.
"""

import json
import re
from typing import Optional, Dict, Any, List
from datetime import datetime


class VibeCodeGenerator:
    """Generate code from creative vibes and intuitive descriptions"""

    def __init__(self):
        self.vibe_categories = {
            "minimalist": self._vibe_minimalist,
            "vibrant": self._vibe_vibrant,
            "dark": self._vibe_dark,
            "playful": self._vibe_playful,
            "professional": self._vibe_professional,
            "futuristic": self._vibe_futuristic,
            "cozy": self._vibe_cozy,
            "sleek": self._vibe_sleek,
        }

    def generate_from_vibe(
        self,
        vibe_description: str,
        component_type: str = "react",
        framework: str = "react",
    ) -> Dict[str, Any]:
        """Generate code from a vibe description"""
        try:
            # Analyze vibe
            vibe_analysis = self._analyze_vibe(vibe_description)

            # Generate component
            component = self._generate_component(
                vibe_analysis=vibe_analysis,
                component_type=component_type,
                framework=framework,
            )

            # Generate styles
            styles = self._generate_styles(vibe_analysis)

            # Generate animations
            animations = self._generate_animations(vibe_analysis)

            return {
                "success": True,
                "vibe": vibe_description,
                "analysis": vibe_analysis,
                "component": component,
                "styles": styles,
                "animations": animations,
                "suggestions": self._get_suggestions(vibe_analysis),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def _analyze_vibe(self, description: str) -> Dict[str, Any]:
        """Analyze vibe description to extract key characteristics"""
        vibe_lower = description.lower()

        # Detect vibe category
        detected_vibe = "modern"  # default
        for vibe_name in self.vibe_categories:
            if vibe_name in vibe_lower:
                detected_vibe = vibe_name
                break

        # Detect colors
        colors = self._extract_colors(description)

        # Detect emotions
        emotions = self._extract_emotions(description)

        # Detect interactions
        interactions = self._extract_interactions(description)

        # Detect layout hints
        layout = self._extract_layout_hints(description)

        return {
            "vibe_type": detected_vibe,
            "colors": colors,
            "emotions": emotions,
            "interactions": interactions,
            "layout": layout,
            "complexity": self._estimate_complexity(description),
        }

    def _extract_colors(self, description: str) -> List[str]:
        """Extract color mentions from description"""
        color_patterns = {
            "red": ["red", "crimson", "scarlet", "blood"],
            "blue": ["blue", "azure", "navy", "sky"],
            "green": ["green", "emerald", "forest", "lime"],
            "yellow": ["yellow", "gold", "amber", "sunny"],
            "purple": ["purple", "violet", "indigo", "lavender"],
            "pink": ["pink", "rose", "magenta", "fuschia"],
            "gray": ["gray", "grey", "silver", "slate"],
            "black": ["black", "dark", "night", "shadow"],
            "white": ["white", "light", "cream", "pale"],
        }

        colors = []
        desc_lower = description.lower()

        for color, keywords in color_patterns.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    colors.append(color)
                    break

        return list(set(colors))

    def _extract_emotions(self, description: str) -> List[str]:
        """Extract emotional descriptors"""
        emotion_patterns = {
            "calm": ["calm", "peaceful", "serene", "relaxing"],
            "energetic": ["energetic", "dynamic", "vibrant", "lively"],
            "playful": ["playful", "fun", "quirky", "whimsical"],
            "serious": ["serious", "professional", "corporate", "formal"],
            "minimal": ["minimal", "simple", "clean", "sparse"],
            "rich": ["rich", "full", "detailed", "elaborate"],
            "warm": ["warm", "cozy", "inviting", "friendly"],
            "cool": ["cool", "sleek", "modern", "edge"],
        }

        emotions = []
        desc_lower = description.lower()

        for emotion, keywords in emotion_patterns.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    emotions.append(emotion)
                    break

        return list(set(emotions))

    def _extract_interactions(self, description: str) -> List[str]:
        """Extract interaction hints"""
        interactions = []
        desc_lower = description.lower()

        interaction_keywords = {
            "hover": "hover_effects",
            "click": "click_feedback",
            "scroll": "scroll_animations",
            "drag": "drag_support",
            "swipe": "swipe_gestures",
            "smooth": "smooth_transitions",
            "animated": "animations",
            "interactive": "interactive_elements",
        }

        for keyword, interaction in interaction_keywords.items():
            if keyword in desc_lower:
                interactions.append(interaction)

        return interactions

    def _extract_layout_hints(self, description: str) -> Dict[str, Any]:
        """Extract layout hints from description"""
        desc_lower = description.lower()

        layout = {
            "direction": "vertical",  # default
            "alignment": "center",
            "spacing": "medium",
            "grid_cols": 1,
        }

        # Direction
        if "horizontal" in desc_lower or "side-by-side" in desc_lower:
            layout["direction"] = "horizontal"

        # Alignment
        if "left" in desc_lower:
            layout["alignment"] = "left"
        elif "right" in desc_lower:
            layout["alignment"] = "right"

        # Spacing
        if "tight" in desc_lower or "compact" in desc_lower:
            layout["spacing"] = "tight"
        elif "spacious" in desc_lower or "open" in desc_lower:
            layout["spacing"] = "large"

        # Grid columns
        if "two" in desc_lower or "2-col" in desc_lower:
            layout["grid_cols"] = 2
        elif "three" in desc_lower or "3-col" in desc_lower:
            layout["grid_cols"] = 3

        return layout

    def _estimate_complexity(self, description: str) -> str:
        """Estimate component complexity"""
        word_count = len(description.split())
        unique_elements = len(set(description.lower().split()))

        if word_count < 20:
            return "simple"
        elif word_count < 50:
            return "medium"
        else:
            return "complex"

    def _generate_component(
        self,
        vibe_analysis: Dict,
        component_type: str,
        framework: str,
    ) -> str:
        """Generate component code based on vibe"""
        vibe_type = vibe_analysis.get("vibe_type", "modern")
        emotions = vibe_analysis.get("emotions", [])
        layout = vibe_analysis.get("layout", {})

        if framework == "react":
            return self._generate_react_component(
                vibe_type, emotions, layout
            )
        elif framework == "vue":
            return self._generate_vue_component(
                vibe_type, emotions, layout
            )
        else:
            return self._generate_html_component(
                vibe_type, emotions, layout
            )

    def _generate_react_component(
        self,
        vibe_type: str,
        emotions: List[str],
        layout: Dict,
    ) -> str:
        """Generate React component"""
        component = f'''
import React, {{ useState, useEffect }} from 'react';
import './VibeComponent.css';

export function VibeComponent() {{
  const [isHovered, setIsHovered] = useState(false);
  const [isAnimating, setIsAnimating] = useState(true);

  const vibe = {{
    type: '{vibe_type}',
    emotions: {json.dumps(emotions)},
    layout: '{layout.get("direction", "vertical")}',
  }};

  return (
    <div className="vibe-container" data-vibe="{{vibe.type}}">
      <div
        className="vibe-content"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Your vibeful content here */}}
        <h1>Feel the Vibe</h1>
        <p>This component was generated from vibes, not specs!</p>
      </div>
    </div>
  );
}}
'''
        return component

    def _generate_vue_component(
        self,
        vibe_type: str,
        emotions: List[str],
        layout: Dict,
    ) -> str:
        """Generate Vue component"""
        return f'''
<template>
  <div class="vibe-container" :data-vibe="vibe.type">
    <div
      class="vibe-content"
      @mouseenter="isHovered = true"
      @mouseleave="isHovered = false"
    >
      <h1>Feel the Vibe</h1>
      <p>This component was generated from vibes, not specs!</p>
    </div>
  </div>
</template>

<script setup>
import {{ ref }} from 'vue';

const isHovered = ref(false);
const vibe = {{
  type: '{vibe_type}',
  emotions: {json.dumps(emotions)},
}};
</script>

<style scoped>
.vibe-container {{
  /* Vibeful styles generated */
}}
</style>
'''

    def _generate_html_component(
        self,
        vibe_type: str,
        emotions: List[str],
        layout: Dict,
    ) -> str:
        """Generate plain HTML component"""
        return f'''
<div class="vibe-container" data-vibe="{vibe_type}">
  <div class="vibe-content">
    <h1>Feel the Vibe</h1>
    <p>This component was generated from vibes, not specs!</p>
  </div>
</div>

<script>
const vibe = {{
  type: '{vibe_type}',
  emotions: {json.dumps(emotions)},
}};

document.querySelector('.vibe-container')
  .addEventListener('mouseenter', function() {{
    this.classList.add('hovered');
  }});
</script>
'''

    def _generate_styles(self, vibe_analysis: Dict) -> str:
        """Generate CSS based on vibe"""
        vibe_type = vibe_analysis.get("vibe_type", "modern")
        colors = vibe_analysis.get("colors", ["blue", "gray"])
        emotions = vibe_analysis.get("emotions", [])

        primary_color = colors[0] if colors else "blue"
        secondary_color = colors[1] if len(colors) > 1 else "gray"

        css = f'''
/* Vibe-Generated Styles: {vibe_type} */

.vibe-container {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}

.vibe-content {{
  padding: 2rem;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
}}

.vibe-container[data-vibe="{vibe_type}"] {{
  --primary: {self._get_color_hex(primary_color)};
  --secondary: {self._get_color_hex(secondary_color)};
'''

        if "calm" in emotions or "peaceful" in emotions:
            css += "\n  animation: float 3s ease-in-out infinite;"

        if "energetic" in emotions or "vibrant" in emotions:
            css += "\n  animation: pulse 1s ease-in-out infinite;"

        css += "\n}\n"
        return css

    def _generate_animations(self, vibe_analysis: Dict) -> str:
        """Generate CSS animations"""
        animations = ""

        if "smooth" in str(vibe_analysis.get("interactions", [])):
            animations += """
@keyframes smoothSlide {
  from { transform: translateX(-10px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
"""

        if "calm" in vibe_analysis.get("emotions", []):
            animations += """
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}
"""

        if "energetic" in vibe_analysis.get("emotions", []):
            animations += """
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
"""

        return animations

    def _get_suggestions(self, vibe_analysis: Dict) -> List[str]:
        """Get optimization suggestions based on vibe"""
        suggestions = [
            "Consider adding micro-interactions",
            "Test accessibility with screen readers",
            "Optimize for mobile responsiveness",
            "Use font pairing for better typography",
        ]

        if "dark" in vibe_analysis.get("vibe_type", ""):
            suggestions.append("Implement dark mode toggle")

        if "interactive" in vibe_analysis.get("interactions", []):
            suggestions.append("Add loading states for interactions")

        return suggestions

    def _vibe_minimalist(self) -> Dict:
        """Minimalist vibe characteristics"""
        return {
            "colors": ["white", "black", "gray"],
            "spacing": "large",
            "typography": "sans-serif",
        }

    def _vibe_vibrant(self) -> Dict:
        """Vibrant vibe characteristics"""
        return {
            "colors": ["red", "yellow", "pink", "blue"],
            "spacing": "medium",
            "animations": "energetic",
        }

    def _vibe_dark(self) -> Dict:
        """Dark vibe characteristics"""
        return {
            "colors": ["black", "gray", "blue"],
            "background": "dark",
            "contrast": "high",
        }

    def _vibe_playful(self) -> Dict:
        """Playful vibe characteristics"""
        return {
            "colors": ["pink", "purple", "yellow"],
            "animations": "bouncy",
            "roundedness": "high",
        }

    def _vibe_professional(self) -> Dict:
        """Professional vibe characteristics"""
        return {
            "colors": ["blue", "gray", "white"],
            "spacing": "structured",
            "typography": "serif",
        }

    def _vibe_futuristic(self) -> Dict:
        """Futuristic vibe characteristics"""
        return {
            "colors": ["cyan", "purple", "black"],
            "effects": "glowing",
            "angles": "sharp",
        }

    def _vibe_cozy(self) -> Dict:
        """Cozy vibe characteristics"""
        return {
            "colors": ["brown", "cream", "orange"],
            "roundedness": "soft",
            "warmth": "high",
        }

    def _vibe_sleek(self) -> Dict:
        """Sleek vibe characteristics"""
        return {
            "colors": ["black", "silver", "white"],
            "contrast": "sharp",
            "minimalism": "high",
        }

    def _get_color_hex(self, color_name: str) -> str:
        """Convert color name to hex"""
        colors = {
            "red": "#ef4444",
            "blue": "#3b82f6",
            "green": "#10b981",
            "yellow": "#f59e0b",
            "purple": "#8b5cf6",
            "pink": "#ec4899",
            "gray": "#6b7280",
            "black": "#000000",
            "white": "#ffffff",
        }
        return colors.get(color_name.lower(), "#3b82f6")


def process_tool(tool_input: dict) -> dict:
    """Process vibe coding request"""
    generator = VibeCodeGenerator()

    return generator.generate_from_vibe(
        vibe_description=tool_input.get("vibe_description", ""),
        component_type=tool_input.get("component_type", "react"),
        framework=tool_input.get("framework", "react"),
    )
