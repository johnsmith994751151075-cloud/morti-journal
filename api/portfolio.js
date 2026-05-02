const https = require('https');

function alpacaRequest(path) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'paper-api.alpaca.markets',
      path: `/v2${path}`,
      headers: {
        'APCA-API-KEY-ID': process.env.ALPACA_KEY,
        'APCA-API-SECRET-KEY': process.env.ALPACA_SECRET,
      }
    };
    https.get(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch(e) { reject(e); }
      });
    }).on('error', reject);
  });
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate');

  try {
    const [account, positions] = await Promise.all([
      alpacaRequest('/account'),
      alpacaRequest('/positions')
    ]);

    res.status(200).json({
      equity: account.equity,
      last_equity: account.last_equity,
      cash: account.cash,
      positions: positions.map(p => ({
        symbol: p.symbol,
        qty: p.qty,
        market_value: p.market_value,
        unrealized_pl: p.unrealized_pl,
        unrealized_plpc: p.unrealized_plpc,
        unrealized_intraday_pl: p.unrealized_intraday_pl,
      }))
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
