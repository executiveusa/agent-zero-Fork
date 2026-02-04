/**
 * LiteLLM Integration for Agent Zero Dashboard
 * Enables switching between different LLM providers
 * Supports: OpenAI, Anthropic, Azure, Cohere, Replicate, etc.
 */

interface LiteLLMConfig {
  model: string;
  api_key?: string;
  api_base?: string;
  temperature?: number;
  max_tokens?: number;
}

interface LLMProvider {
  name: string;
  models: string[];
  apiKeyEnv: string;
  baseUrl?: string;
}

// Supported LLM Providers
export const LLM_PROVIDERS: Record<string, LLMProvider> = {
  openai: {
    name: 'OpenAI',
    models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    apiKeyEnv: 'OPENAI_API_KEY',
  },
  anthropic: {
    name: 'Anthropic',
    models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
    apiKeyEnv: 'ANTHROPIC_API_KEY',
  },
  azure: {
    name: 'Azure OpenAI',
    models: ['azure/gpt-4', 'azure/gpt-35-turbo'],
    apiKeyEnv: 'AZURE_API_KEY',
    baseUrl: process.env.AZURE_API_BASE,
  },
  cohere: {
    name: 'Cohere',
    models: ['command-r', 'command-r-plus'],
    apiKeyEnv: 'COHERE_API_KEY',
  },
  replicate: {
    name: 'Replicate',
    models: ['replicate/llama-2-70b', 'replicate/mixtral-8x7b'],
    apiKeyEnv: 'REPLICATE_API_KEY',
  },
  huggingface: {
    name: 'HuggingFace',
    models: ['huggingface/mistral-7b', 'huggingface/llama-2'],
    apiKeyEnv: 'HUGGINGFACE_API_KEY',
  },
};

/**
 * Create LiteLLM request configuration
 */
export function createLiteLLMRequest(
  model: string,
  prompt: string,
  options: Partial<LiteLLMConfig> = {}
): LiteLLMConfig {
  return {
    model,
    temperature: options.temperature ?? 0.7,
    max_tokens: options.max_tokens ?? 2000,
    api_key: options.api_key,
    api_base: options.api_base,
  };
}

/**
 * Call LiteLLM proxy (requires LiteLLM server running)
 */
export async function callLiteLLM(
  config: LiteLLMConfig,
  messages: Array<{ role: string; content: string }>
) {
  const litellmUrl = process.env.LITELLM_BASE_URL || 'http://localhost:8000';

  const response = await fetch(`${litellmUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${config.api_key || process.env.LITELLM_MASTER_KEY}`,
    },
    body: JSON.stringify({
      model: config.model,
      messages,
      temperature: config.temperature,
      max_tokens: config.max_tokens,
    }),
  });

  if (!response.ok) {
    throw new Error(`LiteLLM API error: ${response.status}`);
  }

  return await response.json();
}

/**
 * Get available models from all configured providers
 */
export function getAvailableModels(): Array<{ provider: string; model: string }> {
  const models: Array<{ provider: string; model: string }> = [];

  for (const [providerId, provider] of Object.entries(LLM_PROVIDERS)) {
    // Check if API key exists for this provider
    const apiKey = process.env[provider.apiKeyEnv];
    if (apiKey) {
      provider.models.forEach(model => {
        models.push({ provider: provider.name, model });
      });
    }
  }

  return models;
}

/**
 * Switch LLM model dynamically
 */
export async function switchLLM(newModel: string): Promise<boolean> {
  try {
    // Validate model exists
    const allModels = getAvailableModels();
    const modelExists = allModels.some(m => m.model === newModel);

    if (!modelExists) {
      console.error(`Model ${newModel} not available`);
      return false;
    }

    // Store in session/state
    // TODO: Implement state management (Zustand)
    console.log(`Switched to model: ${newModel}`);
    return true;
  } catch (error) {
    console.error('Failed to switch LLM:', error);
    return false;
  }
}

/**
 * Example: LiteLLM Config File Generator
 * Creates config.yaml for LiteLLM proxy server
 */
export function generateLiteLLMConfig(): string {
  return `
# LiteLLM Proxy Configuration
model_list:
  # OpenAI
  - model_name: gpt-4
    litellm_params:
      model: gpt-4
      api_key: \${OPENAI_API_KEY}

  - model_name: gpt-3.5-turbo
    litellm_params:
      model: gpt-3.5-turbo
      api_key: \${OPENAI_API_KEY}

  # Anthropic
  - model_name: claude-3-opus
    litellm_params:
      model: claude-3-opus-20240229
      api_key: \${ANTHROPIC_API_KEY}

  - model_name: claude-3-sonnet
    litellm_params:
      model: claude-3-sonnet-20240229
      api_key: \${ANTHROPIC_API_KEY}

  # Azure OpenAI
  - model_name: azure-gpt-4
    litellm_params:
      model: azure/gpt-4
      api_key: \${AZURE_API_KEY}
      api_base: \${AZURE_API_BASE}
      api_version: "2024-02-01"

  # Cohere
  - model_name: command-r
    litellm_params:
      model: command-r
      api_key: \${COHERE_API_KEY}

  # Replicate
  - model_name: llama-2-70b
    litellm_params:
      model: replicate/meta/llama-2-70b-chat
      api_key: \${REPLICATE_API_KEY}

# General settings
general_settings:
  master_key: "\${LITELLM_MASTER_KEY}"
  database_url: "sqlite:///litellm.db"
`.trim();
}

/**
 * Environment variable template for LiteLLM
 */
export const LITELLM_ENV_TEMPLATE = `
# LiteLLM Configuration
LITELLM_BASE_URL=http://localhost:8000
LITELLM_MASTER_KEY=sk-your-master-key-here

# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Azure OpenAI
AZURE_API_KEY=...
AZURE_API_BASE=https://your-resource.openai.azure.com
AZURE_API_VERSION=2024-02-01

# Cohere
COHERE_API_KEY=...

# Replicate
REPLICATE_API_KEY=...

# HuggingFace
HUGGINGFACE_API_KEY=hf_...
`.trim();
