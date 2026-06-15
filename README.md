# Billing & Subscription API Gateway with Redis

This project is a high-performance, asynchronous API Gateway simulation designed to handle high-throughput routing to billing microservices. It focuses on resolving critical enterprise backend challenges such as **Idempotency (preventing duplicate transactions)** and **Rate Limiting (DoS/Traffic protection)** using Redis.

## Key Features

- **Asynchronous Routing:** Leverages FastAPI and HTTPX to achieve non-blocking, asynchronous request forwarding to upstream microservices.
- **Distributed Idempotency Lock:** Implements a distributed atomic locking mechanism via Redis `SET ... NX` to intercept and drop duplicate financial transaction requests within microsecond windows.
- **Rate Limiting:** Protects downstream billing systems from traffic spikes and malicious actors by enforcing a strict client-based threshold (e.g., maximum 5 requests per minute per IP).
- **Production-Ready Containerization:** Fully containerized using Docker and orchestrated with Docker Compose for seamless deployment and environment reproducibility.

## Tech Stack

- **Backend Framework:** Python, FastAPI, HTTPX
- **Caching & Distributed Locks:** Redis (Asyncio)
- **DevOps:** Docker, Docker Compose

## System Architecture

The gateway acts as a secure reverse proxy and single entry point. Incoming HTTP traffic passes through a layered protection wall (Rate Limiter ➡️ Idempotency Check) before being safely routed to the upstream billing service.
