"""
UI2Code_N Integration for Design-to-Code Conversion
Converts design files to React/Vue/HTML components
"""

import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Classes
# ============================================================================

class OutputFramework(Enum):
    """Supported output frameworks."""
    REACT = "react"
    VUE = "vue"
    HTML = "html"
    SVELTE = "svelte"
    ANGULAR = "angular"


class DesignFormat(Enum):
    """Input design formats."""
    IMAGE = "image"
    FIGMA_URL = "figma_url"
    JSON_SPEC = "json"


@dataclass
class DesignElement:
    """Parsed design element."""
    type: str
    name: str
    properties: Dict[str, Any]
    children: List["DesignElement"] = field(default_factory=list)
    styles: Dict[str, Any] = field(default_factory=dict)
    bounds: Optional[Dict[str, int]] = None


@dataclass
class ComponentSpec:
    """Component specification from design."""
    name: str
    elements: List[DesignElement]
    props: List[str] = field(default_factory=list)
    state_vars: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    styling_method: str = "css"


@dataclass
class GeneratedComponent:
    """Generated code component."""
    name: str
    code: str
    framework: OutputFramework
    css: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# Style Mapping
# ============================================================================

TAILWIND_MAPPINGS = {
    "flex": "flex",
    "flex-direction: column": "flex-col",
    "justify-content: center": "justify-center",
    "align-items: center": "items-center",
    "padding: 16px": "p-4",
    "margin: 16px": "m-4",
    "border-radius: 8px": "rounded",
    "background-color: #ffffff": "bg-white",
    "color: #000000": "text-black",
    "font-size: 16px": "text-base",
    "font-weight: bold": "font-bold",
}


# ============================================================================
# Design Parser
# ============================================================================

class DesignParser:
    """Parse design files into structured format."""
    
    @staticmethod
    def parse_image(image_path: str) -> Dict[str, Any]:
        return {
            "type": "image",
            "path": image_path,
            "elements": [],
            "note": "Image analysis requires vision model"
        }
    
    @staticmethod
    def parse_figma_url(url: str) -> Dict[str, Any]:
        parts = url.split("/")
        file_key = None
        node_id = None
        for i, part in enumerate(parts):
            if part == "file" and i + 1 < len(parts):
                file_key = parts[i + 1]
            if part == "node-id" and i + 1 < len(parts):
                node_id = parts[i + 1]
        return {"type": "figma_url", "file_key": file_key, "node_id": node_id}
    
    @staticmethod
    def parse_json_spec(json_data: Dict[str, Any]) -> ComponentSpec:
        elements = []
        for elem_data in json_data.get("elements", []):
            element = DesignElement(
                type=elem_data.get("type", "div"),
                name=elem_data.get("name", "element"),
                properties=elem_data.get("properties", {}),
                children=[],
                styles=elem_data.get("styles", {}),
                bounds=elem_data.get("bounds")
            )
            elements.append(element)
        return ComponentSpec(
            name=json_data.get("name", "GeneratedComponent"),
            elements=elements,
            props=json_data.get("props", []),
            state_vars=json_data.get("state", []),
            imports=json_data.get("imports", []),
            styling_method=json_data.get("styling_method", "css")
        )


# ============================================================================
# Code Generator
# ============================================================================

class UICodeGenerator:
    """Generate code from design specifications."""
    
    def __init__(self, framework: OutputFramework = OutputFramework.REACT):
        self.framework = framework
    
    def generate(self, spec: ComponentSpec) -> GeneratedComponent:
        if self.framework == OutputFramework.REACT:
            return self._generate_react(spec)
        elif self.framework == OutputFramework.VUE:
            return self._generate_vue(spec)
        elif self.framework == OutputFramework.HTML:
            return self._generate_html(spec)
        elif self.framework == OutputFramework.SVELTE:
            return self._generate_svelte(spec)
        elif self.framework == OutputFramework.ANGULAR:
            return self._generate_angular(spec)
        return self._generate_html(spec)
    
    def _generate_react(self, spec: ComponentSpec) -> GeneratedComponent:
        imports = ["import React"]
        if spec.state_vars:
            imports.append("import { useState } from 'react'")
        
        elements_code = self._elements_to_jsx(spec.elements)
        css = self._generate_css(spec)
        
        code = f"""{chr(10).join(imports)}

export const {spec.name}: React.FC = ({', '.join(spec.props) or ''}) => {{
  return (
    <>
{elements_code}
    </>
  );
}};
"""
        return GeneratedComponent(
            name=spec.name, code=code, framework=OutputFramework.REACT,
            css=css, dependencies=["react"]
        )
    
    def _generate_vue(self, spec: ComponentSpec) -> GeneratedComponent:
        props_def = ""
        if spec.props:
            props_def = f"\nprops: {{\n{chr(10).join(f'  {prop}: String' for prop in spec.props)}\n}}"
        elements_code = self._elements_to_template(spec.elements)
        css = self._generate_css(spec)
        code = f"""<template>
  <div>
{elements_code}  </div>
</template>

<script>
export default {{{props_def}
}}
</script>
"""
        return GeneratedComponent(
            name=spec.name, code=code, framework=OutputFramework.VUE,
            css=css, dependencies=["vue"]
        )
    
    def _generate_html(self, spec: ComponentSpec) -> GeneratedComponent:
        elements_code = self._elements_to_html(spec.elements)
        css = self._generate_css(spec)
        code = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{spec.name}</title>
  <style>
{css}
  </style>
</head>
<body>
{elements_code}
</body>
</html>
"""
        return GeneratedComponent(
            name=spec.name, code=code, framework=OutputFramework.HTML,
            css=None, dependencies=[]
        )
    
    def _generate_svelte(self, spec: ComponentSpec) -> GeneratedComponent:
        props = f"export let {', '.join(spec.props)};" if spec.props else ""
        elements_code = self._elements_to_html(spec.elements)
        css = self._generate_css(spec)
        code = f"""<script>
{props}
</script>

{elements_code}

<style>
{css}
</style>
"""
        return GeneratedComponent(
            name=spec.name, code=code, framework=OutputFramework.SVELTE,
            css=None, dependencies=["svelte"]
        )
    
    def _generate_angular(self, spec: ComponentSpec) -> GeneratedComponent:
        inputs = f"\n  @Input() {', '.join(spec.props)};" if spec.props else ""
        template = self._elements_to_html(spec.elements)
        css = self._generate_css(spec)
        code = f"""import {{ Component, Input }} from '@angular/core';
@Component({{
  selector: 'app-{spec.name.lower()}',
  template: `{template}`,
  styles: [`{css}`]
}})
export class {spec.name}Component {{{inputs}
}}
"""
        return GeneratedComponent(
            name=spec.name, code=code, framework=OutputFramework.ANGULAR,
            css=None, dependencies=["@angular/core"]
        )
    
    def _elements_to_jsx(self, elements: List[DesignElement], indent: int = 2) -> str:
        lines = []
        indent_str = " " * indent
        for elem in elements:
            props = []
            if elem.styles:
                class_parts = []
                for prop, value in elem.styles.items():
                    if prop in TAILWIND_MAPPINGS:
                        class_parts.append(TAILWIND_MAPPINGS[prop])
                if class_parts:
                    props.append(f'className="{" ".join(class_parts)}"')
            if elem.name:
                props.append(f'key="{elem.name}"')
            props_str = " ".join(props) if props else ""
            if elem.children:
                children_code = self._elements_to_jsx(elem.children, indent + 2)
                lines.append(f"{indent_str}<{elem.type} {props_str}>\n{children_code}\n{indent_str}</{elem.type}>")
            else:
                lines.append(f"{indent_str}<{elem.type} {props_str} />")
        return "\n".join(lines)
    
    def _elements_to_html(self, elements: List[DesignElement], indent: int = 2) -> str:
        lines = []
        indent_str = " " * indent
        for elem in elements:
            if elem.children:
                children_code = self._elements_to_html(elem.children, indent + 2)
                lines.append(f'{indent_str}<{elem.name}>{children_code}</{elem.name}>')
            else:
                lines.append(f"{indent_str}<{elem.name} />")
        return "\n".join(lines)
    
    def _elements_to_template(self, elements: List[DesignElement], indent: int = 2) -> str:
        return self._elements_to_html(elements, indent)
    
    def _generate_css(self, spec: ComponentSpec) -> str:
        rules = []
        for elem in spec.elements:
            selector = f".{elem.name}" if elem.name else ".element"
            if elem.styles:
                properties = [f"  {k}: {v};" for k, v in elem.styles.items()]
                if properties:
                    rules.append(f"{selector} {{\n{chr(10).join(properties)}\n}}")
        return "\n".join(rules)


# ============================================================================
# UI2Code Tool
# ============================================================================

class UI2CodeTool(Tool):
    """Design-to-Code Conversion Tool."""
    
    async def execute(self, **kwargs):
        input_source: str = kwargs.get("input")
        format_type: str = kwargs.get("format", "json")
        framework: str = kwargs.get("framework", "react")
        output_file: Optional[str] = kwargs.get("output")
        
        if not input_source:
            return Response(message="input argument required", break_loop=False)
        
        try:
            design_format = DesignFormat(format_type)
            output_framework = OutputFramework(framework.lower())
        except ValueError as e:
            return Response(message=str(e), break_loop=False)
        
        try:
            if design_format == DesignFormat.JSON_SPEC:
                if input_source.startswith("{") or input_source.startswith("["):
                    json_data = json.loads(input_source)
                else:
                    json_data = json.loads(Path(input_source).read_text())
                spec = DesignParser.parse_json_spec(json_data)
            elif design_format == DesignFormat.IMAGE:
                json_data = DesignParser.parse_image(input_source)
                spec = ComponentSpec(name="ImageComponent", elements=[], styling_method="css")
                PrintStyle.warning("Image analysis requires vision model")
            elif design_format == DesignFormat.FIGMA_URL:
                json_data = DesignParser.parse_figma_url(input_source)
                spec = ComponentSpec(name="FigmaComponent", elements=[], styling_method="css")
                PrintStyle.warning("Figma API integration required")
            else:
                return Response(message=f"Format {format_type} not implemented", break_loop=False)
            
            generator = UICodeGenerator(output_framework)
            result = generator.generate(spec)
            
            if output_file:
                Path(output_file).write_text(result.code)
                return Response(
                    message=f"Generated {result.name} in {result.framework.value}\nOutput: {output_file}",
                    break_loop=False
                )
            
            return Response(
                message=f"```{result.framework.value}\n{result.code}\n```\n\nCSS:\n```{result.css or '/* No CSS */'}```",
                break_loop=False
            )
        except json.JSONDecodeError as e:
            return Response(message=f"Invalid JSON: {e}", break_loop=False)
        except Exception as e:
            PrintStyle.error(f"UI2Code error: {e}")
            return Response(message=f"UI2Code error: {e}", break_loop=False)


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "UI2CodeTool", "UICodeGenerator", "DesignParser",
    "GeneratedComponent", "ComponentSpec", "DesignElement",
    "OutputFramework", "DesignFormat"
]
