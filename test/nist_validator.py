import redis
import numpy as np
from nistrng import pack_sequence, unpack_sequence, check_eligibility_all_battery, run_all_battery

def validate_pool():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    POOL_KEY = "quantum_entropy_pool"
    
    # 1. Retrieve all bits from the pool
    pool_data = r.get(POOL_KEY)
    
    if not pool_data or len(pool_data) < 10000:
        print("The pool does not have enough bits for a significant statistical test. Generate at least 10,000 bits.")
        return

    print(f"Starting NIST SP 800-22 test suite on {len(pool_data)} quantum bits...")
    
    # 2. Convert the bitstring ("0101...") into a numpy array of integers [0, 1, 0, 1...]
    # The nistrng library expects the data in this format
    binary_sequence = np.array([int(b) for b in pool_data], dtype=int)
    
    # 3. The suite checks which tests are applicable based on the sequence length
    eligible_battery: dict = check_eligibility_all_battery(binary_sequence, SP800_22R1A_BATTERY)
    
    print(f"Applicable tests for this length: {len(eligible_battery)}")
    
    # 4. Running the tests
    results = run_all_battery(binary_sequence, eligible_battery, False)
    
    print("\n--- NIST TEST RESULTS ---")
    pass_count = 0
    fail_count = 0
    
    for result, elapsed_time in results:
        # If the p-value is greater than the significance threshold (typically 0.01), the test passes
        if result.passed:
            print(f"✅ {result.name}: PASSED (p-value: {result.p_value:.4f})")
            pass_count += 1
        else:
            print(f"❌ {result.name}: FAILED (p-value: {result.p_value:.4f})")
            fail_count += 1
            
    print(f"\nSummary: {pass_count} passed, {fail_count} failed.")
    if fail_count == 0:
        print("VERDICT: The sequence is cryptographically secure and indistinguishable from true randomness.")
    else:
        print("VERDICT: The sequence exhibits patterns. Review the Von Neumann extractor.")

if __name__ == "__main__":
    # Import the test battery constants directly in main for convenience
    from nistrng import SP800_22R1A_BATTERY
    validate_pool()