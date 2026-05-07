/**
 * Newsletter subscription endpoint.
 * Posts new subscribers to a Discord webhook (set DISCORD_SUBSCRIBE_WEBHOOK env var).
 * All signups are also logged to Vercel function logs.
 */
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  let body = req.body;
  if (typeof body === 'string') {
    try { body = JSON.parse(body); } catch { body = {}; }
  }

  const { email } = body || {};

  if (!email || !email.includes('@') || !email.includes('.')) {
    return res.status(400).json({ error: 'Invalid email' });
  }

  const ts = new Date().toISOString();
  console.log(`[morti-subscribe] ${email} — ${ts}`);

  const webhookUrl = process.env.DISCORD_SUBSCRIBE_WEBHOOK;
  if (webhookUrl) {
    try {
      await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: `📧 **New Subscriber** — \`${email}\`\n*Morti Capital Newsletter · ${ts}*`
        })
      });
    } catch (e) {
      console.error('[morti-subscribe] Discord webhook failed:', e.message);
    }
  }

  return res.status(200).json({ success: true });
}
