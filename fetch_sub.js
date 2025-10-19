// fetch_sub.js
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const https = require('https');
const zlib = require('zlib');

puppeteer.use(StealthPlugin());

(async () => {
  try {
    const browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor'
      ]
    });
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
    await page.setViewport({ width: 1920, height: 1080 });
    await page.goto('https://www.bsbb.cc/sub/index.php', { waitUntil: 'networkidle0', timeout: 30000 });

    // 模拟人类：随机延迟 + 滚动
    await page.evaluate(async () => {
      await new Promise(r => setTimeout(r, 2000 + Math.random() * 3000));
      window.scrollTo(0, Math.random() * 300);
      document.dispatchEvent(new MouseEvent('mousemove', { clientX: Math.random() * 1920, clientY: Math.random() * 1080 }));
    });

    // 等待延迟 + 潜在挑战（延长到 20s）
    await new Promise(r => setTimeout(r, 15000 + Math.random() * 5000));

    let finalUrl = page.url();
    console.log('Current URL after wait:', finalUrl);

    // 如果仍非 API，检查是否挑战页，解析 HTML
    if (!finalUrl.includes('/api/sub.php?t=')) {
      const html = await page.content();
      console.log('Detected challenge or delay page. Parsing HTML...');

      // Regex 提取 t= 和 __cf_chl_tk (Cloudflare 嵌入)
      const tMatch = html.match(/t=([a-f0-9]{32})/);
      const cfTkMatch = html.match(/__cf_chl_tk=([^&]+)/);
      if (tMatch && cfTkMatch) {
        const t = tMatch[1];
        const cfTk = cfTkMatch[1];
        finalUrl = `https://www.bsbb.cc/api/sub.php?t=${t}&__cf_chl_tk=${cfTk}`;
        console.log('Extracted: t=', t, ', cf_tk=', cfTk.substring(0, 20) + '...');
      } else {
        console.error('No t= or cf_tk found in HTML. Content preview:', html.substring(0, 200));
        await browser.close();
        process.exit(1);
      }
    }

    const cookies = await page.cookies();
    const cookieString = cookies.map(c => `${c.name}=${c.value}`).join('; ');
    console.log('Using', cookies.length, 'cookies for request.');

    await browser.close();

    // 请求最终 URL
    const req = https.request(finalUrl, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookieString,
        'Referer': 'https://www.bsbb.cc/sub/index.php',
        'Accept': 'text/plain, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br'
      }
    }, res => {
      console.log('Response status:', res.statusCode);
      console.log('Content-Encoding:', res.headers['content-encoding'] || 'none');
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => {
        const buffer = Buffer.concat(chunks);
        const encoding = (res.headers['content-encoding'] || '').toLowerCase();
        function finish(decompressed) {
          const txt = decompressed.toString('utf8').trim();
          fs.writeFileSync('raw-sub.txt', txt);
          console.log('Saved raw-sub.txt (length:', txt.length, '). Preview:', txt.substring(0, 100));
          if (txt.length < 1000 || txt.includes('<!DOCTYPE')) {
            console.error('Invalid content (HTML or short).');
            process.exit(1);
          }
        }
        if (encoding === 'gzip') zlib.gunzip(buffer, (e, d) => e ? process.exit(1) : finish(d));
        else if (encoding === 'deflate') zlib.inflate(buffer, (e, d) => e ? process.exit(1) : finish(d));
        else if (encoding === 'br') zlib.brotliDecompress(buffer, (e, d) => e ? process.exit(1) : finish(d));
        else finish(buffer);
      });
    });
    req.on('error', e => { console.error('Request error:', e.message); process.exit(1); });
    req.setTimeout(10000, () => { req.destroy(); process.exit(1); });
    req.end();
  } catch (e) {
    console.error('Script error:', e.message);
    process.exit(1);
  }
})();
