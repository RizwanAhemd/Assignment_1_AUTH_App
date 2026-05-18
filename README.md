# CORE-AUTH Backend

High-performance, non-blocking asynchronous identity engine built with FastAPI, Async SQLAlchemy, PostgreSQL, and Redis.

## Features
- **Pure Async Architecture:** Scalable performance using `async/await` from endpoint handlers down to persistence drivers.
- **Secure Lifecycle Handling:** Cryptographic JWT management built with dedicated verification contexts for Access and Refresh scopes.
- **Atomic Operations:** Clean architectural patterns using Repositories and Services.
- **Distributed Revocation Layer:** High-speed token blacklisting backed by explicit Redis TTL expirations.

## Local Execution Environment

### Prerequisites
Ensure your local compute context has active instances of:
- PostgreSQL 15+
- Redis Server 7+

### 1. Project Initialization
```bash
# Clone the repository and navigate inside
cd core-auth

# Build local runtime virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt