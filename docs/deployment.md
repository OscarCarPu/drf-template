# Deployment

## Production Docker Compose

Start production services:

```bash
docker compose -f docker-compose.prod.yml up -d
```

### Differences from Development

| Aspect | Development | Production |
|---|---|---|
| Web server | `manage.py runserver` | Gunicorn |
| Source code | Volume-mounted (`./src:/app`) | Baked into image |
| Requirements | `requirements/dev.txt` | `requirements/prod.txt` |
| Restart policy | None | `unless-stopped` |
| Resource limits | None | CPU + memory per service |
| Static files | Django serves them | WhiteNoise |
| Ports (Redis) | Exposed (6379) | Internal only |

### Resource Limits

Defined in `docker-compose.prod.yml`:

| Service | CPU | Memory |
|---|---|---|
| backend | 1.0 | 512 MB |
| celeryworker | 0.5 | 256 MB |
| celerybeat | 0.25 | 128 MB |
| postgres | 1.0 | 512 MB |
| redis | 0.25 | 128 MB |

<!-- TODO: Adjust resource limits based on your actual workload and server capacity. -->

## Environment Variables

All variables are read from `.env`. See `.env.example` for defaults.

### Required for Production

| Variable | Example | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | `<random 50+ char string>` | Cryptographic signing key |
| `DJANGO_DEBUG` | `False` | **Must be False in production** |
| `DJANGO_ALLOWED_HOSTS` | `yourdomain.com,www.yourdomain.com` | Comma-separated hostnames |
| `DATABASE_URL` | `postgres://user:pass@host:5432/dbname` | PostgreSQL connection string |
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | Redis broker URL |

### Optional

| Variable | Default | Description |
|---|---|---|
| `GUNICORN_WORKERS` | `4` | Number of Gunicorn worker processes |
| `GUNICORN_TIMEOUT` | `120` | Worker timeout in seconds |
| `CELERY_CONCURRENCY` | `2` | Celery worker process count |
| `CELERY_LOG_LEVEL` | `INFO` | Celery log verbosity |
| `SENTRY_DSN` | _(empty)_ | Sentry error tracking DSN |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Sentry performance sample rate |
| `CORS_ALLOWED_ORIGINS` | _(empty)_ | Comma-separated frontend origins |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` | Email sending backend |

<!-- TODO: Add any project-specific environment variables here. -->

## Gunicorn Tuning

The entrypoint script (`docker/entrypoint.sh`) starts Gunicorn with:

```bash
gunicorn main.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -
```

Rules of thumb:

- **Workers**: `2 * CPU_CORES + 1` (e.g., 2 cores → 5 workers)
- **Timeout**: Increase if you have long-running API endpoints (default 120s is generous)
- Logs go to stdout/stderr for container log aggregation.

## Static Files

Static files are served by **WhiteNoise** (middleware already enabled in `base.py`). The entrypoint runs `collectstatic --noinput` before starting Gunicorn.

For large-scale deployments, consider offloading to S3 + CloudFront:

1. Install `django-storages` and `boto3`.
2. Configure `DEFAULT_FILE_STORAGE` and `STATICFILES_STORAGE` in settings.
3. Set `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, etc. as environment variables.

<!-- TODO: Configure S3/CDN static file storage if needed. -->

## Monitoring

### Sentry

Error tracking is pre-configured in `src/main/settings/sentry.py`. Set `SENTRY_DSN` to enable:

```bash
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
```

Performance tracing is enabled at 10% sample rate by default (`SENTRY_TRACES_SAMPLE_RATE`).

### Flower

Celery monitoring via Flower is available as a Docker service. In production, secure it behind authentication or a reverse proxy.

<!-- TODO: Set up Flower authentication (--basic-auth=user:password) for production. -->

## Pre-Deployment Checklist

- [ ] `DJANGO_DEBUG=False`
- [ ] `DJANGO_SECRET_KEY` set to a unique, unpredictable value
- [ ] `DJANGO_ALLOWED_HOSTS` lists all valid hostnames
- [ ] `DATABASE_URL` points to the production database
- [ ] Database migrations are up to date (`python manage.py migrate`)
- [ ] Static files collected (`python manage.py collectstatic`)
- [ ] `SENTRY_DSN` configured for error tracking
- [ ] HTTPS enabled (via reverse proxy — Nginx, Caddy, or load balancer)
- [ ] `CORS_ALLOWED_ORIGINS` set to actual frontend domain(s)
- [ ] Flower secured with authentication or not exposed publicly
- [ ] Backups configured for PostgreSQL
- [ ] Resource limits reviewed for expected traffic

<!-- TODO: Add project-specific deployment steps (DNS, SSL certificates, CI/CD pipeline). -->
