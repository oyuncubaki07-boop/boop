def run_action(params):
    limit = params['limit']
    
    # Memory-optimized approach using a generator and trial division.
    # This avoids allocating a large boolean array for the sieve upfront,
    # which saves RAM, especially for very large limits.
    # It builds a list of primes incrementally to use for trial division.
    
    def generate_primes_memory_optimized(n_limit):
        if n_limit >= 2:
            yield 2
        
        # Stores primes found so far. This list will grow but remains
        # significantly smaller than a full boolean sieve array for n_limit=10000
        # (1229 primes up to 10000).
        primes_found = [2]
        
        # Only check odd numbers starting from 3 as potential primes
        for num in range(3, n_limit + 1, 2):
            is_prime_candidate = True
            # Iterate through known primes to check divisibility.
            # Optimization: Only need to check divisors up to sqrt(num).
            for p in primes_found:
                if p * p > num:
                    break # If p*p exceeds num, num cannot have any prime factors larger than p
                if num % p == 0:
                    is_prime_candidate = False
                    break
            
            if is_prime_candidate:
                primes_found.append(num) # Add new prime to the list of known primes
                yield num # Yield the prime number (generator pattern)
                
    # Collect all primes from the generator into a list to return.
    return list(generate_primes_memory_optimized(limit))