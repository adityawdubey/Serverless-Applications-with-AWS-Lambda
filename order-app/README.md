# Order Service — Serverless

This is **one microservice** — the **Order Service** — of a larger restaurant
application. A full app would also have Menu, Payments, and Kitchen services;
here we build only this one, end to end. The request path is deliberately
obvious: **browser → API Gateway → Lambda → DynamoDB → back**.

- `POST /orders` — create an order (returns 201 + the created order)
- `GET /orders`  — list all orders (the "kitchen view"; returns 200 + array)

## Prerequisites

- AWS CLI configured with credentials (`aws sts get-caller-identity` works)
- Node.js (the CDK CLI is a Node tool — we use `npx aws-cdk@2`, no global install)
- Python 3.12

## Deploy

The commands below invoke the CDK CLI via `npx aws-cdk@2`. If you have the CLI
installed globally you can use the `cdk` shorthand instead.
Equivalents: `cdk bootstrap`, `cdk deploy`, `cdk destroy`.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
npx aws-cdk@2 bootstrap          # one-time per account/region
npx aws-cdk@2 deploy             # prints ApiUrl and TableName
```

Copy the `ApiUrl` output into `web/index.html` → `const API_BASE = "..."` (no
trailing slash).

## Run the frontend

```bash
cd web && python -m http.server 8000
# open http://localhost:8000
```

Serving over a real `http://` origin is the most reliable option. Opening the
file directly usually also works because CORS allows `*`.

## On-stage script

1. Place an order in the left panel.
2. Refresh the right panel (the "kitchen view") — the order returned from
   DynamoDB appears with no page reload.
3. Optionally open the DynamoDB console and show the item in the `Orders` table.

## Simplifications (call these out verbally)

- `scan()` reads the whole table — fine at this scale; use `Query` with a key in
  production.
- CORS is wide open (`*`) — lock origins down in production.
- No auth, no input-validation library, no pagination.
- In production with many routes + validation, FastAPI + Mangum is the next
  step — omitted here for clarity.
- `PythonFunction` (alpha + Docker) earns its place only when you have
  third-party pip deps to bundle; we have none beyond `boto3`.

## CORS callout (the #1 gotcha)

CORS is enabled in exactly one place — the **HTTP API** (`cors_preflight`).
When CORS is configured on an HTTP API, API Gateway answers preflight and
**ignores** any CORS headers from the Lambda, so the function only returns
`Content-Type`. `curl`/Postman ignore CORS — handy as a stage fallback (see
`scripts/api.http`).

## Teardown

```bash
npx aws-cdk@2 destroy            # deletes the stack (and the table's data)
```
