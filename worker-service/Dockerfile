# ==========================================
# STAGE 1: Builder
# ==========================================
FROM python:3.9-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user -r requirements.txt

COPY . .

# ==========================================
# STAGE 2: Tester
# ==========================================
FROM builder AS tester
RUN python -m pytest test_worker.py

# ==========================================
# STAGE 3: Runtime
# ==========================================
FROM python:3.9-slim AS runtime

# Need to force stdout flushing for Docker logs
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

ENV PATH=/root/.local/bin:$PATH

CMD ["python", "main.py"]
