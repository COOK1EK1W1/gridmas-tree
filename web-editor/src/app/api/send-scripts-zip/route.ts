import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { createReadStream } from 'fs';
import { pipeline } from 'stream';
import { promisify } from 'util';
import archiver from 'archiver';

const pipelineAsync = promisify(pipeline);

export async function GET(req: NextRequest) {
  try {
    // List of core Python files that need to be included
    const coreFiles = [
      "util.py", 
      "colors.py", 
      "tree.csv", 
      "gridmas.py", 
      "tree.py", 
      "particle_system.py", 
      "fizzle.py", 
      "wipe.py", 
      "attribute.py", 
      "geometry.py"
    ];

    const backendPath = path.join(process.cwd(), '../backend');
    
    // Create a zip archive
    const archive = archiver('zip', {
      zlib: { level: 9 } // Maximum compression
    });

    // Add each file to the archive
    for (const fileName of coreFiles) {
      const filePath = path.join(backendPath, fileName);
      
      // Check if file exists before adding
      if (fs.existsSync(filePath)) {
        const fileStream = createReadStream(filePath);
        archive.append(fileStream, { name: fileName });
      } else {
        console.warn(`File not found: ${filePath}`);
      }
    }

    // Finalize the archive
    archive.finalize();

    // Set up response headers
    const headers = new Headers({
      'Content-Type': 'application/zip',
      'Content-Disposition': 'attachment; filename="core-scripts.zip"',
      'Cache-Control': 'no-cache'
    });

    // Create a readable stream from the archive
    const readable = new ReadableStream({
      start(controller) {
        archive.on('data', (chunk) => {
          controller.enqueue(chunk);
        });
        
        archive.on('end', () => {
          controller.close();
        });
        
        archive.on('error', (err) => {
          console.error('Archive error:', err);
          controller.error(err);
        });
      }
    });

    return new NextResponse(readable, {
      status: 200,
      headers
    });

  } catch (error) {
    console.error('Error creating zip archive:', error);
    return new NextResponse('Error creating zip archive', { status: 500 });
  }
}
