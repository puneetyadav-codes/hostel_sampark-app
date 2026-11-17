# Hostel Sampark

A Flask app for submitting, tracking, and managing hostel grievances.

## Run on macOS

1. Install Python 3 and (optionally) Node.js. Open Terminal in this project folder.
2. Create and activate a virtual environment:

   ```sh
   python3 -m venv venv
   source venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. Create a `.env` file in the project folder with the values from your Supabase project:

   ```env
   FLASK_SECRET_KEY=use-a-long-random-secret
   ADMIN_USERNAME=your-admin-name
   ADMIN_PASSWORD=your-admin-password
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SECRET_KEY=your-supabase-server-secret
   GROQ_API_KEY=your-groq-api-key
   ```

   `SUPABASE_SECRET_KEY` is used by the Flask server for grievance submissions, private ticket lookups, and admin actions. Keep it server-side in `.env` and never put it in a template or commit it.
   `GROQ_API_KEY` is needed only when using Groq. Platform API keys are optional; add them only when another service needs to connect, following the platform integration instructions below.

4. In the Supabase SQL Editor, apply these migrations in this exact order:

   1. `supabase/migrations/20261031_add_lookup_token_hash.sql` adds the private-code verifier column.
   2. `supabase/migrations/20261031_lock_grievance_to_server.sql` enables Row Level Security and removes direct table permissions from the `anon` and `authenticated` roles.

   These migrations update an existing `public.grievance` table; create that table first if your Supabase project does not already have it. The Flask server uses `SUPABASE_SECRET_KEY` to access the table.

5. Start the app:

   ```sh
   python app.py
   ```

6. Open <http://127.0.0.1:5000> in the browser.

If the error says a setting is not set in the environment, add that exact name to `.env`. If Python reports a missing module, activate `venv` and install `requirements.txt` again. For a database connection error, verify the Supabase URL/key and that the project is reachable.

To rebuild the CSS after changing Tailwind styles, install Node.js, run `npm install`, then `npm run build:css`. The checked-in CSS already lets you run the app without Node.js.

## AI setup

The app uses Groq's hosted service with the model `openai/gpt-oss-20b`, which is fixed in `ai_provider.py`. You do not need to install Ollama or run a model on your Render server. Set `GROQ_API_KEY` in your local `.env` for local development and in your Render service environment for the deployed app.

The model name is intentionally not an Admin setting. Changing it is a code change and requires a redeploy, which avoids typos and makes it easier to test model changes before they go live. The complete AI instructions are entered in Admin settings, not included in the app code. AI chat stays unavailable until an admin saves instructions. These instructions guide the model but cannot guarantee every answer will follow them.

## Platform API

The API uses standard HTTP requests and JSON, so it can be used by any software capable of making web requests. The public configuration endpoint needs no key. Grievance submission and status lookup require a separate key per connected service, with only the permissions that service needs. Keys are stored as SHA-256 hashes in the server's `PLATFORM_API_KEYS_JSON` setting; the plain key is only shown by the generator and belongs in that platform's private server settings, never browser code or a mobile app.

The complete API description is in [`integrations/openapi.yaml`](./integrations/openapi.yaml). Tools that understand OpenAPI can import this file to show the API or generate client code. A small server-side Python client and an example adapter are in the `integrations` folder.

| Method | Endpoint | Access |
| --- | --- | --- |
| `GET` | `/api/v1/config` | Public settings; browser calls are limited by the approved website addresses in Admin settings |
| `POST` | `/api/v1/submit` | Requires `Authorization: Bearer <PLATFORM_API_KEY>` |
| `POST` | `/api/v1/status` | Requires `Authorization: Bearer <PLATFORM_API_KEY>` and the grievance ticket ID plus private lookup code |

Example submission body:

```json
{
  "title": "Broken light",
  "description": "The light is not working on the second floor.",
  "hostel": "Saramati",
  "category": "Electrical"
}
```

Send the JSON body with `Content-Type: application/json` and `Authorization: Bearer <PLATFORM_API_KEY>`. The successful response includes `ticket_id` and `lookup_code`. Show the private lookup code only to the person submitting the grievance and do not write it to logs.

For example, the platform's server sends:

```http
POST /api/v1/submit HTTP/1.1
Content-Type: application/json
Authorization: Bearer <PLATFORM_API_KEY>

{"title":"Broken light","description":"The light is not working on the second floor.","hostel":"Saramati","category":"Electrical"}
```

To check the status, send this JSON to `/api/v1/status` with the same Authorization header:

```json
{
  "ticket_id": 123,
  "lookup_code": "the-private-code-returned-at-submission"
}
```

The response contains the `ticket_id` and current `status`, for example `{"ticket_id":123,"status":"In Progress"}`; it does not include staff-only remarks.

## Connecting another platform: simple setup

You only need these steps if another website or app should use Hostel Sampark's grievance API.

1. **Generate one key for the other service.** From the project folder run:

   ```powershell
   python integrations\generate_api_key.py campus_portal grievance:submit grievance:status
   ```

   Replace `campus_portal` with a short name for the service. Copy the generated private key into that service's private server settings. The command also prints a JSON entry containing the key's hash and permissions; it does not store the private key in the project.
2. **Add the JSON entry to Render.** In Render, open your app service's **Environment** settings. Add or update `PLATFORM_API_KEYS_JSON` with a JSON object containing the generated client entry. If you previously set the old `PLATFORM_API_KEY` variable, remove it; the per-service API no longer reads that setting. For example:

   ```json
   {"campus_portal":{"key_hash":"paste-the-64-character-hash-from-the-generator","scopes":["grievance:submit","grievance:status"]}}
   ```

   If you connect another service later, add its entry alongside `campus_portal` inside the same JSON object. Do not put the private key itself in this setting. Restart/redeploy the service after saving environment changes.
3. **Use the connector in the other service's server.** Set `HOSTEL_SAMPARK_URL` to your Render app URL and `HOSTEL_SAMPARK_API_KEY` to the generated private key. The example code in [`integrations/example_platform.py`](./integrations/example_platform.py) shows reading options, submitting a grievance, and checking its status. The API key must stay server-side.
4. **Grant only needed permissions.** Use `grievance:submit` to allow a service to submit grievances and `grievance:status` to let it check status. A key with one permission cannot use the other action. Public configuration is readable without a key.
5. **Revoke or replace a key.** Remove that service's entry from `PLATFORM_API_KEYS_JSON` in Render to revoke it. To rotate it, generate a new key and replace the old entry and the connected service's stored key.
6. **Set an approved website origin only if needed.** Admin settings' approved website origins only let a browser read the public `/api/v1/config` response. Enter an exact origin such as `https://other.example`; it does not limit who can visit Hostel Sampark and it is not API authentication. Private submit/status endpoints are for server-to-server use and do not allow browser access, so never put a platform API key in browser code. Server-to-server connectors do not need this setting.

The Python example is a starting point for Flask or other Python server apps. Other languages and platforms can use the same documented HTTP/JSON API or generate a client from the OpenAPI file. No one connector can automatically plug into every product; each platform still needs a small setup step to map its form fields to the API.

Example use in a Python server:

```python
import os

from integrations import HostelSamparkClient

client = HostelSamparkClient(
    base_url=os.environ["HOSTEL_SAMPARK_URL"],
    api_key=os.environ["HOSTEL_SAMPARK_API_KEY"],
)

options = client.get_config()
receipt = client.submit_grievance(
    title="Broken light",
    description="The light is not working.",
    hostel="Saramati",
    category="Electrical",
)
status = client.get_status(receipt["ticket_id"], receipt["lookup_code"])
```

In a real integration, read the URL and API key from environment settings rather than writing the key in code. The key generator prints the private key once; save it directly in the connecting platform's server settings.

## Render session and CSRF settings

On Render, `RENDER=true` makes the app issue secure HTTPS-only session cookies automatically. Set `FLASK_SECRET_KEY` in the Render service environment to a long, random value and keep it unchanged between deploys and instances. Changing it invalidates existing sessions. The app now gives its session cookie a fresh name and marks HTML pages as non-cacheable so browsers do not reuse stale forms.

After deploying this update, visit `/admin-login` again and sign in. If the error continues, check that Render has one stable `FLASK_SECRET_KEY` value and that the browser is using the same `https://hostel-sampark-app.onrender.com` host for both loading and submitting the form.
