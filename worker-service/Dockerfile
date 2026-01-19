# ==========================================
# STAGE 1: Builder
# ==========================================
FROM rust:1.73 as builder

WORKDIR /usr/src/worker-service

COPY . .

RUN cargo install --path .

# ==========================================
# STAGE 2: Runtime
# ==========================================
FROM debian:buster-slim AS runtime

COPY --from=builder /usr/local/cargo/bin/worker-service /usr/local/bin/worker-service

CMD ["worker-service"]
