import { NextRequest, NextResponse } from 'next/server';

/**
 * POST /api/az/chat
 * Agent Zero chat endpoint (fully serverless for Vercel)
 */

const AZ_API_KEY = process.env.AZ_API_KEY || 'az-api-key';
const AZ_AUTH_ENABLED = process.env.AZ_AUTH_ENABLED === 'true';
const LITELLM_BASE_URL = process.env.LITELLM_BASE_URL || 'https://agent-zero-fork.vercel.app/api/litellm';
const LITELLM_MASTER_KEY = process.env.LITELLM_MASTER_KEY || 'sk-litellm-master-key';

function verifyApiKey(request: NextRequest): boolean {
  if (!AZ_AUTH_ENABLED) return true;
  
  const authHeader = request.headers.get('authorization');
  if (!authHeader) return false;
  
  const token = authHeader.replace('Bearer ', '');
  return token === AZ_API_KEY;
}

async function callLiteLLM(model: string, messages: any[], options: any = {}) {
  const response = await fetch(`${LITELLM_BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${LITELLM_MASTER_KEY}`,
    },
    body: JSON.stringify({
      model,
      messages,
      ...options,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'LiteLLM API error');
  }

  return response.json();
}

export async function POST(request: NextRequest) {
  if (!verifyApiKey(request)) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  try {
    const body = await request.json();
    const { message, model = 'gpt-4', context = [], options = {} } = body;

    if (!message) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      );
    }

    // Build messages array from context + new message
    const messages = [
      ...context,
      { role: 'user', content: message },
    ];

    // Call LiteLLM proxy
    const completion = await callLiteLLM(model, messages, options);

    // Extract assistant response
    const assistantMessage = completion.choices[0]?.message?.content || '';

    return NextResponse.json({
      success: true,
      response: assistantMessage,
      model,
      usage: completion.usage,
    });
  } catch (error: any) {
    console.error('Agent Zero API error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * GET /api/az/chat
 * Health check endpoint
 */
export async function GET(request: NextRequest) {
  return NextResponse.json({
    status: 'ok',
    service: 'Agent Zero API',
    litellm_base_url: LITELLM_BASE_URL,
    auth_enabled: AZ_AUTH_ENABLED,
  });
}
