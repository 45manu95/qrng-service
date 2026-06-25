from celery import Celery
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
import redis
import time
import os

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
IBM_TOKEN = os.environ.get("IBM_TOKEN", "your_default_token")
REDIS_URL = f"redis://{REDIS_HOST}:6379/0"

# 1. Initialize Celery using Redis as both the Broker (message queue) and the Backend
app = Celery('qrng_tasks', broker=REDIS_URL, backend=REDIS_URL)

# Connection to Redis for the entropy pool
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
POOL_KEY = "quantum_entropy_pool"
LOCK_KEY = "quantum_job_pending"

@app.task(name="tasks.refill_entropy_pool")
def refill_entropy_pool():
    """Background task that queries IBM Quantum and refills the Redis pool"""
    print("Starting background quantum task...")
    
    try:
        # Authentication
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=IBM_TOKEN)
        
        # Select a real quantum computer (not a simulator) currently online (operational=True) with the shortest queue
        backend = service.least_busy(operational=True, simulator=False)
        print(f"Backend selected by the worker: {backend.name}")
        
        # Build the circuit (5 qubits)
        n_qubits = 5
        qc = QuantumCircuit(n_qubits, n_qubits)
        for i in range(n_qubits):
            qc.h(i)
        qc.measure(range(n_qubits), range(n_qubits))
        
        # Transpilation and job submission
        transpiled_qc = transpile(qc, backend=backend)
        sampler = Sampler(backend)
        
        print("Submitting job to IBM...")
        job = sampler.run([transpiled_qc], shots=10000)
        
        # Asynchronous monitoring without permanently blocking the worker if something fails
        print(f"Job successfully submitted. ID: {job.job_id()}. Waiting for results...")
        result = job.result()
        
        # Extract data (SamplerV2 format)
        pub_result = result[0]
        data = pub_result.data.c
        bitstring_list = data.get_bitstrings()
        
        # Join all extracted bits into a single string
        raw_bits = "".join(bitstring_list)
        
        # Clean the raw entropy
        clean_bits = von_neumann_extractor(raw_bits)
        
        # Save ONLY the purified bits to Redis
        if clean_bits:
            r.append(POOL_KEY, clean_bits)
        
        current_size = r.strlen(POOL_KEY)
        print(f"SUCCESS! Added {len(raw_bits)} bits. Current pool size: {current_size} bits.")
        return f"Added {len(raw_bits)} bits from backend {backend.name}"
        
    except Exception as e:
        print(f"ERROR during task execution: {str(e)}")
        return f"Failed: {str(e)}"
    finally:
        r.delete(LOCK_KEY)

import re

def von_neumann_extractor(raw_bits: str) -> str:
    """Applies the Von Neumann extractor using optimized regular expressions."""
    # Split the string into non-overlapping pairs
    pairs = re.findall('..', raw_bits)
    
    # Map valid pairs directly and discard the others ('00' and '11')
    clean_bits = ['0' if p == '01' else '1' for p in pairs if p in ('01', '10')]
    
    return "".join(clean_bits)