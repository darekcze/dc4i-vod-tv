import {accessSync, constants} from 'node:fs';
import {delimiter, join} from 'node:path';

// Resolve before starting servers. Never change the browser sandbox policy here.
export function browserPath() {
  const candidates = process.env.CHROME_PATH ? [process.env.CHROME_PATH] : [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    ...(process.env.PATH || '').split(delimiter).filter(Boolean).flatMap(dir =>
      ['chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable'].map(name => join(dir, name)))
  ];
  for (const candidate of candidates) {
    try { accessSync(candidate, constants.X_OK); return candidate; } catch {}
  }
  throw new Error('Chrome/Chromium unavailable; set CHROME_PATH to an executable browser path.');
}
