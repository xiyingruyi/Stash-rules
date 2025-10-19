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
      args: ['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage','--disable-blink-features=AutomationControlled']
    });
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36');
    await page.goto('https://www.bsbb.cc/sub/index.php', { waitUntil: 'networkidle0', timeout: 30000 });
    await new Promise(r => setTimeout(r, 12000 + Math.random()*2000));
    const finalUrl = page.url();
    if (!finalUrl.includes('/api/sub.php?t=')) {
      console.error('No redirect to /api/sub.php?t= found. URL:', finalUrl);
      await browser.close();
      process.exit(1);
    }
    const cookies = await page.cookies();
    const cookieString = cookies.map(c => `${c.name}=${c.value}`).join('; ');
    await browser.close();

    const req = https.request(finalUrl, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0',
        'Cookie': cookieString,
        'Accept-Encoding': 'gzip, deflate, br'
      }
    }, res => {
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => {
        const buffer = Buffer.concat(chunks);
        const encoding = (res.headers['content-encoding'] || '').toLowerCase();
        function finish(buf) {
          const txt = buf.toString('utf8').trim();
          fs.writeFileSync('input_nodes.txt', txt);
          console.log('Saved -> input_nodes.txt  length:', txt.length);
        }
        if (encoding === 'gzip') zlib.gunzip(buffer, (e, d) => e ? process.exit(1) : finish(d));
        else if (encoding === 'deflate') zlib.inflate(buffer, (e, d) => e ? process.exit(1) : finish(d));
        else if (encoding === 'br') zlib.brotliDecompress(buffer, (e, d) => e ? process.exit(1) : finish(d));
        else finish(buffer);
      });
    });
    req.on('error', e => { console.error(e); process.exit(1); });
    req.end();
  } catch (e) { console.error(e); process.exit(1); }
})();