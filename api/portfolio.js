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
  res.setHeader('Cache-Control', 'no-store');

  try {
    const [account, positions, orders] = await Promise.all([
      alpacaRequest('/account'),
      alpacaRequest('/positions'),
      alpacaRequest('/orders?status=open&limit=50'),
    ]);

    const equity      = parseFloat(account.equity);
    const lastEquity  = parseFloat(account.last_equity);
    const cash        = parseFloat(account.cash);
    const startingCap = 100000;

    const totalPnl      = equity - startingCap;
    const unrealizedPnl = positions.reduce((sum, p) => sum + parseFloat(p.unrealized_pl || 0), 0);
    const realizedPnl   = totalPnl - unrealizedPnl;
    const dayChange     = equity - lastEquity;

    // Classify open orders — only top-level entries (not OCO legs)
    const posSymbols    = new Set(positions.map(p => p.symbol));
    const pendingBuys   = [];
    const pendingCloses = [];

    for (const o of orders) {
      if (o.order_class === 'bracket' && o.side === 'buy') {
        // Bracket entry leg — pending open position
        pendingBuys.push({
          symbol: o.symbol,
          qty:    o.qty || o.notional,
          type:   'PENDING OPEN',
          order_class: o.order_class,
        });
      } else if (o.side === 'sell' && o.type === 'market' && !o.order_class) {
        // Market sell with no class = intentional close (not a stop-loss)
        pendingCloses.push({ symbol: o.symbol, qty: o.qty });
      }
      // Ignore: stop orders (type=stop), bracket legs (order_class=oco) — these are protection
    }

    res.status(200).json({
      equity,
      last_equity:     lastEquity,
      cash,
      starting_capital: startingCap,
      total_pnl:       totalPnl,
      realized_pnl:    realizedPnl,
      unrealized_pnl:  unrealizedPnl,
      day_change:      dayChange,

      positions: positions.map(p => ({
        symbol:                  p.symbol,
        qty:                     p.qty,
        avg_entry_price:         p.avg_entry_price,
        current_price:           p.current_price,
        market_value:            p.market_value,
        unrealized_pl:           p.unrealized_pl,
        unrealized_plpc:         p.unrealized_plpc,
        unrealized_intraday_pl:  p.unrealized_intraday_pl,
        closing: pendingCloses.some(c => c.symbol === p.symbol),
      })),

      pending_orders: pendingBuys,
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
