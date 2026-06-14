import re
import time
from memory_profiler import profile
from guardog import GuardogSession

# 1. Compile the standard regex rules for the baseline test
regex_rules = re.compile(b"(AKIA[0-9A-Z]{16}|[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4})")

@profile
def test_standard_regex(payload_bytes):
    print("Running Standard re.sub()...")
    start = time.time()
    redacted = regex_rules.sub(b"[REDACTED]", payload_bytes)
    end = time.time()
    print(f"Standard re finished in {end - start:.2f} seconds.")
    return redacted

@profile
def test_guardog_engine(payload_bytearray):
    print("Running GuardogSession.sanitize() in Zero-Copy mode...")
    
    session = GuardogSession()
    
    start = time.time()
    # Passing the bytearray triggers the zero-copy bypass
    result = session.sanitize(payload_bytearray)
    end = time.time()
    
    print(f"Guardog finished in {end - start:.2f} seconds.")
    print(f"Total secrets found: {len(result['matches'])}")

if __name__ == "__main__":
    print("Loading 1GB payload into memory...")
    # Read as raw bytes and create a mutable buffer
    with open("1GB_test_payload.log", "rb") as f:
        raw_bytes = f.read() 
        mutable_buffer = bytearray(raw_bytes) 
    
    print("\n--- STARTING BENCHMARKS ---")
    test_standard_regex(raw_bytes)
    print("\n")
    test_guardog_engine(mutable_buffer)