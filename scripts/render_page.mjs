#!/usr/bin/env node

import { chromium } from 'playwright';

function parseArgs(argv) {
  const options = {
    url: '',
    timeoutMs: 10000,
    waitSelectors: [],
  };

  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === '--url' && index + 1 < argv.length) {
      options.url = argv[index + 1];
      index += 1;
      continue;
    }
    if (value === '--timeout-ms' && index + 1 < argv.length) {
      options.timeoutMs = Number.parseInt(argv[index + 1], 10);
      index += 1;
      continue;
    }
    if (value === '--wait-selector' && index + 1 < argv.length) {
      options.waitSelectors.push(argv[index + 1]);
      index += 1;
    }
  }
  return options;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (!options.url) {
    throw new Error('url is required');
  }

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  let requestCount = 0;
  page.on('request', () => {
    requestCount += 1;
  });

  try {
    await page.goto(options.url, {
      waitUntil: 'domcontentloaded',
      timeout: options.timeoutMs,
    });

    try {
      await page.waitForLoadState('networkidle', { timeout: options.timeoutMs });
    } catch {
      // Keep the result if networkidle does not settle in time.
    }

    for (const selector of options.waitSelectors) {
      try {
        await page.waitForSelector(selector, { timeout: options.timeoutMs });
      } catch {
        // Selector wait is best-effort in the first browser slice.
      }
    }

    const finalUrl = page.url();
    const html = await page.content();
    const scriptHints = await page.evaluate(() => {
      const hints = [];
      const scriptCount = document.querySelectorAll('script').length;
      if (scriptCount > 0) {
        hints.push('script-tags-present');
      }
      if (document.querySelector('noscript')) {
        hints.push('noscript-present');
      }
      if (document.querySelector('#app, #root, [data-reactroot], [ng-app]')) {
        hints.push('spa-shell-detected');
      }
      return hints;
    });

    process.stdout.write(JSON.stringify({
      final_url: finalUrl,
      html,
      signals: {
        network_requests: requestCount,
        script_hints: scriptHints,
      },
    }));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
