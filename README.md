# 🌌 Cloud QRNG (Quantum Random Number Generator)

**Ultra-high entropy Randomness-as-a-Service**, powered by real IBM quantum hardware and certified by the NIST SP 800-22 statistical suite.

Much of modern cryptography relies on pseudo-random number generators (PRNGs), which depend on deterministic algorithms. This project overcomes the limitation of determinism by extracting **true quantum entropy** from the collapse of superposition states generated on physical quantum processors (via Hadamard gates).

---

## 🚀 Architecture & Engineering

This is not just a simple script, but an asynchronous microservices architecture designed to mask the high latency of cloud-based quantum hardware.
* **FastAPI (Backend):** Exposes ultra-low latency RESTful endpoints for seed extraction.
* **Redis (In-Memory Pool):** Acts as a reservoir for pre-computed entropy. Extractions are performed via **atomic transactions** (`Redis WATCH/MULTI`) to prevent race conditions among concurrent users.
* **Celery & RabbitMQ/Redis (Asynchronous Worker):** A background worker monitors the reservoir level and communicates asynchronously with the IBM Quantum API to replenish it without blocking the web server.
* **Qiskit:** Interface for building and transpiling quantum circuits.

---

## 🔬 Entropy Quality (Post-Processing)

Real quantum hardware is prone to noise and thermal decay, which can generate bias (e.g., a slight prevalence of 0s over 1s). This project implements a cleaning pipeline:

* **Von Neumann Extractor:** A de-biasing algorithm applied in real-time by the worker to perfectly balance the probability distribution.
* **Statistical Validation (NIST):** An integrated script to test bit pools against the **NIST SP 800-22** suite (*Frequency Test*, *Runs Test*, etc.) before they are served.

