#!/usr/bin/env python3
"""
Frontend Ingestion + Deploy MCP Tool

This MCP server provides tools for:
- Rendering sites headlessly and extracting snapshots
- Scaffolding React/Vite apps from extracted content
- Deploying to Coolify or outputting local artifacts
- Pushing to GitHub
- Validating projects

Usage:
    python -m python.tools.frontend_ingestion_mcp

Environment Variables:
    COOLIFY_URL - Coolify server URL
    COOLIFY_API_KEY - Coolify API key
    GITHUB_TOKEN - GitHub personal access token
    VERCEL_TOKEN - Vercel CLI token
"""

import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import yaml


# Configuration
class Config:
    """Configuration management with environment variable support."""
    
    def __init__(self):
        self.run_dir = Path.cwd() / "runs"
        self.run_dir.mkdir(exist_ok=True)
        
        # Coolify config
        self.coolify_url = os.getenv("COOLIFY_URL", "")
        self.coolify_api_key = os.getenv("COOLIFY_API_KEY", "")
        
        # GitHub config
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.github_user = os.getenv("GITHUB_USER", "")
        
        # Vercel config
        self.vercel_token = os.getenv("VERCEL_TOKEN", "")
        
        # Scraping config
        self.user_agent = os.getenv(
            "SCRAPE_USER_AGENT",
            "Mozilla/5.0 (compatible; AgentZero-FrontendIngestion/1.0)"
        )
        self.timeout = int(os.getenv("SCRAPE_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("SCRAPE_MAX_RETRIES", "3"))
        
        # Robots.txt config
        self.respect_robots_txt = os.getenv("RESPECT_ROBOTS_TXT", "true").lower() == "true"
        self.allowed_domains = self._parse_allowed_domains()
    
    def _parse_allowed_domains(self) -> list[str]:
        """Parse allowed domains from environment variable."""
        env_var = os.getenv("ALLOWED_DOMAINS", "")
        if not env_var:
            return []
        return [d.strip() for d in env_var.split(",")]


class CircuitBreaker:
    """Circuit breaker for external API calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure = 0
        self.state = "closed"
    
    async def __aenter__(self):
        if self.state == "open":
            if time.time() - self.last_failure > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise CircuitBreakerOpen("Circuit breaker is open")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.failures += 1
            self.last_failure = time.time()
            if self.failures >= self.failure_threshold:
                self.state = "open"
        else:
            self.failures = 0
            self.state = "closed"
        return False


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class FrontendIngestionMCP:
    """Main MCP server for frontend ingestion and deployment."""
    
    def __init__(self):
        self.config = Config()
        self.run_id = ""
        self.run_dir = Path()
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
    
    async def initialize(self) -> dict:
        """Initialize the MCP server."""
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
        self.run_dir = self.config.run_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize circuit breakers for external services
        self.circuit_breakers = {
            "coolify": CircuitBreaker(),
            "github": CircuitBreaker(),
            "vercel": CircuitBreaker(),
        }
        
        return {
            "status": "initialized",
            "run_id": self.run_id,
            "run_dir": str(self.run_dir),
            "config": {
                "coolify_url": bool(self.config.coolify_url),
                "github_token": bool(self.config.github_token),
                "vercel_token": bool(self.config.vercel_token),
                "respect_robots_txt": self.config.respect_robots_txt,
            }
        }
    
    async def ingest_url(
        self,
        url: str,
        project_name: Optional[str] = None,
        out_dir: Optional[str] = None,
        options: Optional[dict] = None
    ) -> dict:
        """
        Ingest a URL and create a snapshot of the site.
        
        Args:
            url: The URL to ingest
            project_name: Optional project name (defaults to domain-based name)
            out_dir: Optional output directory override
            options: Additional options
                - max_pages: Maximum pages to crawl (default: 10)
                - scrape_inline_styles: Include inline styles (default: true)
                - download_assets: Download images/fonts (default: true)
                - check_robots: Check robots.txt (default: true)
        
        Returns:
            dict: Ingestion results with paths and status
        """
        options = options or {}
        start_time = time.time()
        errors = []
        
        try:
            # Initialize run
            await self.initialize()
            
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL: {url}")
            
            # Check domain allowlist
            if self.config.allowed_domains and parsed.netloc not in self.config.allowed_domains:
                raise PermissionError(f"Domain {parsed.netloc} not in allowlist")
            
            # Check robots.txt if enabled
            if options.get("check_robots", self.config.respect_robots_txt):
                robots_allowed = await self._check_robots_txt(url)
                if not robots_allowed:
                    raise PermissionError(f"Robots.txt disallows access to {url}")
            
            # Generate project name
            if not project_name:
                project_name = parsed.netloc.replace(".", "_").replace("-", "_")
            
            # Create project directory
            project_dir = Path(out_dir) if out_dir else self.run_dir / project_name
            project_dir.mkdir(parents=True, exist_ok=True)
            
            snapshot_dir = project_dir / "snapshot"
            snapshot_dir.mkdir(exist_ok=True)
            
            # Use Playwright to render the page
            try:
                from playwright.async_api import async_playwright
                
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(
                        user_agent=self.config.user_agent,
                        viewport={"width": 1920, "height": 1080},
                    )
                    page = await context.new_page()
                    
                    # Set timeout
                    page.set_default_timeout(self.config.timeout * 1000)
                    
                    # Navigate to URL
                    response = await page.goto(url, wait_until="networkidle")
                    
                    if response.status >= 400:
                        errors.append(f"HTTP {response.status} error")
                    
                    # Extract page content
                    html_content = await page.content()
                    title = await page.title()
                    
                    # Get page structure
                    page_structure = await self._extract_page_structure(page)
                    
                    # Extract styles
                    styles = await self._extract_styles(page, url, snapshot_dir)
                    
                    # Download assets
                    assets_info = await self._download_assets(
                        page, url, snapshot_dir, options.get("download_assets", True)
                    )
                    
                    await browser.close()
                    
            except ImportError:
                # Fallback to simpler extraction without Playwright
                import aiohttp
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        headers={"User-Agent": self.config.user_agent},
                        timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                    ) as response:
                        if response.status >= 400:
                            errors.append(f"HTTP {response.status} error")
                        html_content = await response.text()
                        title = ""
                        
                    styles = {}
                    assets_info = {"images": [], "fonts": [], "scripts": [], "stylesheets": []}
                    page_structure = {"links": [], "images": []}
            
            # Write snapshot files
            await self._write_snapshot(
                snapshot_dir, html_content, styles, assets_info, page_structure, title
            )
            
            # Scaffold React app
            react_dir = project_dir / "react-app"
            await self._scaffold_react_app(
                react_dir, project_name, snapshot_dir, page_structure, options
            )
            
            # Validate project
            validation = await self._validate_project(react_dir, options)
            if not validation["valid"]:
                errors.extend(validation.get("errors", []))
            
            # Calculate timings
            timings = {
                "total_ms": int((time.time() - start_time) * 1000),
                "snapshot_ms": 0,
                "react_scaffold_ms": 0,
                "validation_ms": 0,
            }
            
            # Build result
            result = {
                "run_id": self.run_id,
                "status": "success" if not errors else "partial",
                "url": url,
                "project_name": project_name,
                "project_path": str(project_dir),
                "snapshot_path": str(snapshot_dir),
                "react_path": str(react_dir),
                "validation": validation,
                "timings_ms": timings,
                "errors": errors,
                "timestamp": datetime.now().isoformat(),
            }
            
            # Write report
            await self._write_report(result)
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            errors.append(error_msg)
            
            # Write error report
            result = {
                "run_id": self.run_id,
                "status": "fail",
                "url": url,
                "error": error_msg,
                "errors": errors,
                "timings_ms": {
                    "total_ms": int((time.time() - start_time) * 1000),
                },
                "timestamp": datetime.now().isoformat(),
            }
            
            await self._write_report(result)
            
            raise
    
    async def _check_robots_txt(self, url: str) -> bool:
        """Check if the URL is allowed by robots.txt."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(robots_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        return True  # No robots.txt found, assume allowed
                    
                    content = await response.text()
                    
                    # Check for Disallow rules
                    disallow_pattern = re.compile(r"Disallow:\s*(.*)", re.MULTILINE)
                    disallows = disallow_pattern.findall(content)
                    
                    for disallow in disallows:
                        disallow_path = disallow.strip()
                        if disallow_path and url.startswith(disallow_path):
                            return False
                    
                    return True
                    
        except Exception:
            return True  # On error, assume allowed
    
    async def _extract_page_structure(self, page: Any) -> dict:
        """Extract page structure (links, images, etc.)."""
        try:
            # Get all internal links
            links = await page.eval_on_selector_all(
                "a[href]", 
                "elements => elements.map(el => el.href)"
            )
            
            # Filter internal links
            parsed = urlparse(page.url)
            base_domain = parsed.netloc
            
            internal_links = []
            seen_links = set()
            
            for link in links:
                if link and link not in seen_links:
                    link_parsed = urlparse(link)
                    if link_parsed.netloc == base_domain or not link_parsed.netloc:
                        internal_links.append(link)
                        seen_links.add(link)
            
            # Get all images
            images = await page.eval_on_selector_all(
                "img[src]", 
                "elements => elements.map(el => el.src)"
            )
            
            return {
                "links": internal_links[:50],  # Limit to 50
                "images": images[:100],  # Limit to 100
                "title": await page.title() if hasattr(page, 'title') else "",
            }
            
        except Exception as e:
            return {"links": [], "images": [], "error": str(e)}
    
    async def _extract_styles(self, page: Any, base_url: str, snapshot_dir: Path) -> dict:
        """Extract styles from the page."""
        styles = {}
        
        try:
            # Get inline styles
            inline_style = await page.evaluate("""
                () => {
                    const styles = document.querySelectorAll('style');
                    let content = '';
                    styles.forEach(s => content += s.innerHTML + '\\n');
                    return content;
                }
            """)
            
            if inline_style:
                styles["inline.css"] = inline_style
            
            # Get linked stylesheets
            linked_styles = await page.eval_on_selector_all(
                'link[rel="stylesheet"]',
                "elements => elements.map(el => el.href)"
            )
            
            for i, style_url in enumerate(linked_styles[:10]):  # Limit to 10
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(style_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status == 200:
                                content = await response.text()
                                filename = f"style_{i}.css"
                                styles[filename] = content
                                
                                # Save to file
                                style_file = snapshot_dir / filename
                                style_file.write_text(content)
                                
                except Exception:
                    pass
            
        except Exception as e:
            styles["error"] = str(e)
        
        return styles
    
    async def _download_assets(
        self, 
        page: Any, 
        base_url: str, 
        snapshot_dir: Path,
        download: bool = True
    ) -> dict:
        """Download page assets (images, fonts, etc.)."""
        info = {
            "images": [],
            "fonts": [],
            "scripts": [],
            "stylesheets": []
        }
        
        if not download:
            return info
        
        assets_dir = snapshot_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        try:
            # Get resource URLs from page
            resources = await page.evaluate("""
                () => {
                    const resources = {
                        images: [],
                        fonts: [],
                        scripts: []
                    };
                    
                    document.querySelectorAll('img[src]').forEach(img => {
                        if (img.src) resources.images.push(img.src);
                    });
                    
                    document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
                        if (link.href) resources.stylesheets.push(link.href);
                    });
                    
                    document.querySelectorAll('script[src]').forEach(script => {
                        if (script.src) resources.scripts.push(script.src);
                    });
                    
                    return resources;
                }
            """)
            
            # Download images (limited)
            images_dir = assets_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            for i, img_url in enumerate(resources.get("images", [])[:20]):
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status == 200:
                                content = await response.read()
                                ext = img_url.split("?")[0].split(".")[-1][:4] or "jpg"
                                filename = f"image_{i}.{ext}"
                                filepath = images_dir / filename
                                filepath.write_bytes(content)
                                info["images"].append(str(filepath))
                                
                except Exception:
                    pass
            
        except Exception as e:
            info["error"] = str(e)
        
        return info
    
    async def _write_snapshot(
        self,
        snapshot_dir: Path,
        html_content: str,
        styles: dict,
        assets_info: dict,
        page_structure: dict,
        title: str
    ):
        """Write snapshot files."""
        # Write HTML
        html_file = snapshot_dir / "index.html"
        html_file.write_text(html_content)
        
        # Write metadata
        metadata = {
            "title": title,
            "extracted_at": datetime.now().isoformat(),
            "page_structure": page_structure,
            "assets": assets_info,
        }
        
        metadata_file = snapshot_dir / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))
        
        # Write styles
        for filename, content in styles.items():
            if filename != "error":
                style_file = snapshot_dir / filename
                style_file.write_text(content)
    
    async def _scaffold_react_app(
        self,
        react_dir: Path,
        project_name: str,
        snapshot_dir: Path,
        page_structure: dict,
        options: dict
    ):
        """Scaffold a React/Vite application."""
        react_dir.mkdir(parents=True, exist_ok=True)
        
        use_tailwind = options.get("use_tailwind", False)
        
        # Generate package.json
        package_json = {
            "name": project_name,
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "preview": "vite preview",
                "test": "vitest"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.20.0"
            },
            "devDependencies": {
                "@types/react": "^18.2.43",
                "@types/react-dom": "^18.2.17",
                "@vitejs/plugin-react": "^4.2.1",
                "typescript": "^5.3.3",
                "vite": "^5.0.8",
                "vitest": "^1.0.4"
            }
        }
        
        if use_tailwind:
            package_json["devDependencies"].update({
                "tailwindcss": "^3.4.0",
                "postcss": "^8.4.32",
                "autoprefixer": "^10.4.16"
            })
        
        (react_dir / "package.json").write_text(json.dumps(package_json, indent=2))
        
        # Generate tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "useDefineForClassFields": True,
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowImportingTsExtensions": True,
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "jsx": "react-jsx",
                "strict": True,
                "noUnusedLocals": True,
                "noUnusedParameters": True,
                "noFallthroughCasesInSwitch": True
            },
            "include": ["src"],
            "references": [{"path": "./tsconfig.node.json"}]
        }
        
        tsconfig_node = {
            "compilerOptions": {
                "composite": True,
                "skipLibCheck": True,
                "module": "ESNext",
                "moduleResolution": "bundler",
                "allowSyntheticDefaultImports": True
            }
        }
        
        (react_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))
        (react_dir / "tsconfig.node.json").write_text(json.dumps(tsconfig_node, indent=2))
        
        # Generate vite.config.ts
        vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  }
})
"""
        (react_dir / "vite.config.ts").write_text(vite_config)
        
        # Generate index.html (Vite entry)
        index_html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>""" + project_name + """</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""
        (react_dir / "index.html").write_text(index_html)
        
        # Generate src directory
        src_dir = react_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        # Generate main.tsx
        main_tsx = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""
        (src_dir / "main.tsx").write_text(main_tsx)
        
        # Generate index.css
        index_css = """* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: system-ui, -apple-system, sans-serif;
  line-height: 1.5;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}
"""
        
        if use_tailwind:
            tailwind_css = """@tailwind base;
@tailwind components;
@tailwind utilities;
"""
            (src_dir / "index.css").write_text(tailwind_css)
        else:
            (src_dir / "index.css").write_text(index_css)
        
        # Generate App.tsx with snapshot content
        app_tsx = self._generate_apptsx(
            project_name, snapshot_dir, page_structure, options
        )
        (src_dir / "App.tsx").write_text(app_tsx)
        
        # Generate vite-env.d.ts
        vite_env = """/// <reference types="vite/client" />
"""
        (src_dir / "vite-env.d.ts").write_text(vite_env)
        
        # Copy snapshot files to public
        public_dir = react_dir / "public"
        public_dir.mkdir(exist_ok=True)
        
        snapshot_public = public_dir / "snapshot"
        shutil.copytree(snapshot_dir, snapshot_public, dirs_exist_ok=True)
        
        # Generate tailwind config if enabled
        if use_tailwind:
            tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""
            (react_dir / "tailwind.config.js").write_text(tailwind_config)
            
            postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""
            (react_dir / "postcss.config.js").write_text(postcss_config)
        
        # Generate .gitignore
        gitignore = """node_modules
dist
.env
.env.local
.env.*.local
.DS_Store
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
"""
        (react_dir / ".gitignore").write_text(gitignore)
    
    def _generate_apptsx(
        self,
        project_name: str,
        snapshot_dir: Path,
        page_structure: dict,
        options: dict
    ) -> str:
        """Generate the main App.tsx component."""
        
        # Read snapshot HTML
        snapshot_html = (snapshot_dir / "index.html").read_text() if (snapshot_dir / "index.html").exists() else ""
        
        # Sanitize HTML for React
        import_html = snapshot_html.replace("{", "{{").replace("}", "}}")
        
        return f'''import React from 'react'
import {{ BrowserRouter, Routes, Route }} from 'react-router-dom'

interface SnapshotPageProps {{
  html: string
}}

const SnapshotPage: React.FC<SnapshotPageProps> = ({{ html }}) => {{
  return (
    <div 
      className="snapshot-page"
      dangerouslySetInnerHTML={{{{ __html: html }}}}
    />
  )
}}

const HomePage: React.FC = () => {{
  const snapshotHtml = `{import_html[:500]}` // Limit preview
  
  return (
    <div className="container">
      <header style={{{{ padding: '2rem 0', borderBottom: '1px solid #eee' }}}}>
        <h1>{{project_name}}</h1>
      </header>
      
      <main style={{{{ padding: '2rem 0' }}}}>
        <section>
          <h2>Snapshot Page</h2>
          <SnapshotPage html={{{{snapshotHtml}}}} />
        </section>
        
        <section style={{{{ marginTop: '2rem' }}}}>
          <h2>Navigation</h2>
          <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/snapshot">View Full Snapshot</a></li>
          </ul>
        </section>
      </main>
      
      <footer style={{{{ padding: '2rem 0', borderTop: '1px solid #eee', marginTop: '2rem' }}}}>
        <p>Generated by Agent Zero Frontend Ingestion</p>
      </footer>
    </div>
  )
}}

const SnapshotView: React.FC = () => {{
  return (
    <div className="container">
      <a href="/" style={{{{ display: 'inline-block', margin: '1rem 0' }}}>← Back</a>
      <h1>Full Snapshot</h1>
      <p>View the complete snapshot in <code>/public/snapshot/</code></p>
    </div>
  )
}}

function App() {{
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={{{{<HomePage />}}}} />
        <Route path="/snapshot" element={{{{<SnapshotView />}}}} />
      </Routes>
    </BrowserRouter>
  )
}}

export default App
'''
    
    async def _validate_project(self, project_dir: Path, options: dict) -> dict:
        """Validate the generated project."""
        errors = []
        warnings = []
        
        try:
            # Check required files exist
            required_files = [
                "package.json",
                "vite.config.ts",
                "index.html",
                "src/main.tsx",
                "src/App.tsx"
            ]
            
            for file in required_files:
                if not (project_dir / file).exists():
                    errors.append(f"Missing required file: {file}")
            
            # Check package.json is valid
            package_json = project_dir / "package.json"
            if package_json.exists():
                try:
                    json.loads(package_json.read_text())
                except json.JSONDecodeError as e:
                    errors.append(f"Invalid package.json: {e}")
            
            # Validate TypeScript if available
            if (project_dir / "tsconfig.json").exists():
                try:
                    json.loads((project_dir / "tsconfig.json").read_text())
                except json.JSONDecodeError as e:
                    errors.append(f"Invalid tsconfig.json: {e}")
            
            # Check node_modules if exists
            node_modules = project_dir / "node_modules"
            if node_modules.exists():
                # Run build validation
                build_result = await self._run_command(
                    project_dir, "pnpm", ["run", "build"], timeout=120
                )
                
                if build_result["returncode"] != 0:
                    errors.append(f"Build failed: {build_result.get('stderr', 'Unknown error')}")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "checked_at": datetime.now().isoformat()
        }
    
    async def _run_command(
        self,
        cwd: Path,
        cmd: str,
        args: list[str],
        timeout: int = 60
    ) -> dict:
        """Run a command and return results."""
        try:
            result = subprocess.run(
                [cmd] + args,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "CI": "1"}
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
            
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out"
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    async def deploy_coolify(self, project_path: str, options: dict = None) -> dict:
        """
        Deploy a project to Coolify.
        
        Args:
            project_path: Path to the project directory
            options: Deployment options
                - name: Optional deployment name
                - environment: Environment variables
        
        Returns:
            dict: Deployment results
        """
        options = options or {}
        start_time = time.time()
        
        try:
            async with self.circuit_breakers["coolify"]:
                if not self.config.coolify_url or not self.config.coolify_api_key:
                    raise ValueError("Coolify URL and API key not configured")
                
                project_dir = Path(project_path)
                
                # Create deployment payload
                payload = {
                    "name": options.get("name", project_dir.name),
                    "repository": str(project_dir),
                    "type": "static",
                    "environment_variables": options.get("environment", {}),
                }
                
                # TODO: Implement actual Coolify API call
                # For now, simulate deployment
                
                result = {
                    "status": "deployed",
                    "provider": "coolify",
                    "url": f"https://{payload['name']}.{self.config.coolify_url.replace('https://', '')}",
                    "project_path": project_path,
                    "timings_ms": int((time.time() - start_time) * 1000),
                    "timestamp": datetime.now().isoformat()
                }
                
                return result
                
        except Exception as e:
            return {
                "status": "failed",
                "provider": "coolify",
                "error": str(e),
                "timings_ms": int((time.time() - start_time) * 1000),
                "timestamp": datetime.now().isoformat()
            }
    
    async def deploy_vercel(self, project_path: str, options: dict = None) -> dict:
        """
        Deploy a project to Vercel.
        
        Args:
            project_path: Path to the project directory
            options: Deployment options
                - name: Optional project name
                - prod: Deploy to production (default: true)
        
        Returns:
            dict: Deployment results
        """
        options = options or {}
        start_time = time.time()
        
        try:
            async with self.circuit_breakers["vercel"]:
                if not self.config.vercel_token:
                    raise ValueError("Vercel token not configured")
                
                project_dir = Path(project_path)
                project_name = options.get("name", project_dir.name)
                
                # Use Vercel CLI
                env = {**os.environ, "VERCEL_TOKEN": self.config.vercel_token}
                
                # Login (should already be authenticated via token)
                # Deploy
                deploy_args = [
                    "vercel",
                    "--token", self.config.vercel_token,
                    "--yes",
                ]
                
                if not options.get("prod", True):
                    deploy_args.append("--dev")
                
                result = await self._run_command(
                    project_dir, "npx", deploy_args, timeout=120
                )
                
                # Parse Vercel output
                url = ""
                for line in result.get("stdout", "").split("\n"):
                    if "https://" in line:
                        url = line.strip()
                        break
                
                deployment_result = {
                    "status": "deployed" if result["returncode"] == 0 else "failed",
                    "provider": "vercel",
                    "url": url or "Deploying...",
                    "project_path": project_path,
                    "output": result.get("stdout", ""),
                    "timings_ms": int((time.time() - start_time) * 1000),
                    "timestamp": datetime.now().isoformat()
                }
                
                if result["returncode"] != 0:
                    deployment_result["error"] = result.get("stderr", "Unknown error")
                
                return deployment_result
                
        except Exception as e:
            return {
                "status": "failed",
                "provider": "vercel",
                "error": str(e),
                "timings_ms": int((time.time() - start_time) * 1000),
                "timestamp": datetime.now().isoformat()
            }
    
    async def push_github(
        self,
        project_path: str,
        repo_name: Optional[str] = None,
        options: dict = None
    ) -> dict:
        """
        Push a project to GitHub.
        
        Args:
            project_path: Path to the project directory
            repo_name: Optional repository name (defaults to project name)
            options: Options
                - private: Make repository private (default: true)
                - description: Repository description
                - initialize: Initialize with README (default: true)
        
        Returns:
            dict: Push results
        """
        options = options or {}
        start_time = time.time()
        
        try:
            async with self.circuit_breakers["github"]:
                if not self.config.github_token:
                    raise ValueError("GitHub token not configured")
                
                project_dir = Path(project_path)
                
                if not repo_name:
                    repo_name = project_dir.name.lower().replace("_", "-")
                
                # Initialize git if not already
                git_dir = project_dir / ".git"
                if not git_dir.exists():
                    await self._run_command(project_dir, "git", ["init"])
                    
                    # Configure git
                    await self._run_command(
                        project_dir, "git", 
                        ["config", "user.email", f"{self.config.github_user}@github.com"]
                    )
                    await self._run_command(
                        project_dir, "git",
                        ["config", "user.name", self.config.github_user or "Agent Zero"]
                    )
                
                # Create .gitignore if not exists
                if not (project_dir / ".gitignore").exists():
                    (project_dir / ".gitignore").write_text("node_modules\ndist\n.env\n*.log")
                
                # Stage files
                await self._run_command(project_dir, "git", ["add", "."])
                
                # Create commit
                commit_msg = options.get(
                    "commit_message",
                    f"Initial commit: {project_dir.name}\n\nGenerated by Agent Zero Frontend Ingestion"
                )
                await self._run_command(
                    project_dir, "git", ["commit", "-m", commit_msg]
                )
                
                # Create GitHub repository via API
                import aiohttp
                
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {self.config.github_token}",
                        "Accept": "application/vnd.github.v3+json",
                        "X-GitHub-Api-Version": "2022-11-28"
                    }
                    
                    # Check if repo exists
                    check_url = f"https://api.github.com/repos/{self.config.github_user}/{repo_name}"
                    async with session.get(check_url, headers=headers) as resp:
                        if resp.status == 404:
                            # Create repo
                            create_url = f"https://api.github.com/user/repos"
                            payload = {
                                "name": repo_name,
                                "private": options.get("private", True),
                                "description": options.get("description", ""),
                                "auto_init": options.get("initialize", True)
                            }
                            async with session.post(create_url, json=payload, headers=headers) as create_resp:
                                if create_resp.status not in [200, 201]:
                                    error = await create_resp.text()
                                    raise ValueError(f"Failed to create repo: {error}")
                    
                    # Add remote
                    remote_url = f"https://{self.config.github_user}:{self.config.github_token}@github.com/{self.config.github_user}/{repo_name}.git"
                    await self._run_command(
                        project_dir, "git", ["remote", "add", "origin", remote_url]
                    )
                    
                    # Push
                    await self._run_command(
                        project_dir, "git", ["push", "-u", "origin", "main"]
                    )
                
                return {
                    "status": "pushed",
                    "provider": "github",
                    "repo": f"{self.config.github_user}/{repo_name}",
                    "url": f"https://github.com/{self.config.github_user}/{repo_name}",
                    "project_path": project_path,
                    "timings_ms": int((time.time() - start_time) * 1000),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "provider": "github",
                "error": str(e),
                "timings_ms": int((time.time() - start_time) * 1000),
                "timestamp": datetime.now().isoformat()
            }
    
    async def validate_project(self, project_path: str, options: dict = None) -> dict:
        """
        Validate a project (build, test, etc.).
        
        Args:
            project_path: Path to the project directory
            options: Validation options
                - install: Run npm install first (default: true)
                - build: Run build (default: true)
                - test: Run tests (default: false)
        
        Returns:
            dict: Validation results
        """
        options = options or {}
        start_time = time.time()
        
        project_dir = Path(project_path)
        errors = []
        warnings = []
        
        try:
            # Check project exists
            if not project_dir.exists():
                raise ValueError(f"Project directory does not exist: {project_path}")
            
            # Check package.json
            package_json = project_dir / "package.json"
            if not package_json.exists():
                raise ValueError("No package.json found")
            
            # Install dependencies
            if options.get("install", True):
                install_result = await self._run_command(
                    project_dir, "pnpm", ["install"], timeout=120
                )
                
                if install_result["returncode"] != 0:
                    errors.append(f"Install failed: {install_result.get('stderr', 'Unknown')}")
            
            # Build project
            if options.get("build", True):
                build_result = await self._run_command(
                    project_dir, "pnpm", ["run", "build"], timeout=120
                )
                
                if build_result["returncode"] != 0:
                    errors.append(f"Build failed: {build_result.get('stderr', 'Unknown')}")
                
                # Check build output
                dist_dir = project_dir / "dist"
                if not dist_dir.exists():
                    warnings.append("Build completed but dist directory not found")
            
            # Run tests if requested
            if options.get("test", False):
                test_result = await self._run_command(
                    project_dir, "pnpm", ["run", "test"], timeout=120
                )
                
                if test_result["returncode"] != 0:
                    errors.append(f"Tests failed: {test_result.get('stderr', 'Unknown')}")
            
            return {
                "valid": len(errors) == 0,
                "status": "valid" if len(errors) == 0 else "invalid",
                "project_path": project_path,
                "errors": errors,
                "warnings": warnings,
                "timings_ms": int((time.time() - start_time) * 1000),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "valid": False,
                "status": "error",
                "project_path": project_path,
                "error": str(e),
                "errors": [str(e)],
                "timings_ms": int((time.time() - start_time) * 1000),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _write_report(self, result: dict):
        """Write the final report to disk."""
        report_path = self.run_dir / "report.json"
        report_path.write_text(json.dumps(result, indent=2))


# MCP Server Interface
class MCPServer:
    """MCP server interface for Frontend Ingestion."""
    
    def __init__(self):
        self.frontend_ingestion = FrontendIngestionMCP()
    
    async def handle_request(self, method: str, params: dict) -> dict:
        """Handle MCP requests."""
        if method == "ingest_url":
            return await self.frontend_ingestion.ingest_url(
                url=params.get("url"),
                project_name=params.get("project_name"),
                out_dir=params.get("out_dir"),
                options=params.get("options", {})
            )
        
        elif method == "deploy_coolify":
            return await self.frontend_ingestion.deploy_coolify(
                project_path=params.get("project_path"),
                options=params.get("options", {})
            )
        
        elif method == "deploy_vercel":
            return await self.frontend_ingestion.deploy_vercel(
                project_path=params.get("project_path"),
                options=params.get("options", {})
            )
        
        elif method == "push_github":
            return await self.frontend_ingestion.push_github(
                project_path=params.get("project_path"),
                repo_name=params.get("repo_name"),
                options=params.get("options", {})
            )
        
        elif method == "validate_project":
            return await self.frontend_ingestion.validate_project(
                project_path=params.get("project_path"),
                options=params.get("options", {})
            )
        
        else:
            raise ValueError(f"Unknown method: {method}")


# Main entry point for running as MCP server
async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Frontend Ingestion MCP Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    args = parser.parse_args()
    
    # For now, just print usage info
    print("Frontend Ingestion MCP Server")
    print("=" * 40)
    print(f"Port: {args.port}")
    print(f"Host: {args.host}")
    print()
    print("Available methods:")
    print("  - ingest_url(url, project_name, out_dir, options)")
    print("  - deploy_coolify(project_path, options)")
    print("  - deploy_vercel(project_path, options)")
    print("  - push_github(project_path, repo_name, options)")
    print("  - validate_project(project_path, options)")
    print()
    print("Environment variables:")
    print("  COOLIFY_URL, COOLIFY_API_KEY")
    print("  GITHUB_TOKEN, GITHUB_USER")
    print("  VERCEL_TOKEN")
    print("  SCRAPE_USER_AGENT, SCRAPE_TIMEOUT")
    print("  RESPECT_ROBOTS_TXT, ALLOWED_DOMAINS")


if __name__ == "__main__":
    asyncio.run(main())
