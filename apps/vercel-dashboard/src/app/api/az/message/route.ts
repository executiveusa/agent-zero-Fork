import { NextRequest, NextResponse } from 'next/server';
import { proxyToAgentZero } from '@/lib/proxy';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const sessionId = request.cookies.get('session-id')?.value || 'default';

    const result = await proxyToAgentZero('/api_message', {
      method: 'POST',
      body,
      sessionId,
      useApiKey: true,
    });

    if (result.error) {
      return NextResponse.json({ error: result.error.error }, { status: result.error.status });
    }

    return NextResponse.json(result.data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
