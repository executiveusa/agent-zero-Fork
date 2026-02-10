# Composio Toolkit Quick Reference

## Action Slug Format
Actions follow the pattern: `APP_ACTION_NAME`
Examples: `GITHUB_CREATE_ISSUE`, `GMAIL_SEND_EMAIL`, `SLACK_SEND_MESSAGE`

## Top Integrations & Common Actions

### Development & Code
| App | Example Actions |
|-----|----------------|
| GITHUB | `GITHUB_CREATE_ISSUE`, `GITHUB_CREATE_PULL_REQUEST`, `GITHUB_LIST_REPOS`, `GITHUB_STAR_REPO` |
| GITLAB | `GITLAB_CREATE_ISSUE`, `GITLAB_CREATE_MERGE_REQUEST` |
| LINEAR | `LINEAR_CREATE_ISSUE`, `LINEAR_UPDATE_ISSUE`, `LINEAR_LIST_PROJECTS` |
| JIRA | `JIRA_CREATE_ISSUE`, `JIRA_GET_ISSUE`, `JIRA_TRANSITION_ISSUE` |

### Communication
| App | Example Actions |
|-----|----------------|
| GMAIL | `GMAIL_SEND_EMAIL`, `GMAIL_FETCH_EMAILS`, `GMAIL_CREATE_DRAFT` |
| SLACK | `SLACK_SEND_MESSAGE`, `SLACK_LIST_CHANNELS`, `SLACK_CREATE_CHANNEL` |
| DISCORD | `DISCORD_SEND_MESSAGE`, `DISCORD_CREATE_CHANNEL` |
| TWILIO | `TWILIO_SEND_SMS`, `TWILIO_MAKE_CALL` |
| MICROSOFT_TEAMS | `MICROSOFT_TEAMS_SEND_MESSAGE` |

### Productivity
| App | Example Actions |
|-----|----------------|
| GOOGLE_CALENDAR | `GOOGLE_CALENDAR_CREATE_EVENT`, `GOOGLE_CALENDAR_LIST_EVENTS` |
| GOOGLE_SHEETS | `GOOGLE_SHEETS_ADD_ROW`, `GOOGLE_SHEETS_GET_SHEET_DATA` |
| GOOGLE_DRIVE | `GOOGLE_DRIVE_UPLOAD_FILE`, `GOOGLE_DRIVE_LIST_FILES` |
| NOTION | `NOTION_CREATE_PAGE`, `NOTION_QUERY_DATABASE`, `NOTION_UPDATE_PAGE` |
| AIRTABLE | `AIRTABLE_CREATE_RECORD`, `AIRTABLE_LIST_RECORDS` |
| TRELLO | `TRELLO_CREATE_CARD`, `TRELLO_MOVE_CARD` |
| ASANA | `ASANA_CREATE_TASK`, `ASANA_UPDATE_TASK` |

### CRM & Sales
| App | Example Actions |
|-----|----------------|
| HUBSPOT | `HUBSPOT_CREATE_CONTACT`, `HUBSPOT_CREATE_DEAL`, `HUBSPOT_LIST_CONTACTS` |
| SALESFORCE | `SALESFORCE_CREATE_LEAD`, `SALESFORCE_CREATE_OPPORTUNITY` |
| PIPEDRIVE | `PIPEDRIVE_CREATE_DEAL`, `PIPEDRIVE_CREATE_PERSON` |

### Payments & E-Commerce
| App | Example Actions |
|-----|----------------|
| STRIPE | `STRIPE_CREATE_INVOICE`, `STRIPE_CREATE_CUSTOMER`, `STRIPE_LIST_PAYMENTS` |
| SHOPIFY | `SHOPIFY_CREATE_PRODUCT`, `SHOPIFY_LIST_ORDERS` |

### Marketing
| App | Example Actions |
|-----|----------------|
| MAILCHIMP | `MAILCHIMP_ADD_SUBSCRIBER`, `MAILCHIMP_SEND_CAMPAIGN` |
| SENDGRID | `SENDGRID_SEND_EMAIL` |

### Cloud Storage
| App | Example Actions |
|-----|----------------|
| DROPBOX | `DROPBOX_UPLOAD_FILE`, `DROPBOX_LIST_FILES` |
| ONEDRIVE | `ONEDRIVE_UPLOAD_FILE`, `ONEDRIVE_LIST_FILES` |
| BOX | `BOX_UPLOAD_FILE`, `BOX_LIST_FILES` |

### Databases
| App | Example Actions |
|-----|----------------|
| POSTGRESQL | `POSTGRESQL_RUN_QUERY` |
| MYSQL | `MYSQL_RUN_QUERY` |
| MONGODB | `MONGODB_INSERT_DOCUMENT`, `MONGODB_FIND_DOCUMENTS` |

### Support
| App | Example Actions |
|-----|----------------|
| ZENDESK | `ZENDESK_CREATE_TICKET`, `ZENDESK_UPDATE_TICKET` |
| INTERCOM | `INTERCOM_SEND_MESSAGE`, `INTERCOM_CREATE_CONTACT` |
| FRESHDESK | `FRESHDESK_CREATE_TICKET` |

### Design & Content
| App | Example Actions |
|-----|----------------|
| FIGMA | `FIGMA_GET_FILE`, `FIGMA_LIST_PROJECTS` |
| WORDPRESS | `WORDPRESS_CREATE_POST`, `WORDPRESS_UPDATE_POST` |

### Meetings
| App | Example Actions |
|-----|----------------|
| ZOOM | `ZOOM_CREATE_MEETING`, `ZOOM_LIST_MEETINGS` |
| GOOGLE_MEET | `GOOGLE_MEET_CREATE_MEETING` |

## Authentication
Composio handles OAuth flows automatically for connected apps.
Auth is managed centrally — no need for per-app API keys in your code.

## Tips
- **Don't memorize slugs** — use `composio_tool:search` with natural language
- **Check params first** — use `composio_tool:schema` before calling unfamiliar actions
- **Entity ID** — defaults to "default"; use specific IDs for multi-tenant scenarios
- **Error handling** — failed actions return error details in the response message
- **Rate limits** — free tier allows 20,000 API calls per month
