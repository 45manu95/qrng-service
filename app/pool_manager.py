import redis

# Connessione al Redis locale
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

POOL_KEY = "quantum_entropy_pool"

def add_entropy_to_pool(bitstring: str):
    """Aggiunge la stringa di bit al serbatoio."""
    r.append(POOL_KEY, bitstring)
    print(f"Aggiunti {len(bitstring)} bit al pool. Dimensione attuale: {get_pool_size()} bit.")

def get_pool_size() -> int:
    """Restituisce quanti bit ci sono nel serbatoio."""
    return r.strlen(POOL_KEY)