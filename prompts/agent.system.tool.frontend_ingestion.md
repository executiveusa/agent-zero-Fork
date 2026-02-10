# Tool: `frontend_ingestion`

## Description

The `frontend_ingestion` tool enables Agent Zero to render websites headlessly, extract static snapshots, scaffold React/Vite applications, and deploy them to Coolify, Vercel, or GitHub. This tool is designed for frontend ingestion, migration, and deployment workflows.

## Capabilities

- **URL Ingestion**: Render any URL headlessly using Playwright
- **Snapshot Extraction**: Capture HTML, CSS, images, and assets
- **React Scaffolding**: Generate a Vite React TypeScript application
- **Deployment**: Deploy to Coolify, Vercel, or output as local artifact
- **GitHub Integration**: Push projects to GitHub repositories
- **Validation**: Build validation and health checks

## Methods

### `ingest_url`

Ingest a URL and create a snapshot + React app.

**Parameters:**

- `url` (required, string): The URL to ingest
- `project_name` (optional, string): Project name (defaults to domain-based name)
- `out_dir` (optional, string): Output directory override
- `options` (optional, object):
  - `max_pages` (number): Maximum pages to crawl (default: 10)
  - `scrape_inline_styles` (boolean): Include inline styles (default: true)
  - `download_assets` (boolean): Download images/fonts (default: true)
  - `check_robots` (boolean): Check robots.txt (default: true)
  - `use_tailwind` (boolean): Enable Tailwind CSS (default: false)

**Returns:**

```json
{
  "run_id": "20240209_143000_abc123",
  "status": "success",
  "url": "https://example.com",
  "project_name": "example_com",
  "project_path": "/path/to/runs/20240209_.../example_com",
  "snapshot_path": "/path/to/.../example_com/snapshot",
  "react_path": "/path/to/.../example_com/react-app",
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": []
  },
  "timings_ms": {
    "total_ms": 15000,
    "snapshot_ms": 8000,
    "react_scaffold_ms": 5000,
    "validation_ms": 2000
  },
  "errors": [],
  "timestamp": "2024-02-09T14:30:00Z"
}
```

### `deploy_coolify`

Deploy a project to Coolify.

**Parameters:**

- `project_path` (required, string): Path to the project directory
- `options` (optional, object):
  - `name` (string): Deployment name
  - `environment` (object): Environment variables

**Returns:**

```json
{
  "status": "deployed",
  "provider": "coolify",
  "url": "https://example.coolify.domain.com",
  "project_path": "/path/to/project",
  "timings_ms": 5000,
  "timestamp": "2024-02-09T14:30:00Z"
}
```

### `deploy_vercel`

Deploy a project to Vercel.

**Parameters:**

- `project_path` (required, string): Path to the project directory
- `options` (optional, object):
  - `name` (string): Project name
  - `prod` (boolean): Deploy to production (default: true)

**Returns:**

```json
{
  "status": "deployed",
  "provider": "vercel",
  "url": "https://example.vercel.app",
  "project_path": "/path/to/project",
  "output": "...",
  "timings_ms": 8000,
  "timestamp": "2024-02-09T14:30:00Z"
}
```

### `push_github`

Push a project to GitHub.

**Parameters:**

- `project_path` (required, string): Path to the project directory
- `repo_name` (optional, string): Repository name
- `options` (optional, object):
  - `private` (boolean): Make repository private (default: true)
  - `description` (string): Repository description
  - `commit_message` (string): Commit message

**Returns:**

```json
{
  "status": "pushed",
  "provider": "github",
  "repo": "username/example-com",
  "url": "https://github.com/username/example-com",
  "project_path": "/path/to/project",
  "timings_ms": 10000,
  "timestamp": "2024-02-09T14:30:00Z"
}
```

### `validate_project`

Validate a project (build, test, etc.).

**Parameters:**

- `project_path` (required, string): Path to the project directory
- `options` (optional, object):
  - `install` (boolean): Run npm install first (default: true)
  - `build` (boolean): Run build (default: true)
  - `test` (boolean): Run tests (default: false)

**Returns:**

```json
{
  "valid": true,
  "status": "valid",
  "project_path": "/path/to/project",
  "errors": [],
  "warnings": [],
  "timings_ms": 15000,
  "timestamp": "2024-02-09T14:30:00Z"
}
```

## Usage Examples

### Basic Ingestion

```python
# Ingest a URL and create a React app
result = await frontend_ingestion.ingest_url(
    url="https://example.com",
    project_name="my-landing-page"
)

# Access results
print(f"Status: {result['status']}")
print(f"React app: {result['react_path']}")
print(f"Build valid: {result['validation']['valid']}")
```

### Ingestion with Tailwind

```python
result = await frontend_ingestion.ingest_url(
    url="https://example.com",
    options={
        "use_tailwind": True,
        "download_assets": True,
        "check_robots": True
    }
)
```

### Full Deployment Pipeline

```python
# Ingest
ingest_result = await frontend_ingestion.ingest_url(
    url="https://example.com",
    project_name="my-project"
)

# Deploy to Vercel
deploy_result = await frontend_ingestion.deploy_vercel(
    project_path=ingest_result["react_path"],
    options={"name": "my-project"}
)

# Push to GitHub
github_result = await frontend_ingestion.push_github(
    project_path=ingest_result["react_path"],
    repo_name="my-project",
    options={"description": "Migrated from example.com"}
)
```

### Validation Only

```python
# Validate existing project
result = await frontend_ingestion.validate_project(
    project_path="/path/to/existing/project",
    options={
        "install": True,
        "build": True,
        "test": False
    }
)

if result["valid"]:
    print("Project is valid!")
else:
    print(f"Errors: {result['errors']}")
```

## Configuration

### Environment Variables

| Variable             | Description                  | Required           |
| -------------------- | ---------------------------- | ------------------ |
| `COOLIFY_URL`        | Coolify server URL           | For Coolify deploy |
| `COOLIFY_API_KEY`    | Coolify API key              | For Coolify deploy |
| `GITHUB_TOKEN`       | GitHub personal access token | For GitHub push    |
| `GITHUB_USER`        | GitHub username              | For GitHub push    |
| `VERCEL_TOKEN`       | Vercel CLI token             | For Vercel deploy  |
| `SCRAPE_USER_AGENT`  | User agent for scraping      | No                 |
| `SCRAPE_TIMEOUT`     | Timeout in seconds           | No (default: 30)   |
| `SCRAPE_MAX_RETRIES` | Maximum retry attempts       | No (default: 3)    |
| `RESPECT_ROBOTS_TXT` | Respect robots.txt           | No (default: true) |
| `ALLOWED_DOMAINS`    | Comma-separated allowlist    | No                 |

### robots.txt Handling

By default, the tool checks robots.txt before scraping. To disable:

```bash
export RESPECT_ROBOTS_TXT=false
```

Or allow specific domains:

```bash
export ALLOWED_DOMAINS=example.com,another-domain.com
```

## Security Considerations

1. **Secrets**: Never store secrets in the frontend output. Secrets should only come from environment variables or a vault.

2. **robots.txt**: The tool respects robots.txt by default. You can disable this with `RESPECT_ROBOTS_TXT=false` (not recommended).

3. **Rate Limiting**: External calls have timeouts and retries. Circuit breakers prevent cascade failures.

4. **Input Validation**: URLs are validated before processing. Domain allowlists prevent unauthorized scraping.

## Output Structure

All outputs follow this structure:

```
runs/
└── {run_id}/
    ├── report.json              # Final report
    ├── {project_name}/
    │   ├── snapshot/
    │   │   ├── index.html       # Captured HTML
    │   │   ├── metadata.json    # Page metadata
    │   │   ├── style_0.css      # Stylesheets
    │   │   └── assets/          # Downloaded assets
    │   └── react-app/           # Vite React app
    │       ├── package.json
    │       ├── vite.config.ts
    │       ├── index.html
    │       ├── src/
    │       │   ├── main.tsx
    │       │   ├── App.tsx
    │       │   └── index.css
    │       └── public/
    │           └── snapshot/    # Static snapshot files
    └── logs/                    # Execution logs
```

## Error Handling

The tool provides clean failure modes:

- **Permission Errors**: Domain not in allowlist, robots.txt disallows access
- **Network Errors**: Timeouts, connection failures (with retries)
- **Validation Errors**: Missing required files, invalid configurations
- **Build Errors**: Failed npm install or build

All errors are captured in the `errors` array in the result.

## Best Practices

1. **Use Version Control**: Always push to GitHub before deploying to Vercel/Coolify

2. **Validate First**: Run `validate_project` before deploying

3. **Set Timeouts**: Use appropriate timeouts for slow sites

4. **Check robots.txt**: Respect website crawling policies

5. **Monitor Usage**: Track API calls and resource usage

## Limitations

- JavaScript-heavy sites may not render correctly
- Authentication-protected content cannot be scraped
- Very large sites may timeout
- Dynamic content loaded after network idle won't be captured

## See Also

- [Playwright Documentation](https://playwright.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Vercel CLI](https://vercel.com/docs/cli)
- [Coolify Documentation](https://coolify.io/docs/)
