/**
 * Morti Capital — Newsletter subscription endpoint.
 *
 * Every signup is:
 *  1. Appended to a private GitHub Gist (persistent list, never lost)
 *  2. Pinged to the morti_cio Discord channel via webhook (instant notification)
 *  3. Sent via Resend if RESEND_API_KEY is set (optional bonus)
 *
 * Required env vars (set in Vercel dashboard):
 *   GITHUB_TOKEN             — GitHub PAT with gist scope
 *   SUBSCRIBERS_GIST_ID      — ID of the private subscribers gist
 *   DISCORD_SUBSCRIBER_WEBHOOK — Discord webhook URL for notifications
 *
 * Optional:
 *   RESEND_API_KEY — if set, also emails babarlabs@gmail.com
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

  // ── 1. Store in GitHub Gist ──────────────────────────────────────────────
  const ghToken  = process.env.GITHUB_TOKEN;
  const gistId   = process.env.SUBSCRIBERS_GIST_ID;
  let storedOk   = false;
  let totalCount = 0;

  if (ghToken && gistId) {
    try {
      // Fetch current list
      const getRes = await fetch(`https://api.github.com/gists/${gistId}`, {
        headers: {
          'Authorization': `token ${ghToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'MortiCapital/1.0'
        }
      });
      const gistData = await getRes.json();
      const raw = gistData.files?.['subscribers.json']?.content || '{"subscribers":[],"count":0}';
      const parsed = JSON.parse(raw);

      // Deduplicate
      const already = parsed.subscribers.some(s =>
        (typeof s === 'string' ? s : s.email) === email
      );

      if (!already) {
        parsed.subscribers.push({ email, signed_up: ts });
        parsed.count = parsed.subscribers.length;
        parsed.last_updated = ts;

        // Write back
        await fetch(`https://api.github.com/gists/${gistId}`, {
          method: 'PATCH',
          headers: {
            'Authorization': `token ${ghToken}`,
            'Content-Type': 'application/json',
            'User-Agent': 'MortiCapital/1.0'
          },
          body: JSON.stringify({
            files: {
              'subscribers.json': { content: JSON.stringify(parsed, null, 2) }
            }
          })
        });
        storedOk = true;
        totalCount = parsed.count;
        console.log(`[morti-subscribe] Stored in Gist. Total: ${totalCount}`);
      } else {
        storedOk = true; // Already subscribed, that's fine
        totalCount = parsed.count;
        console.log(`[morti-subscribe] Duplicate — already subscribed.`);
        return res.status(200).json({ success: true, note: 'already_subscribed' });
      }
    } catch (e) {
      console.error('[morti-subscribe] Gist write failed:', e.message);
    }
  } else {
    console.warn('[morti-subscribe] GITHUB_TOKEN or SUBSCRIBERS_GIST_ID not set — signup not persisted!');
  }

  // ── 2. Discord notification ──────────────────────────────────────────────
  const discordWebhook = process.env.DISCORD_SUBSCRIBER_WEBHOOK;
  if (discordWebhook) {
    try {
      await fetch(discordWebhook, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: null,
          embeds: [{
            title: '📧 New Morti Capital Subscriber',
            color: 0xC9A96E,
            fields: [
              { name: 'Email', value: `\`${email}\``, inline: true },
              { name: 'Total Subscribers', value: `${totalCount}`, inline: true },
              { name: 'Time', value: new Date(ts).toLocaleString('en-US', { timeZone: 'America/New_York', dateStyle: 'medium', timeStyle: 'short' }), inline: false }
            ],
            footer: { text: 'morti-journal · newsletter' }
          }]
        })
      });
    } catch (e) {
      console.error('[morti-subscribe] Discord notify failed:', e.message);
    }
  }

  // ── 3. Resend (optional, if key is set) ──────────────────────────────────
  const resendKey = process.env.RESEND_API_KEY;
  if (resendKey) {
    try {
      await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${resendKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          from: 'Morti Capital <onboarding@resend.dev>',
          to: ['babarlabs@gmail.com'],
          subject: `📧 New Morti Capital Subscriber — ${email}`,
          html: `<p><strong>New subscriber:</strong> ${email}</p><p><em>${ts}</em></p><p>Total: ${totalCount}</p>`
        })
      });
    } catch (e) {
      console.error('[morti-subscribe] Resend failed:', e.message);
    }
  }

  return res.status(200).json({ success: true });
}
