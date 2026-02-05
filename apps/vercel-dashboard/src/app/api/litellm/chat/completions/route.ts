import { NextRequest, NextResponse } from 'next/server';

/**
 * LiteLLM Virtual Keys API Proxy
 * Routes LLM requests through a unified interface
 * Supports: OpenAI, Anthropic, Google AI
 */

const API_KEYS = {
  openai: process.env.OPENAI_API_KEY,
  anthropic: process.env.ANTHROPIC_API_KEY,
  anthropic_2: process.env.ANTHROPIC_API_KEY_2,
  google: process.env.GOOGLE_API_KEY,
};

const LITELLM_MASTER_KEY = process.env.LITELLM_MASTER_KEY || 'sk-litellm-master-key';

// Model routing configuration
const MODEL_ROUTES: Record<string, { provider: string; model: string; key: string }> = {
  'gpt-4': { provider: 'openai', model: 'gpt-4', key: 'openai' },
  'gpt-4-turbo': { provider: 'openai', model: 'gpt-4-turbo-preview', key: 'openai' },
  'gpt-3.5-turbo': { provider: 'openai', model: 'gpt-3.5-turbo', key: 'openai' },
  'claude-3-opus': { provider: 'anthropic', model: 'claude-3-opus-20240229', key: 'anthropic' },
  'claude-3-sonnet': { provider: 'anthropic', model: 'claude-3-sonnet-20240229', key: 'anthropic' },
  'claude-3-haiku': { provider: 'anthropic', model: 'claude-3-haiku-20240307', key: 'anthropic' },
  'gemini-pro': { provider: 'google', model: 'gemini-pro', key: 'google' },
};

/**
 * Verify LiteLLM master key
 */
function verifyMasterKey(request: NextRequest): boolean {
  const authHeader = request.headers.get('authorization');
  if (!authHeader) return false;
  
  const token = authHeader.replace('Bearer ', '');
  return token === LITELLM_MASTER_KEY;
}

/**
 * POST /api/litellm/chat/completions
 * OpenAI-compatible chat completions endpoint
 */
export async function POST(request: NextRequest) {
  try {
    // Verify authentication
    if (!verifyMasterKey(request)) {
      return NextResponse.json(
        { error: 'Unauthorized. Invalid LiteLLM master key.' },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { model, messages, stream = false, ...rest } = body;

    // Route to appropriate provider
    const route = MODEL_ROUTES[model];
    if (!route) {
      return NextResponse.json(
        { error: `Model '${model}' not found. Available models: ${Object.keys(MODEL_ROUTES).join(', ')}` },
        { status: 400 }
      );
    }

    const apiKey = API_KEYS[route.key as keyof typeof API_KEYS];
    if (!apiKey) {
      return NextResponse.json(
        { error: `API key not configured for provider: ${route.provider}` },
        { status: 500 }
      );
    }

    // Forward to appropriate provider
    if (route.provider === 'openai') {
      return await forwardToOpenAI(route.model, messages, apiKey, stream, rest);
    } else if (route.provider === 'anthropic') {
      return await forwardToAnthropic(route.model, messages, apiKey, stream, rest);
    } else if (route.provider === 'google') {
      return await forwardToGoogle(route.model, messages, apiKey, stream, rest);
    }

    return NextResponse.json({ error: 'Provider not implemented' }, { status: 501 });

  } catch (error: any) {
    console.error('LiteLLM proxy error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * Forward request to OpenAI
 */
async function forwardToOpenAI(
  model: string,
  messages: any[],
  apiKey: string,
  stream: boolean,
  rest: any
) {
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages,
      stream,
      ...rest,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`OpenAI API error: ${error}`);
  }

  if (stream) {
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  }

  const data = await response.json();
  return NextResponse.json(data);
}

/**
 * Forward request to Anthropic
 */
async function forwardToAnthropic(
  model: string,
  messages: any[],
  apiKey: string,
  stream: boolean,
  rest: any
) {
  // Convert OpenAI format to Anthropic format
  const systemMessage = messages.find(m => m.role === 'system');
  const conversationMessages = messages.filter(m => m.role !== 'system');

  const anthropicBody: any = {
    model,
    messages: conversationMessages,
    max_tokens: rest.max_tokens || 4096,
    stream,
  };

  if (systemMessage) {
    anthropicBody.system = systemMessage.content;
  }

  if (rest.temperature !== undefined) {
    anthropicBody.temperature = rest.temperature;
  }

  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify(anthropicBody),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Anthropic API error: ${error}`);
  }

  if (stream) {
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  }

  const data = await response.json();
  
  // Convert Anthropic format to OpenAI format
  return NextResponse.json({
    id: data.id,
    object: 'chat.completion',
    created: Math.floor(Date.now() / 1000),
    model,
    choices: [
      {
        index: 0,
        message: {
          role: 'assistant',
          content: data.content[0].text,
        },
        finish_reason: data.stop_reason === 'end_turn' ? 'stop' : data.stop_reason,
      },
    ],
    usage: {
      prompt_tokens: data.usage.input_tokens,
      completion_tokens: data.usage.output_tokens,
      total_tokens: data.usage.input_tokens + data.usage.output_tokens,
    },
  });
}

/**
 * Forward request to Google AI
 */
async function forwardToGoogle(
  model: string,
  messages: any[],
  apiKey: string,
  stream: boolean,
  rest: any
) {
  // Convert OpenAI format to Google AI format
  const contents = messages.map(msg => ({
    role: msg.role === 'assistant' ? 'model' : 'user',
    parts: [{ text: msg.content }],
  }));

  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents,
        generationConfig: {
          temperature: rest.temperature || 0.7,
          maxOutputTokens: rest.max_tokens || 2048,
        },
      }),
    }
  );

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Google AI error: ${error}`);
  }

  const data = await response.json();

  // Convert Google AI format to OpenAI format
  return NextResponse.json({
    id: `google-${Date.now()}`,
    object: 'chat.completion',
    created: Math.floor(Date.now() / 1000),
    model,
    choices: [
      {
        index: 0,
        message: {
          role: 'assistant',
          content: data.candidates[0].content.parts[0].text,
        },
        finish_reason: 'stop',
      },
    ],
    usage: {
      prompt_tokens: 0,
      completion_tokens: 0,
      total_tokens: 0,
    },
  });
}

/**
 * GET /api/litellm/models
 * List available models
 */
export async function GET(request: NextRequest) {
  if (!verifyMasterKey(request)) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  const models = Object.entries(MODEL_ROUTES).map(([id, config]) => ({
    id,
    object: 'model',
    created: Date.now(),
    owned_by: config.provider,
    provider: config.provider,
    actual_model: config.model,
  }));

  return NextResponse.json({
    object: 'list',
    data: models,
  });
}
