# Serverless Applications with AWS Lambda

An introductory, student-focused session on serverless computing with AWS Lambda,
covering fundamentals, practical exposure, and industry insights, plus a
demo built end to end with the AWS CDK.

## Topics

- Introduction to Serverless Computing
- AWS Lambda Functions
- API Gateway Basics
- Event-Driven Systems
- Backend Automation & Real-World Use Cases

## The Order Service

This demo builds **one microservice**, the **Order Service**, of a
larger restaurant application. A full app would also have Menu, Payments, and
Kitchen services; here we build only this one, end to end.

This is the **Option B** version: the page is hosted on a **public S3 static
website** (HTTP), and the API is a separate **API Gateway → Lambda → DynamoDB**
path. Because the page (S3, `http`) and the API (`execute-api`, `https`) live on
**different origins**, the browser makes a cross-origin request, so the HTTP API
enables **CORS**, and the page learns the API's address from a small `config.js`
that CDK generates at deploy time (it sets `API_BASE` to the real `ApiUrl`).

```
Browser ──HTTP───►  S3 static website (public)        # the page
        └─HTTPS──►  API Gateway ─► Lambda ─► DynamoDB  # /orders (CORS enabled)
```

> No CloudFront here; it was the "polished production" layer and is optional.
> This stack deploys today with no account verification gate. Trade-offs: the
> website endpoint is **HTTP-only** (no HTTPS), the bucket is **public**, and
> because it's cross-origin you re-add **CORS** (a nice teaching moment).

- `POST /orders`: create an order (returns 201 + the created order)
- `GET /orders`: list all orders (the "kitchen view"; returns 200 + array)

### Project layout

```
app.py                                       # CDK app entry point
cdk.json                                     # CDK config + feature flags
requirements.txt                             # Python dependencies (CDK + test)
stacks/order_service_stack.py                # CDK stack: DynamoDB + Lambda + HTTP API (CORS) + public S3 website
lambda_functions/order_service/handler.py    # the Lambda handler (thin routeKey router)
web/index.html                               # vanilla-JS frontend (calls API_BASE + /orders)
scripts/deploy.sh, scripts/delete.sh         # one-command deploy / teardown
scripts/api.http                             # curl snippets
tests/unit/                                  # pytest (handler via moto, stack via assertions)
```

## Prerequisites

- AWS CLI configured with credentials (`aws sts get-caller-identity` works)
- Node.js + the CDK CLI (`npm install -g aws-cdk`)
- Python 3.12

## Deploy

The fastest path is the script; it bootstraps, deploys, and uploads the
frontend (plus the generated `config.js`) to the S3 website bucket:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
./scripts/deploy.sh
```

Or run the CDK steps yourself:

```bash
cdk bootstrap          # one-time per account/region
cdk deploy             # prints SiteUrl and ApiUrl
```

When it finishes, open the **`SiteUrl`** (the S3 website endpoint, `http://…`) in
your browser. CDK writes a `config.js` next to the page that sets `API_BASE` to
the deployed `ApiUrl`, so the page calls the API cross-origin (CORS is enabled on
the API).

## Local development

For UI-only tweaks you can serve the files locally:

```bash
cd web && python -m http.server 8000        # open http://localhost:8000
```

There's no `config.js` locally, so `API_BASE` falls back to empty and API calls
won't resolve; point it at the deployed API for a full local test by adding a
`web/config.js` with `window.API_BASE = "<ApiUrl>";` (it's git-ignored / a
deploy artifact), or just test the full flow against the deployed `SiteUrl`.

## On-stage script

1. Place an order in the left panel.
2. Refresh the right panel (the "kitchen view"); the order returned from
   DynamoDB appears with no page reload.
3. Optionally open the DynamoDB console and show the item in the `Orders` table.

## Tests

```bash
pip install -r requirements.txt
pytest
```

## Simplifications (call these out verbally)

- `scan()` reads the whole table (fine at this scale); use `Query` with a key in
  production.
- No auth, no input-validation library, no pagination.
- In production with many routes + validation, FastAPI + Mangum is the next
  step, omitted here for clarity.
- `PythonFunction` (alpha + Docker) earns its place only when you have
  third-party pip deps to bundle; we have none beyond `boto3`.

## CORS callout (the #1 gotcha, and how we handle it)

CORS bites whenever a page calls an API on a *different* origin, exactly our
case here: the page is on the S3 website (`http://…s3-website…`) and the API is
on `https://…execute-api…`. The fix is to enable **CORS** on the HTTP API
(`cors_preflight` in the stack), which lets the browser's preflight succeed.
`curl`/Postman ignore CORS entirely, so they work regardless; see
`scripts/api.http`. (The alternative that sidesteps CORS is to put both the page
and `/orders` behind one CloudFront origin; that's the optional
"production-shaped" variant, omitted here.)

## Teardown

```bash
./scripts/delete.sh          # or: cdk destroy
```
