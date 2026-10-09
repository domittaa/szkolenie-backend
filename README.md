# backend (Pizza Platform API)

FastAPI service with the REST API used by the **frontend** SPA. Runs on Cloud Run (`pizza-backend`),
stores data in PostgreSQL on Cloud SQL and publishes order events to Pub/Sub.

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/healthz` | – | Liveness probe, uptime check |
| GET | `/readyz` | – | Startup probe (checks the database) |
| GET | `/api/v1/menu?category=&available_only=` | – | Menu |
| GET | `/api/v1/menu/{item_id}` | – | Menu item |
| POST | `/api/v1/menu` | admin | Create a menu item |
| PATCH | `/api/v1/menu/{item_id}` | admin | Update a menu item |
| POST | `/api/v1/orders` | customer | Place an order |
| GET | `/api/v1/orders?page=&page_size=&status=` | customer / staff | Own orders (staff: all orders), paginated |
| GET | `/api/v1/orders/{order_id}` | customer / staff | Order details |
| POST | `/api/v1/orders/{order_id}/cancel` | customer / staff | Cancel (customers only before `preparing`) |
| PATCH | `/api/v1/orders/{order_id}/status` | staff | Move the order through its lifecycle |
| POST | `/api/v1/promo-codes/validate` | customer | Validate a promo code (feature flag `PROMO_CODES_ENABLED`) |

OpenAPI: `/docs` (disabled in prod). Errors always use the pizza-core envelope
`{"error": {"code", "message", "details", "request_id"}}`.

## Related repositories

- **core-library**: `pizza-core` (money, errors, pagination, auth, events, logging, db), pinned `>=1.4,<2.0`.
- **frontend**: consumes this API. Its types in `src/api/types.ts` are maintained by hand.
- **gcp**: Cloud Run service and its env vars (`modules/app-environment/services.tf`), Cloud SQL,
  Pub/Sub topic `order-events`, the migration job `pizza-backend-migrate`, CI identities.

## Local development

```bash
docker compose up -d db
python -m venv .venv && source .venv/bin/activate
# pizza-core from Artifact Registry...
pip install --extra-index-url https://europe-central2-python.pkg.dev/pizza-shared-4821/python-libs/simple/ -e ".[dev]"
# ...or from a local checkout of the core-library repo next to this one
pip install -e "../core-library[fastapi,pubsub]" -e ".[dev]"

cp .env.example .env
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload   # http://localhost:8000/docs
pytest
```

## Configuration

| Variable | Description | Set by (Cloud Run) |
|---|---|---|
| `APP_ENV` | `local` / `dev` / `prod` | Terraform |
| `LOG_LEVEL` | Log level | Terraform (tfvars) |
| `GCP_PROJECT_ID` | Project of the Pub/Sub topic | Terraform |
| `DB_INSTANCE_CONNECTION_NAME`, `DB_NAME`, `DB_USER` | Cloud SQL socket connection | Terraform |
| `DB_PASSWORD` | Database password | Secret Manager `db-password` |
| `AUTH_ISSUER`, `AUTH_AUDIENCE` | Identity Platform token validation | Terraform |
| `ORDERS_TOPIC` | Pub/Sub topic for order events | Terraform |
| `CORS_ALLOWED_ORIGINS` | Comma separated frontend origins | Terraform (frontend URL + `extra_cors_origins`) |
| `PROMO_CODES_ENABLED` | Promo codes feature flag | Terraform (tfvars) |
| `DATABASE_URL`, `USE_INMEMORY_EVENTS` | Local development only | – |

## Contract change checklist

- API change → update frontend `src/api/types.ts` and the pages using it
- New env var → add it to gcp `modules/app-environment/services.tf` (service **and** migration job)
- New error code → add it to pizza-core `ErrorCode` and to frontend `src/api/errors.ts`
- Order lifecycle or pricing rules → mirrored in frontend `src/utils/orderStatus.ts` / `src/utils/pricing.ts`

## Links

- Jira: project **PIZZA**, component `backend`
- Confluence: PIZZA → *Architecture Overview*, *Order Lifecycle*, *Pricing & Delivery*, *API Guidelines*
