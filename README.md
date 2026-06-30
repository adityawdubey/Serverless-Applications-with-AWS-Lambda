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
Kitchen services; here we build only this one, end to end. The request path is
deliberately obvious: **browser → API Gateway → Lambda → DynamoDB → back**.

- `POST /orders` — create an order (returns 201 + the created order)
- `GET /orders`  — list all orders (the "kitchen view"; returns 200 + array)

### Project layout

```
app.py                                  # CDK app entry point
cdk.json                                # CDK config + feature flags
requirements.txt                        # Python dependencies (CDK + test)
stacks/order_service_stack.py           # the CDK stack (DynamoDB + Lambda + HTTP API)
lambda_functions/order_service/handler.py   # the Lambda handler (thin routeKey router)
web/index.html                          # vanilla-JS frontend
scripts/deploy.sh, scripts/delete.sh    # one-command deploy / teardown
scripts/api.http                        # curl snippets
tests/unit/                             # pytest (handler via moto, stack via assertions)
```

## Prerequisites

- AWS CLI configured with credentials (`aws sts get-caller-identity` works)
- Node.js + the CDK CLI (`npm install -g aws-cdk`)
- Python 3.12

## Deploy

The fastest path is the script — it bootstraps, deploys, and wires the live API
URL into the frontend automatically:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
./scripts/deploy.sh
```

Or run the CDK steps yourself:

```bash
cdk bootstrap          # one-time per account/region
cdk deploy             # prints ApiUrl and TableName
```

Then copy the `ApiUrl` output into `web/index.html` → `const API_BASE = "..."`
(no trailing slash) — the deploy script does this for you.

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

## Tests

```bash
pip install -r requirements.txt
pytest
```

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
./scripts/delete.sh          # or: cdk destroy
```
