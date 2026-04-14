# Notification Setup

> 🚧 **Coming soon** — Detailed setup for each notification method.

## Options

### Gmail SMTP (Recommended Default)

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password: Google Account → Security → App Passwords
3. In n8n, add a **Send Email** node credential with your Gmail address and the app password
4. Set SSL/TLS to ON, port 465

**Note:** DigitalOcean blocks SMTP ports by default. Use Resend instead, or open a support ticket to unblock.

### Resend (Recommended for DigitalOcean)

1. Sign up at [resend.com](https://resend.com) (free: 100 emails/day)
2. Verify your domain or use their test domain
3. Get your API key
4. In n8n, use an **HTTP Request** node to POST to Resend's API

### Discord Webhook (Power Users)

1. In your Discord server: Channel Settings → Integrations → Webhooks → New Webhook
2. Copy the webhook URL
3. In n8n, use an **HTTP Request** node to POST to the webhook URL
