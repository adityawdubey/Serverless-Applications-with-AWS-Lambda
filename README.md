# Serverless Applications with AWS Lambda

An introductory, student-focused session on serverless computing with AWS Lambda
— covering fundamentals, practical exposure, and industry insights — plus a
hands-on demo built end to end with the AWS CDK.

## Session topics

- Introduction to Serverless Computing
- AWS Lambda Functions
- API Gateway Basics
- Event-Driven Systems
- Backend Automation & Real-World Use Cases

## Hands-on: the Order Service

The hands-on portion builds **one microservice** — the **Order Service** — of a
larger restaurant application. A full app would also have Menu, Payments, and
Kitchen services; here we build only this one, end to end.

This is the **production-shaped** version: a single **CloudFront** distribution
serves both the page (from a private S3 bucket) and the API (the `/orders` path
forwards to API Gateway). Because the page and the API share one origin, the
browser makes no cross-origin request — so there is **no CORS** and no API-URL
config to manage; the page just calls the relative path `/orders`.

```
                       ┌─► (default)  S3 (static site)         # the page
Browser ──HTTPS──► CloudFront
                       └─► /orders    API Gateway ─► Lambda ─► DynamoDB
```

- `POST /orders` — create an order (returns 201 + the created order)
- `GET /orders`  — list all orders (the "kitchen view"; returns 200 + array)

### Project layout

```
app.py                                       # CDK app entry point
cdk.json                                     # CDK config + feature flags
requirements.txt                             # Python dependencies (CDK + test)
stacks/order_service_stack.py                # CDK stack: DynamoDB + Lambda + HTTP API + S3 + CloudFront
lambda_functions/order_service/handler.py    # the Lambda handler (thin routeKey router)
web/index.html                               # vanilla-JS frontend (calls relative /orders)
scripts/deploy.sh, scripts/delete.sh         # one-command deploy / teardown
scripts/api.http                             # curl snippets
tests/unit/                                  # pytest (handler via moto, stack via assertions)
```

## Prerequisites

- AWS CLI configured with credentials (`aws sts get-caller-identity` works)
- Node.js + the CDK CLI (`npm install -g aws-cdk`)
- Python 3.12

## Deploy

The fastest path is the script — it bootstraps, deploys, and uploads the
frontend to S3:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
./scripts/deploy.sh
```

Or run the CDK steps yourself:

```bash
cdk bootstrap          # one-time per account/region
cdk deploy             # prints SiteUrl, ApiUrl, and TableName
```

When it finishes, open the **`SiteUrl`** (the CloudFront URL) in your browser.
On a first deploy, give CloudFront a few minutes to finish provisioning.

## Local development

The page calls the relative path `/orders`, so it expects the API on its own
origin. For UI-only tweaks you can still serve the files locally:

```bash
cd web && python -m http.server 8000        # open http://localhost:8000
```

API calls won't resolve at `localhost` (there's no `/orders` there, and the API
has no CORS by design), so test the full flow against the deployed `SiteUrl`. To
point `API_BASE` somewhere temporarily for local work, edit the top of
`web/index.html`.

## On-stage script

1. Place an order in the left panel.
2. Refresh the right panel (the "kitchen view") — the order returned from
   DynamoDB appears with no page reload.
3. Optionally open the DynamoDB console and show the item in the `Orders` table.

## Tests

```bash
pip install -r requirements.txt
pytest
```

## Simplifications (call these out verbally)

- `scan()` reads the whole table — fine at this scale; use `Query` with a key in
  production.
- No auth, no input-validation library, no pagination.
- In production with many routes + validation, FastAPI + Mangum is the next
  step — omitted here for clarity.
- `PythonFunction` (alpha + Docker) earns its place only when you have
  third-party pip deps to bundle; we have none beyond `boto3`.

## CORS callout (the #1 gotcha — and how we sidestep it)

CORS bites whenever a page calls an API on a *different* origin. We avoid it
entirely: CloudFront serves both the page and `/orders`, so they share one
origin and the browser never makes a cross-origin request — no CORS config at
all. (The simpler-but-noisier alternative is to keep the page and API on
separate origins and enable CORS on the HTTP API; `curl`/Postman ignore CORS
either way — see `scripts/api.http`.)

## Teardown

```bash
./scripts/delete.sh          # or: cdk destroy
```
