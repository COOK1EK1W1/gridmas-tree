import prisma from '@/util/prisma';
import { NextRequest, NextResponse } from 'next/server';


export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  
  // Get pattern IDs from query parameter
  const idsParam = searchParams.get('ids');
  
  if (!idsParam) {
    return NextResponse.json({ error: 'Missing ids parameter' }, { status: 400 });
  }
  
  const patternIds = idsParam.split(',').map(id => id.trim()).filter(id => id.length > 0);
  
  if (patternIds.length === 0) {
    return NextResponse.json({ error: 'No valid pattern IDs provided' }, { status: 400 });
  }
  
  if (patternIds.length === 1) {
    // Single pattern ID - return single object
    const res = await prisma.pattern.findFirst({
      where: {
        id: patternIds[0]
      }
    })
    if (!res) {
      return NextResponse.json({ error: 'Pattern not found' }, { status: 404 });
    }

    return NextResponse.json(res, {
      status: 200,
    });
  } else {
    // Multiple pattern IDs - return array
    const res = await prisma.pattern.findMany({
      where: {
        id: {
          in: patternIds
        }
      }
    });

    return NextResponse.json(res, {
      status: 200,
    });
  }
} 
