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

Without `DATABASE_URL`, the app uses SQLite. On Render Free, SQLite data can disappear after restart, redeploy, or idle spin-down.

## Domain

1. Render service > Settings > Custom Domains.
2. Add `manvimart.com`.
3. Render will also add or redirect `www.manvimart.com`.
4. At your domain DNS provider, add the DNS records Render shows.
5. Remove old `AAAA` records for the domain if Render asks.
6. Return to Render and click Verify.

After verification, Render automatically enables HTTPS.
