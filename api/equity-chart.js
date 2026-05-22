const https = require('https');

function alpacaGet(hostname, path, headers) {
  return new Promise((resolve, reject) => {
    https.get({ hostname, path, headers }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => { try { resolve(JSON.parse(data)); } catch(e) { reject(e); } });
    }).on('error', reject);
  });
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate');

  const alpacaHeaders = {
    'APCA-API-KEY-ID': process.env.ALPACA_KEY,
    'APCA-API-SECRET-KEY': process.env.ALPACA_SECRET,
  };
  const dataHeaders = {
    ...alpacaHeaders,
  };

  try {
    // Portfolio history
    const ph = await alpacaGet(
      'paper-api.alpaca.markets',
      '/v2/account/portfolio/history?period=1M&timeframe=1D&extended_hours=false',
      alpacaHeaders
    );
    if (ph.message || ph.code) throw new Error(`Alpaca auth error: ${ph.message || ph.code}`);

    // Benchmarks from Alpaca data API
    const today = new Date().toISOString().split('T')[0];
    // SPY = S&P 500, QQQ = Nasdaq 100, DIA = Dow Jones
    const barsPath = `/v2/stocks/bars?symbols=SPY,QQQ,DIA&timeframe=1Day&start=2026-04-24&end=${today}&feed=iex&limit=100`;
    const barsData = await alpacaGet('data.alpaca.markets', barsPath, dataHeaders);

    // Filter portfolio to trading days with equity > 0
    const portfolioPairs = ph.timestamp
      .map((ts, i) => ({ date: new Date(ts * 1000).toISOString().split('T')[0], equity: ph.equity[i] }))
      .filter(p => p.equity > 0);

    // Always patch today's point with live equity — Alpaca history lags by hours
    const todayNY = new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' });
    const liveAccount = await alpacaGet('paper-api.alpaca.markets', '/v2/account', alpacaHeaders);
    const liveEquity = parseFloat(liveAccount.equity);
    if (liveEquity > 0) {
      // Remove any existing today entry (stale) and replace with live value
      const withoutToday = portfolioPairs.filter(p => p.date !== todayNY);
      withoutToday.push({ date: todayNY, equity: liveEquity, live: true });
      portfolioPairs.length = 0;
      withoutToday.forEach(p => portfolioPairs.push(p));
    }

    // Normalize all benchmarks to $100K from first available bar
    const normalized = {};
    const benchSymbols = { SPY: 'S&P 500', QQQ: 'Nasdaq 100', DIA: 'Dow Jones' };
    for (const sym of Object.keys(benchSymbols)) {
      const bars = (barsData.bars || {})[sym] || [];
      const base = bars[0]?.c || 1;
      normalized[sym] = {
        label: benchSymbols[sym],
        data: bars.map(b => ({
          date: b.t.split('T')[0],
          value: parseFloat((100000 * b.c / base).toFixed(2))
        }))
      };
    }

    // Calculate outperformance vs each benchmark
    const latestEquity = portfolioPairs.length ? portfolioPairs[portfolioPairs.length - 1].equity : 100000;
    const mortiBeta = ((latestEquity - 100000) / 100000 * 100).toFixed(2);
    const alpha = {};
    for (const sym of Object.keys(benchSymbols)) {
      const pts = normalized[sym].data;
      const latestBench = pts.length ? pts[pts.length - 1].value : 100000;
      const benchReturn = ((latestBench - 100000) / 100000 * 100).toFixed(2);
      alpha[sym] = {
        label: benchSymbols[sym],
        bench_return_pct: benchReturn,
        morti_return_pct: mortiBeta,
        alpha_pct: (parseFloat(mortiBeta) - parseFloat(benchReturn)).toFixed(2)
      };
    }

    res.status(200).json({
      portfolio: portfolioPairs,
      benchmarks: normalized,
      alpha
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
