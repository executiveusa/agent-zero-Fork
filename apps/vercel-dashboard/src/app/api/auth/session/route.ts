import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const res = NextResponse.json({ status: 'ok' });
  return res;
}

export async function GET(request: NextRequest) {
  return NextResponse.json({ authenticated: false });
}
