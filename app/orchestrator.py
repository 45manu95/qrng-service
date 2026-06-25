import os
import redis
import time
from app.tasks import refill_entropy_pool

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

POOL_KEY = "quantum_entropy_pool"
LOCK_KEY = "quantum_job_pending"
MIN_THRESHOLD = 50000

def monitor_and_recharge():
    print("QRNG Orchestrator started. Monitoring the pool...")
    
    while True:
        pool_size = r.strlen(POOL_KEY) or 0
        print(f"Current pool status: {pool_size} bits available.")
        
        if pool_size < MIN_THRESHOLD:
            # Try to acquire the lock (expires automatically after 2 hours as a failsafe)
            lock_acquired = r.set(LOCK_KEY, "1", ex=7200, nx=True)
            
            if lock_acquired:
                print("WARNING: Low entropy! Launching quantum task and setting lock...")
                refill_entropy_pool.delay()
            else:
                print("Low entropy, but a quantum task is already queued. Waiting...")
        
        time.sleep(30)

if __name__ == "__main__":
    monitor_and_recharge()