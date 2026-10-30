import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { createReadStream } from 'fs';
import archiver from 'archiver';

export const dynamic = 'force-static'

class MissingCoreFilesError extends Error {
  constructor(files: string[]) {
    super(`Missing core files: ${files.join(', ')}`);
  }
}

export async function GET() {
  try {
    // List of core Python files that need to be included
    const coreFiles = [
      "util.py",
      "colors.py",
      "tree.csv",
      "gridmas.py",
      "fixture.py",
      "pixel_driver.py",
      "web_driver.py",
      "legacy_display.py",
      "pattern_manager.py",
      "particle_system.py",
      "fizzle.py",
      "wipe.py",
      "attribute.py",
      "geometry.py",
      "music.py"
    ];

    const backendPath = path.join(process.cwd(), '../backend');

    // Create a zip archive
    const archive = archiver('zip', {
      zlib: { level: 9 } // Maximum compression
    });

    const missingFiles: string[] = [];

    // Add each file to the archive
    for (const fileName of coreFiles) {
      let filePath;
      if (fileName == "tree.csv") {
        filePath = path.join(process.cwd(), '../point-clouds/grid-2025.csv');
      } else {
        filePath = path.join(backendPath, fileName);
      }

      // This route is prerendered, so a missing file must fail the build rather than ship a broken zip
      if (!fs.existsSync(filePath)) {
        missingFiles.push(filePath);
        continue;
      }

      const fileStream = createReadStream(filePath);
      archive.append(fileStream, { name: fileName });
    }

    if (missingFiles.length > 0) {
      throw new MissingCoreFilesError(missingFiles);
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
    if (error instanceof MissingCoreFilesError) throw error;
    console.error('Error creating zip archive:', error);
    return new NextResponse('Error creating zip archive', { status: 500 });
  }
}
