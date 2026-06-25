import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import redis
import secrets

# Initialize the FastAPI app
app = FastAPI(
    title="Cloud QRNG Service",
    description="Quantum Random Number Generator API. Provides certified real entropy.",
    version="1.0.0"
)

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
IBM_TOKEN = os.environ.get("IBM_TOKEN", "default_token")

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
POOL_KEY = "quantum_entropy_pool"

@app.get("/")
def get_status():
    """Returns the current status of the entropy pool."""
    pool_size = r.strlen(POOL_KEY) or 0
    return {
        "status": "online",
        "pool_size_bits": pool_size,
        "message": "Use /api/v1/random to request entropy."
    }

@app.get("/api/v1/random")
def get_random_bytes(
    length: int = Query(32, description="Number of requested bytes (e.g., 32 bytes = 256 bits)", ge=1, le=1024)
):
    """Safely and atomically extracts quantum bytes from the pool."""
    bits_needed = length * 8
    
    # Start a Redis pipeline to handle the transaction
    with r.pipeline() as pipe:
        while True:
            try:
                # Watch the key: if someone else modifies it in the meantime, the transaction fails
                pipe.watch(POOL_KEY)
                current_pool = pipe.get(POOL_KEY)
                
                # If the pool is empty or does not have enough bits
                if not current_pool or len(current_pool) < bits_needed:
                    pipe.unwatch() # Release the lock/watch
                    # FALLBACK: Generate secure classic bytes
                    fallback_bytes = secrets.token_hex(length)
                    return {
                        "bytes_requested": length,
                        "bits_consumed": 0,
                        "hex_data": fallback_bytes,
                        "warning": "Quantum entropy depleted. Data generated via secure classic PRNG (fallback)."
                    }
                
                # Extract the required bits from the beginning of the string
                bits_to_return = current_pool[:bits_needed]
                # Save the rest for future users
                remaining_bits = current_pool[bits_needed:]
                
                # Execute the modification atomically
                pipe.multi()
                pipe.set(POOL_KEY, remaining_bits)
                pipe.execute()
                
                # Convert the binary string (e.g., '1101...') to Hexadecimal format for convenience
                byte_array = bytearray(int(bits_to_return[i:i+8], 2) for i in range(0, len(bits_to_return), 8))
                hex_result = byte_array.hex()
                
                return {
                    "bytes_requested": length,
                    "bits_consumed": bits_needed,
                    "hex_data": hex_result
                }
                
            except redis.WatchError:
                # Another user consumed bits simultaneously! 
                # The while loop restarts and automatically retries the operation.
                continue