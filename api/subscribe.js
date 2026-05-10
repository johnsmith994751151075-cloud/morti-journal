/**
 * Newsletter subscription endpoint.
 * Sends email notification to owner via Resend (set RESEND_API_KEY env var).
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
          html: `<p><strong>New subscriber:</strong> ${email}</p><p><em>${ts}</em></p>`
        })
      });
    } catch (e) {
      console.error('[morti-subscribe] Resend failed:', e.message);
    }
  }

  return res.status(200).json({ success: true });
}
