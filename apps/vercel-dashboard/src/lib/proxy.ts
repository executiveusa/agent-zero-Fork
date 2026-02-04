/**
 * BFF Proxy Utility - Server-side communication with Agent Zero backend
 * Handles API key injection, CSRF tokens, and session management
 * CRITICAL: Never expose AZ_API_KEY to the browser
 */

import { ApiError, ApiResponse } from '@/types';

// Backend configuration
const AZ_BASE_URL = process.env.AZ_BASE_URL || 'http://localhost:50001';
const AZ_API_KEY = process.env.AZ_API_KEY || '';
const AZ_AUTH_LOGIN = process.env.AZ_AUTH_LOGIN;
const AZ_AUTH_PASSWORD = process.env.AZ_AUTH_PASSWORD;

// Session storage (in-memory for now, use Redis in production)
const sessionStore = new Map<string, {
  cookies: Record<string, string>;
  csrfToken: string;
  lastUsed: Date;
}>();

interface ProxyOptions {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
  useApiKey?: boolean; // Use X-API-KEY instead of session
  sessionId?: string; // User session ID for backend session storage
}

/**
 * Proxy a request to Agent Zero backend
 */
export async function proxyToAgentZero(
  endpoint: string,
  options: ProxyOptions = {}
): Promise<ApiResponse> {
  const {
    method = 'POST',
    body,
    headers = {},
    useApiKey = false,
    sessionId,
  } = options;

  try {
    const url = `${AZ_BASE_URL}${endpoint}`;
    const fetchHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    };

    // Mode A: API Key for /api_* endpoints
    if (useApiKey) {
      fetchHeaders['X-API-KEY'] = AZ_API_KEY;
    }
    // Mode B: Session + CSRF for authenticated endpoints
    else if (sessionId) {
      const session = await getOrCreateBackendSession(sessionId);
      
      // Add session cookies
      if (session.cookies) {
        const cookieHeader = Object.entries(session.cookies)
          .map(([key, value]) => `${key}=${value}`)
          .join('; ');
        fetchHeaders['Cookie'] = cookieHeader;
      }

      // Add CSRF token
      if (session.csrfToken) {
        fetchHeaders['X-CSRF-Token'] = session.csrfToken;
      }
    }

    const response = await fetch(url, {
      method,
      headers: fetchHeaders,
      body: body ? JSON.stringify(body) : undefined,
    });

    // Handle redirects to /login (session expired)
    if (response.status === 302 && sessionId) {
      // Re-login and retry
      await refreshBackendSession(sessionId);
      return proxyToAgentZero(endpoint, options);
    }

    // Handle CSRF errors
    if (response.status === 403 && sessionId) {
      // Fetch new CSRF token and retry
      await refreshBackendSession(sessionId);
      return proxyToAgentZero(endpoint, options);
    }

    if (!response.ok) {
      const errorText = await response.text();
      return {
        error: {
          error: `HTTP ${response.status}`,
          details: errorText,
          status: response.status,
        },
      };
    }

    const contentType = response.headers.get('content-type');
    
    // Handle JSON responses
    if (contentType?.includes('application/json')) {
      const data = await response.json();
      return { data };
    }

    // Handle file/image responses
    if (contentType?.includes('image') || endpoint.includes('/image_get')) {
      const blob = await response.blob();
      return { data: blob };
    }

    // Handle other responses
    const text = await response.text();
    return { data: text };

  } catch (error) {
    console.error('Proxy error:', error);
    return {
      error: {
        error: 'Network Error',
        details: error instanceof Error ? error.message : 'Unknown error',
        status: 500,
      },
    };
  }
}

/**
 * Get or create backend session for a dashboard user
 */
async function getOrCreateBackendSession(sessionId: string) {
  // Check if session exists and is recent
  const existing = sessionStore.get(sessionId);
  if (existing && (Date.now() - existing.lastUsed.getTime()) < 3600000) { // 1 hour
    existing.lastUsed = new Date();
    return existing;
  }

  // Create new backend session
  return await createBackendSession(sessionId);
}

/**
 * Create new backend session via /login
 */
async function createBackendSession(sessionId: string) {
  try {
    // First, get CSRF token
    const csrfResponse = await fetch(`${AZ_BASE_URL}/csrf_token`);
    const csrfData = await csrfResponse.json();
    const csrfToken = csrfData.token;

    // Extract session cookie from CSRF response
    const setCookieHeader = csrfResponse.headers.get('set-cookie');
    const cookies: Record<string, string> = {};
    
    if (setCookieHeader) {
      setCookieHeader.split(',').forEach(cookie => {
        const [nameValue] = cookie.split(';');
        const [name, value] = nameValue.split('=');
        if (name && value) {
          cookies [name.trim()] = value.trim();
        }
      });
    }

    // If credentials are provided, login to backend
    if (AZ_AUTH_LOGIN && AZ_AUTH_PASSWORD) {
      const formData = new URLSearchParams();
      formData.append('username', AZ_AUTH_LOGIN);
      formData.append('password', AZ_AUTH_PASSWORD);

      const loginResponse = await fetch(`${AZ_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Cookie': Object.entries(cookies).map(([k, v]) => `${k}=${v}`).join('; '),
        },
        body: formData,
        redirect: 'manual', // Don't follow redirects
      });

      // Extract new cookies from login response
      const loginSetCookie = loginResponse.headers.get('set-cookie');
      if (loginSetCookie) {
        loginSetCookie.split(',').forEach(cookie => {
          const [nameValue] = cookie.split(';');
          const [name, value] = nameValue.split('=');
          if (name && value) {
            cookies[name.trim()] = value.trim();
          }
        });
      }
    }

    const session = {
      cookies,
      csrfToken,
      lastUsed: new Date(),
    };

    sessionStore.set(sessionId, session);
    return session;

  } catch (error) {
    console.error('Failed to create backend session:', error);
    // Return empty session
    return {
      cookies: {},
      csrfToken: '',
      lastUsed: new Date(),
    };
  }
}

/**
 * Refresh backend session (re-login)
 */
async function refreshBackendSession(sessionId: string) {
  sessionStore.delete(sessionId);
  return await createBackendSession(sessionId);
}

/**
 * Redact sensitive data from responses
 */
export function redactSecrets(data: any): any {
  if (!data || typeof data !== 'object') return data;

  const sensitiveKeys = [
    'token', 'key', 'secret', 'password', 'credential',
    'api_key', 'auth', 'csrf', 'session',
  ];

  const redacted = Array.isArray(data) ? [...data] : { ...data };

  for (const key in redacted) {
    if (sensitiveKeys.some(sk => key.toLowerCase().includes(sk))) {
      redacted[key] = '[REDACTED]';
    } else if (typeof redacted[key] === 'object') {
      redacted[key] = redactSecrets(redacted[key]);
    }
  }

  return redacted;
}

/**
 * Helper: Check if endpoint should use API key mode
 */
export function shouldUseApiKey(endpoint: string): boolean {
  const apiKeyEndpoints = [
    '/api_message',
    '/api_log_get',
    '/api_files_get',
    '/api_reset_chat',
    '/api_terminate_chat',
  ];
  
  return apiKeyEndpoints.some(e => endpoint.startsWith(e));
}
