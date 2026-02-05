import { NextRequest, NextResponse } from 'next/server';

/**
 * GET /api/litellm/models
 * List all available models across providers
 */

const LITELLM_MASTER_KEY = process.env.LITELLM_MASTER_KEY || 'sk-litellm-master-key';

function verifyMasterKey(request: NextRequest): boolean {
  const authHeader = request.headers.get('authorization');
  if (!authHeader) return false;
  
  const token = authHeader.replace('Bearer ', '');
  return token === LITELLM_MASTER_KEY;
}

export async function GET(request: NextRequest) {
  if (!verifyMasterKey(request)) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  const models = [
    {
      id: 'gpt-4',
      object: 'model',
      created: 1687882411,
      owned_by: 'openai',
      provider: 'openai',
      actual_model: 'gpt-4',
    },
    {
      id: 'gpt-4-turbo',
      object: 'model',
      created: 1687882411,
      owned_by: 'openai',
      provider: 'openai',
      actual_model: 'gpt-4-turbo-preview',
    },
    {
      id: 'gpt-3.5-turbo',
      object: 'model',
      created: 1687882411,
      owned_by: 'openai',
      provider: 'openai',
      actual_model: 'gpt-3.5-turbo',
    },
    {
      id: 'claude-3-opus',
      object: 'model',
      created: 1687882411,
      owned_by: 'anthropic',
      provider: 'anthropic',
      actual_model: 'claude-3-opus-20240229',
    },
    {
      id: 'claude-3-sonnet',
      object: 'model',
      created: 1687882411,
      owned_by: 'anthropic',
      provider: 'anthropic',
      actual_model: 'claude-3-sonnet-20240229',
    },
    {
      id: 'claude-3-haiku',
      object: 'model',
      created: 1687882411,
      owned_by: 'anthropic',
      provider: 'anthropic',
      actual_model: 'claude-3-haiku-20240307',
    },
    {
      id: 'gemini-pro',
      object: 'model',
      created: 1687882411,
      owned_by: 'google',
      provider: 'google',
      actual_model: 'gemini-pro',
    },
  ];

  return NextResponse.json({
    object: 'list',
    data: models,
  });
}
