import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(req: NextRequest) {
  const name = req.nextUrl.searchParams.get("s")
  if (name === null) return
  const scriptPath = path.join(process.cwd(), '../backend', name);
  console.log(scriptPath)
  const fileContents = fs.readFileSync(scriptPath, 'utf-8');

  return new NextResponse(fileContents, {
    status: 200,
    headers: {
      'Content-Type': 'text/x-python',
      'Content-Disposition': `attachment; filename="${name}" `,
    },
  });
} 
