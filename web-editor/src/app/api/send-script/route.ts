import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { NextApiRequest } from 'next';


export async function GET(req: NextApiRequest) {
  const name = req.nextUrl.searchParams.get("s")
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
