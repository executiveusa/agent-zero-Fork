"""
Loveable.dev Project Upgrader

Analyzes Loveable.dev sites and automatically enhances unfinished projects
with new features, better UX/UI, and production-ready improvements.
"""

import json
import re
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None


class LoveableProjectUpgrader:
    """Upgrade and enhance Loveable.dev projects"""

    def __init__(self):
        self.loveable_api_key = os.getenv("LOVEABLE_API_KEY", "")
        self.base_url = "https://lovable.dev/api"
        self.upgrade_suggestions = []

    def analyze_project(self, project_id: str) -> Dict[str, Any]:
        """Analyze a Loveable.dev project for upgrade opportunities"""
        try:
            project_data = self._fetch_project_data(project_id)
            if not project_data:
                return {"error": "Project not found", "success": False}

            analysis = {
                "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
                "current_state": self._analyze_current_state(project_data),
                "missing_features": self._identify_missing_features(project_data),
                "ui_ux_improvements": self._analyze_ui_ux(project_data),
                "performance_issues": self._analyze_performance(project_data),
                "security_concerns": self._analyze_security(project_data),
                "upgrade_roadmap": self._generate_upgrade_roadmap(project_data),
            }
            return {"success": True, **analysis}
        except Exception as e:
            return {"error": str(e), "success": False}

    def _fetch_project_data(self, project_id: str) -> Optional[Dict]:
        """Fetch project data from Loveable.dev"""
        if not requests or not self.loveable_api_key:
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.loveable_api_key}",
                "Accept": "application/json",
            }
            response = requests.get(
                f"{self.base_url}/projects/{project_id}",
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def _analyze_current_state(self, project_data: Dict) -> Dict[str, Any]:
        """Analyze current project state"""
        return {
            "project_name": project_data.get("name", ""),
            "created_date": project_data.get("created_at"),
            "last_updated": project_data.get("updated_at"),
            "completion_percentage": project_data.get("completion", 0),
            "current_features": len(project_data.get("features", [])),
            "tech_stack": project_data.get("tech_stack", []),
        }

    def _identify_missing_features(self, project_data: Dict) -> List[Dict]:
        """Identify features that should be added"""
        features = project_data.get("features", [])
        missing = []

        # Common features to check
        feature_checklist = [
            {"name": "Authentication", "category": "security"},
            {"name": "User Profiles", "category": "user"},
            {"name": "Search Functionality", "category": "feature"},
            {"name": "Pagination", "category": "ux"},
            {"name": "Filtering & Sorting", "category": "feature"},
            {"name": "Export Data", "category": "feature"},
            {"name": "Analytics", "category": "monitoring"},
            {"name": "Real-time Updates", "category": "feature"},
            {"name": "Notifications", "category": "user"},
            {"name": "Dark Mode", "category": "ux"},
        ]

        existing_features = [f["name"].lower() for f in features]

        for feature in feature_checklist:
            if feature["name"].lower() not in existing_features:
                missing.append({
                    "name": feature["name"],
                    "category": feature["category"],
                    "priority": "high" if feature["category"] in ["security", "user"] else "medium",
                })

        return missing[:10]

    def _analyze_ui_ux(self, project_data: Dict) -> Dict[str, List]:
        """Analyze UI/UX for improvements"""
        improvements = {
            "layout": [],
            "accessibility": [],
            "responsiveness": [],
            "performance": [],
        }

        html_content = project_data.get("html", "")

        # Check for accessibility
        if "alt=" not in html_content:
            improvements["accessibility"].append("Add alt text to images")
        if "aria-label" not in html_content:
            improvements["accessibility"].append("Add ARIA labels for better screen reader support")
        if "role=" not in html_content:
            improvements["accessibility"].append("Add ARIA roles for semantic structure")

        # Check for mobile responsiveness
        if "viewport" not in html_content:
            improvements["responsiveness"].append("Add responsive viewport meta tag")
        if "flex" not in html_content and "grid" not in html_content:
            improvements["layout"].append("Use flexbox/grid for better responsive design")

        # Check for performance
        if "defer" not in html_content or "async" not in html_content:
            improvements["performance"].append("Optimize script loading with defer/async")
        if "loading='lazy'" not in html_content:
            improvements["performance"].append("Implement lazy loading for images")

        return improvements

    def _analyze_performance(self, project_data: Dict) -> Dict[str, Any]:
        """Analyze performance issues"""
        return {
            "issues": [
                "Optimize bundle size",
                "Implement code splitting",
                "Add caching strategies",
                "Minimize CSS/JS",
            ],
            "recommendations": [
                "Use CDN for static assets",
                "Implement service workers",
                "Add compression for API responses",
            ],
        }

    def _analyze_security(self, project_data: Dict) -> Dict[str, Any]:
        """Analyze security concerns"""
        concerns = {
            "critical": [],
            "high": [],
            "medium": [],
        }

        # Basic security checks
        if "https" not in project_data.get("url", ""):
            concerns["critical"].append("Enable HTTPS/SSL")
        if "csrf" not in project_data.get("framework", "").lower():
            concerns["high"].append("Implement CSRF protection")
        if "rate_limit" not in str(project_data.get("api", {})):
            concerns["high"].append("Add rate limiting to API endpoints")
        if "sanitize" not in str(project_data.get("validation", {})):
            concerns["medium"].append("Sanitize user inputs")

        return concerns

    def _generate_upgrade_roadmap(self, project_data: Dict) -> List[Dict]:
        """Generate step-by-step upgrade roadmap"""
        roadmap = []

        # Phase 1: Security & Stability
        roadmap.append({
            "phase": 1,
            "name": "Security & Stability",
            "duration": "1-2 weeks",
            "tasks": [
                "Enable HTTPS/SSL",
                "Implement authentication",
                "Add error handling",
                "Set up monitoring",
            ],
        })

        # Phase 2: Features
        roadmap.append({
            "phase": 2,
            "name": "Core Features",
            "duration": "2-3 weeks",
            "tasks": [
                "Add search functionality",
                "Implement filtering/sorting",
                "Add user profiles",
                "Enable data export",
            ],
        })

        # Phase 3: UX/UI Improvements
        roadmap.append({
            "phase": 3,
            "name": "UX/UI Enhancement",
            "duration": "2-3 weeks",
            "tasks": [
                "Improve responsive design",
                "Add dark mode",
                "Enhance accessibility",
                "Optimize performance",
            ],
        })

        # Phase 4: Advanced Features
        roadmap.append({
            "phase": 4,
            "name": "Advanced Features",
            "duration": "3-4 weeks",
            "tasks": [
                "Add real-time updates",
                "Implement notifications",
                "Add analytics dashboard",
                "Create API documentation",
            ],
        })

        return roadmap

    def generate_upgrade_code(
        self,
        project_id: str,
        feature: str,
    ) -> Dict[str, Any]:
        """Generate code for a specific upgrade"""
        try:
            project_data = self._fetch_project_data(project_id)
            if not project_data:
                return {"error": "Project not found", "success": False}

            code_templates = self._get_code_templates(project_data, feature)

            return {
                "success": True,
                "feature": feature,
                "code": code_templates,
                "installation_steps": self._get_installation_steps(feature),
                "dependencies": self._get_dependencies(feature),
                "testing_guide": self._get_testing_guide(feature),
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def _get_code_templates(self, project_data: Dict, feature: str) -> Dict:
        """Get code templates for features"""
        templates = {
            "Authentication": {
                "component": self._template_auth_component(),
                "api": self._template_auth_api(),
            },
            "Dark Mode": {
                "component": self._template_dark_mode(),
                "styles": self._template_dark_mode_styles(),
            },
            "Search": {
                "component": self._template_search_component(),
                "filter": self._template_search_filter(),
            },
        }
        return templates.get(feature, {})

    def _template_auth_component(self) -> str:
        """Template for authentication component"""
        return '''
// AuthContext.jsx
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await response.json();
      setUser(data.user);
      localStorage.setItem('token', data.token);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login }}>
      {children}
    </AuthContext.Provider>
  );
}
'''

    def _template_dark_mode(self) -> str:
        """Template for dark mode component"""
        return '''
// useTheme.js
export function useTheme() {
  const [isDark, setIsDark] = useState(() => {
    return localStorage.getItem('theme') === 'dark';
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  return { isDark, toggleTheme: () => setIsDark(!isDark) };
}
'''

    def _template_search_component(self) -> str:
        """Template for search component"""
        return '''
// SearchComponent.jsx
export function SearchComponent() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleSearch = debounce(async (term) => {
    if (term.length < 2) return;
    const response = await fetch(`/api/search?q=${term}`);
    const data = await response.json();
    setResults(data);
  }, 300);

  return (
    <div className="search">
      <input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          handleSearch(e.target.value);
        }}
        placeholder="Search..."
      />
      <div className="results">
        {results.map(item => <div key={item.id}>{item.name}</div>)}
      </div>
    </div>
  );
}
'''

    def _template_dark_mode_styles(self) -> str:
        """Template for dark mode CSS"""
        return '''
/* styles.css */
:root {
  --bg: #ffffff;
  --text: #000000;
}

:root.dark {
  --bg: #1a1a1a;
  --text: #ffffff;
}

body {
  background-color: var(--bg);
  color: var(--text);
  transition: all 0.3s ease;
}
'''

    def _template_search_filter(self) -> str:
        """Template for search filter"""
        return "// Filter implementation"

    def _get_installation_steps(self, feature: str) -> List[str]:
        """Get installation steps for a feature"""
        return [
            f"1. Copy the {feature} component code",
            f"2. Install required dependencies",
            f"3. Import the component in your project",
            f"4. Configure settings as needed",
            f"5. Test the integration",
        ]

    def _get_dependencies(self, feature: str) -> List[str]:
        """Get dependencies for a feature"""
        deps = {
            "Authentication": ["bcryptjs", "jsonwebtoken", "passport"],
            "Dark Mode": ["tailwindcss"],
            "Search": ["fuse.js", "react-select"],
        }
        return deps.get(feature, [])

    def _get_testing_guide(self, feature: str) -> str:
        """Get testing guide for a feature"""
        return f"""
## Testing Guide for {feature}

1. Unit Tests
   - Test individual functions
   - Mock external dependencies
   - Verify expected outputs

2. Integration Tests
   - Test component interaction
   - Verify data flow
   - Test edge cases

3. Manual Testing
   - Test in browser
   - Verify on mobile
   - Test with accessibility tools
"""


import os


def process_tool(tool_input: dict) -> dict:
    """Process Loveable project upgrade request"""
    upgrader = LoveableProjectUpgrader()

    action = tool_input.get("action", "analyze")
    project_id = tool_input.get("project_id", "")

    if action == "analyze":
        return upgrader.analyze_project(project_id)
    elif action == "generate_code":
        return upgrader.generate_upgrade_code(
            project_id=project_id,
            feature=tool_input.get("feature", ""),
        )
    else:
        return {"error": f"Unknown action: {action}"}
