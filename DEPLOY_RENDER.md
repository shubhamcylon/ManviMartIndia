# Manvi Mart Render Deploy

## Render Web Service

1. Push this project to GitHub.
2. Render Dashboard > New > Web Service.
3. Connect the GitHub repository.
4. Use these settings:
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn main:app`
   - Health Check Path: `/healthz`
   - Instance Type: Free

## Environment Variables

Add these in Render > Service > Environment:

- `SECRET_KEY`: generate a long random value, or let `render.yaml` generate it.
- `MAIL_USERNAME`: Gmail address for password reset emails, optional.
- `MAIL_PASSWORD`: Gmail app password, optional.
- `DATABASE_URL`: Render Postgres external/internal URL, optional.
- `STORE_EMAIL`: Owner email for order alerts (example: `you@gmail.com`).
- `STORE_WHATSAPP_NUMBER`: Optional, owner WhatsApp number for post-order customer confirmation link (example: `9198XXXXXXXX`).
- `ORDER_ALERT_TELEGRAM_BOT_TOKEN`: Optional free instant alert channel.
- `ORDER_ALERT_TELEGRAM_CHAT_ID`: Optional free instant alert channel.
- `ORDER_ALERT_WHATSAPP_PHONE`: Optional free WhatsApp alert via CallMeBot (example: `9198XXXXXXXX`).
- `ORDER_ALERT_WHATSAPP_APIKEY`: Optional free WhatsApp alert via CallMeBot.
- `GOOGLE_SHEET_WEBHOOK_URL`: Optional Apps Script Web App URL to push every new order into Google Sheet.
- `GOOGLE_SHEET_WEBHOOK_TOKEN`: Optional secret token sent as `?token=...` query string.

Without `DATABASE_URL`, the app uses SQLite. On Render Free, SQLite data can disappear after restart, redeploy, or idle spin-down.

## Free Order Notification Options

### Option 1: Telegram (Recommended Free)
1. In Telegram, create bot via `@BotFather`.
2. Copy bot token and set `ORDER_ALERT_TELEGRAM_BOT_TOKEN`.
3. Send one message to your bot from your Telegram account.
4. Get chat id using:
   `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
5. Set `ORDER_ALERT_TELEGRAM_CHAT_ID`.

### Option 2: WhatsApp (Free via CallMeBot)
1. Open CallMeBot WhatsApp API page and register your number.
2. Get your API key.
3. Set `ORDER_ALERT_WHATSAPP_PHONE` and `ORDER_ALERT_WHATSAPP_APIKEY`.
4. On each order, website will send a WhatsApp text alert automatically.

### Option 3: Google Sheet (Free via Apps Script)
1. Open your Google Sheet.
2. Extensions > Apps Script.
3. Paste this script and deploy as Web App (Execute as: Me, Access: Anyone with link).

```javascript
function doPost(e) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Orders") || SpreadsheetApp.getActiveSpreadsheet().insertSheet("Orders");
  const token = "CHANGE_THIS_TOKEN";
  const incomingToken = e?.parameter?.token || "";
  const data = JSON.parse(e.postData.contents || "{}");

  if (token && incomingToken !== token) {
    return ContentService.createTextOutput("Unauthorized").setMimeType(ContentService.MimeType.TEXT);
  }

  if (sheet.getLastRow() === 0) {
    sheet.appendRow([
      "Created At", "Tracking ID", "Invoice", "Customer", "Phone", "Email",
      "Payment", "Status", "Address", "City", "State", "Pincode", "Total", "Items"
    ]);
  }

  const items = (data.items || []).map(i => `${i.name} x${i.quantity}`).join(", ");
  sheet.appendRow([
    data.created_at || "",
    data.tracking_id || "",
    data.invoice_no || "",
    data.customer_name || "",
    data.customer_phone || "",
    data.customer_email || "",
    data.payment_method || "",
    data.order_status || "",
    data.shipping_address || "",
    data.shipping_city || "",
    data.shipping_state || "",
    data.shipping_pincode || "",
    data.grand_total || "",
    items
  ]);

  return ContentService.createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}
```

4. Copy deployed Web App URL to `GOOGLE_SHEET_WEBHOOK_URL`.
5. If using token protection, set same token in Render as `GOOGLE_SHEET_WEBHOOK_TOKEN`.

## Domain

1. Render service > Settings > Custom Domains.
2. Add `manvimart.com`.
3. Render will also add or redirect `www.manvimart.com`.
4. At your domain DNS provider, add the DNS records Render shows.
5. Remove old `AAAA` records for the domain if Render asks.
6. Return to Render and click Verify.

After verification, Render automatically enables HTTPS.
