# Alembic migration versions

Generated automatically by:

```bash
cd backend
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

Then seed data:

```bash
python -m app.jobs.seed_badges
python -m app.jobs.seed_levels
```
