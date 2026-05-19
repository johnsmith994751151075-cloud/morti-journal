const https = require('https');

const GIST_ID  = 'c271bdfabd17bf7301d4d7be889b9932';
const API_URL  = `https://api.github.com/gists/${GIST_ID}`;

function fetchUrl(url, headers) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return fetchUrl(res.headers.location, headers).then(resolve).catch(reject);
      }
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(new Error('JSON parse failed: ' + data.slice(0, 100))); }
      });
    }).on('error', reject);
  });
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  // No edge caching — always fresh
  res.setHeader('Cache-Control', 'no-store');

  try {
    // Fetch via GitHub Gist API (not raw CDN) — always returns latest content
    const headers = {
      'User-Agent': 'MortiCapital/1.0',
      'Accept': 'application/vnd.github.v3+json'
    };
    const gist = await fetchUrl(API_URL, headers);
    const content = gist.files['agent_reads.json'].content;
    const data = JSON.parse(content);
    res.status(200).json(data);
  } catch (e) {
    res.status(200).json({ date: null, timestamp: null, agents: {} });
  }
};
