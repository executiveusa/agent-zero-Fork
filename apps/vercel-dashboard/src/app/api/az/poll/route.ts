import { NextRequest, NextResponse } from 'next/server';
import { proxyToAgentZero } from '@/lib/proxy';
import { PollResponse } from '@/types';

/**
 * POST /api/az/poll
 * Proxy to Agent Zero /poll endpoint
 * Returns real-time dashboard state
 */
export async function POST(request: NextRequest) {
  try {
    // Get session ID from request (for now, use a default)
    // TODO: Replace with NextAuth session after authentication is implemented
    const sessionId = request.cookies.get('session-id')?.value || 'default-session';

    // Proxy to backend /poll endpoint
    const result = await proxyToAgentZero('/poll', {
      method: 'POST',
      sessionId,
      useApiKey: false, // Use session-based auth for /poll
    });

    if (result.error) {
      return NextResponse.json(
        { error: result.error.error, details: result.error.details },
        { status: result.error.status }
      );
    }

    // Return poll data
    const pollData = result.data as PollResponse;
    return NextResponse.json(pollData);

  } catch (error) {
    console.error('Poll route error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
