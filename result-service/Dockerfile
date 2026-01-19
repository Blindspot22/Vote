# ==========================================
# STAGE 1: Builder
# ==========================================
FROM python:3.9-slim AS builder

WORKDIR /app

# Install build dependencies if needed (though binary wheel usually works)
# RUN apt-get update && apt-get install -y libpq-dev gcc

COPY requirements.txt .
RUN pip install --user -r requirements.txt

COPY . .

# ==========================================
# STAGE 2: Tester
# ==========================================
FROM builder AS tester
RUN python -m pytest test_app.py

# ==========================================
# STAGE 3: Runtime
# ==========================================
FROM python:3.9-slim AS runtime

WORKDIR /app

# Copy dependencies
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

ENV PATH=/root/.local/bin:$PATH

EXPOSE 80

CMD ["gunicorn", "-b", "0.0.0.0:80", "app:app"]
