import { NextRequest, NextResponse } from 'next/server';
import { proxyToAgentZero } from '@/lib/proxy';

/**
 * GET /api/az/health
 * Health check endpoint
 * Proxies to Agent Zero backend to verify connectivity
 */
export async function GET(request: NextRequest) {
  try {
    // Attempt to proxy a simple request to verify backend connectivity
    const result = await proxyToAgentZero('/csrf_token', {
      method: 'GET',
      useApiKey: false,
    });

    if (result.error) {
      return NextResponse.json(
        { 
          status: 'error',
          backend: 'disconnected',
          error: result.error.error,
          details: result.error.details
        },
        { status: 503 }
      );
    }

    return NextResponse.json({
      status: 'ok',
      backend: 'connected',
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    return NextResponse.json(
      { 
        status: 'error',
        backend: 'error',
        error: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
