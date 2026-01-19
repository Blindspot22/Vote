# ==========================================
# STAGE 1: Builder
# ==========================================
FROM rust:1.58 as builder

WORKDIR /usr/src/vote-service

COPY . .

RUN cargo install --path .

# ==========================================
# STAGE 2: Runtime
# ==========================================
FROM debian:buster-slim AS runtime

COPY --from=builder /usr/local/cargo/bin/vote-service /usr/local/bin/vote-service

CMD ["vote-service"]
