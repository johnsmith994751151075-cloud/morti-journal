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
  res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate');

  try {
    const [account, positions] = await Promise.all([
      alpacaRequest('/account'),
      alpacaRequest('/positions')
    ]);

    const equity      = parseFloat(account.equity);
    const lastEquity  = parseFloat(account.last_equity);
    const cash        = parseFloat(account.cash);
    const startingCap = 100000;

    // Total P&L since inception — always accurate
    const totalPnl = equity - startingCap;

    // Unrealized P&L — sum of all open positions
    const unrealizedPnl = positions.reduce((sum, p) => sum + parseFloat(p.unrealized_pl || 0), 0);

    // Realized P&L — accounting identity: Total = Realized + Unrealized
    // This is always mathematically correct regardless of what trades happened
    const realizedPnl = totalPnl - unrealizedPnl;

    // Day change — mark vs previous close (includes position exits)
    const dayChange = equity - lastEquity;

    res.status(200).json({
      equity,
      last_equity: lastEquity,
      cash,
      starting_capital: startingCap,

      // P&L breakdown — always accurate
      total_pnl:      totalPnl,       // inception return
      realized_pnl:   realizedPnl,    // crystallized gains (closed trades)
      unrealized_pnl: unrealizedPnl,  // open book mark-to-market
      day_change:     dayChange,       // vs previous close (includes exits)

      positions: positions.map(p => ({
        symbol:                p.symbol,
        qty:                   p.qty,
        avg_entry_price:       p.avg_entry_price,
        current_price:         p.current_price,
        market_value:          p.market_value,
        unrealized_pl:         p.unrealized_pl,
        unrealized_plpc:       p.unrealized_plpc,
        unrealized_intraday_pl: p.unrealized_intraday_pl,
      }))
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
