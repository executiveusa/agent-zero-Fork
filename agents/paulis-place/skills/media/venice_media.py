"""
Venice AI Media Skill for Agent Zero
Generate images and videos using Venice AI API
"""

import os
import aiohttp
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class MediaType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class ImageModel(Enum):
    FLUX = "flux"
    STABLE_DIFFUSION = "stable-diffusion"
    DALLE = "dalle"


class VideoModel(Enum):
    KLING = "kling"
    RUNWAY = "runway"
    PIKA = "pika"


@dataclass
class MediaRequest:
    """A media generation request"""
    request_id: str
    media_type: MediaType
    model: str
    prompt: str
    negative_prompt: Optional[str] = None
    aspect_ratio: str = "16:9"
    duration: int = 5
    style: Optional[str] = None


@dataclass
class MediaResult:
    """A generated media result"""
    request_id: str
    media_type: MediaType
    url: str
    seed: int
    model: str


class VeniceMediaSkill:
    """
    Skill for generating media using Venice AI.
    
    Capabilities:
    - Generate images with various models
    - Create videos with Kling, Runway, Pika
    - Apply styles and negative prompts
    - Batch generation
    """
    
    name = "venice_media"
    description = "Generate images and videos using Venice AI"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("VENICE_AI_API_KEY")
        self.base_url = "https://api.venice.ai/api/v1"
        
    async def generate_image(
        self,
        prompt: str,
        model: ImageModel = ImageModel.FLUX,
        aspect_ratio: str = "16:9",
        style: str = None,
        negative_prompt: str = None
    ) -> MediaResult:
        """Generate an image using Venice AI"""
        
        request = MediaRequest(
            request_id=f"img_{hash(prompt) % 10000}",
            media_type=MediaType.IMAGE,
            model=model.value,
            prompt=prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,
            style=style
        )
        
        # API call would go here
        # For now, return a simulated result
        return MediaResult(
            request_id=request.request_id,
            media_type=MediaType.IMAGE,
            url=f"https://venice.ai/generated/{request.request_id}.png",
            seed=12345,
            model=model.value
        )
    
    async def generate_video(
        self,
        prompt: str,
        model: VideoModel = VideoModel.KLING,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        style: str = None
    ) -> MediaResult:
        """Generate a video using Venice AI"""
        
        request = MediaRequest(
            request_id=f"vid_{hash(prompt) % 10000}",
            media_type=MediaType.VIDEO,
            model=model.value,
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            style=style
        )
        
        # API call would go here
        return MediaResult(
            request_id=request.request_id,
            media_type=MediaType.VIDEO,
            url=f"https://venice.ai/generated/{request.request_id}.mp4",
            seed=67890,
            model=model.value
        )
    
    async def generate_ad_creative(
        self,
        ad_concept: Dict[str, Any],
        format: str = "video"
    ) -> List[MediaResult]:
        """Generate ad creatives based on concept"""
        results = []
        
        if format == "video":
            # Generate video ad
            prompt = f"""
            {ad_concept.get('visual_description', 'Professional business setting')}
            
            Style: Cinematic, high-quality, engaging
            Mood: {ad_concept.get('mood', 'Inspiring')}
            
            Scene: {ad_concept.get('scene_description', 'A person discovering a solution')}
            """
            
            result = await self.generate_video(
                prompt=prompt,
                model=VideoModel.KLING,
                duration=ad_concept.get('duration', 10),
                aspect_ratio="9:16"  # Vertical for social
            )
            results.append(result)
            
        elif format == "image":
            # Generate image ad
            prompt = f"""
            {ad_concept.get('visual_description', 'Professional business setting')}
            
            Style: {ad_concept.get('style', 'Modern, clean')}
            Mood: {ad_concept.get('mood', 'Professional')}
            """
            
            result = await self.generate_image(
                prompt=prompt,
                model=ImageModel.FLUX,
                aspect_ratio="1:1"  # Square for social
            )
            results.append(result)
            
        return results
    
    async def batch_generate(
        self,
        prompts: List[str],
        media_type: MediaType = MediaType.IMAGE,
        model: str = "flux"
    ) -> List[MediaResult]:
        """Generate multiple media items in batch"""
        results = []
        
        for prompt in prompts:
            if media_type == MediaType.IMAGE:
                result = await self.generate_image(prompt=prompt, model=ImageModel(model))
            else:
                result = await self.generate_video(prompt=prompt, model=VideoModel(model))
            results.append(result)
            
        return results
    
    def create_ad_prompt(self, concept: str, style: str = "cinematic") -> str:
        """Create a detailed prompt for ad generation"""
        return f"""
        {concept}
        
        Style: {style}, professional, high-quality
        Lighting: Natural, soft, flattering
        Composition: Rule of thirds, dynamic
        Color palette: Warm, inviting, professional
        
        Quality markers: 4K, high resolution, sharp focus
        Negative: blurry, low quality, distorted, amateur
        """


# Skill registration
skill = VeniceMediaSkill()