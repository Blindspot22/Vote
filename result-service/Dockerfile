# ==========================================
# STAGE 1: Builder
# ==========================================
FROM rust:1.73 as builder

WORKDIR /usr/src/result-service

COPY . .

RUN cargo install --path .

# ==========================================
# STAGE 2: Runtime
# ==========================================
FROM debian:buster-slim AS runtime

COPY --from=builder /usr/local/cargo/bin/result-service /usr/local/bin/result-service

CMD ["result-service"]
