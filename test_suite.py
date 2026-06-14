import guardog
import sys
import subprocess

def generate_binaries():
    # FIX: Pointing to the new, standalone compiler instead of the old builder
    subprocess.run([sys.executable, "matrix_compiler.py"], check=True, stdout=subprocess.DEVNULL)

def test_thread_boundary_blindspot():
    print("[*] Running Structural: Thread Boundary Overlap Test...")
    session = guardog.GuardogSession()
    
    padding = "A" * int(session.PARALLEL_THRESHOLD / 4)
    boundary_payload = padding + "AKIAIOSFODNN7EXAMPLE" + padding
    
    res = session.sanitize(boundary_payload)
    assert "[AWS_KEY]" in res['text'], "FATAL: Secret dropped at OpenMP thread boundary."
    print("[+] Boundary Integration: PASSED (No blindspots)")

def test_amnesia_overwrite():
    print("[*] Running Structural: Two-Pass Amnesia Overwrite Test...")
    session = guardog.GuardogSession()
    
    overlapping_payload = "AKIAIOSFODNN7EXAMPLEAKIAIOSFODNN7EXAMPLE"
    res = session.sanitize(overlapping_payload)
    
    assert len(res['matches']) == 2, f"FATAL: Dropped overlapping secret. Only found {len(res['matches'])}"
    print("[+] Two-Pass Deferred Mutation: PASSED (Overlaps safely resolved)")

def test_pipeline_integrity():
    print("[*] Running Structural: Pipeline Integrity (No Normalization DoS)...")
    session = guardog.GuardogSession()
    
    legitimate_data = '{"id": "∑123", "lang": "日本語", "secret": "AKIAIOSFODNN7EXAMPLE"}'
    res = session.sanitize(legitimate_data)
    
    assert "∑" in res['text'] and "日本語" in res['text'], "FATAL: Legitimate payload corrupted by engine."
    assert "[AWS_KEY]" in res['text'], "FATAL: Failed to redact inside JSON."
    print("[+] Pipeline Integrity: PASSED (Zero DoS corruption)")

if __name__ == "__main__":
    print("==================================================")
    print(" GUARDOG ENTERPRISE: STRUCTURAL INTEGRITY VALIDATION")
    print("==================================================")
    
    try:
        generate_binaries()
        test_thread_boundary_blindspot()
        test_amnesia_overwrite()
        test_pipeline_integrity()
        print("\n[+] ALL SYSTEMS NOMINAL: The FAANG Architecture is locked.")
    except AssertionError as e:
        print(f"\n[!] VERIFICATION FAILED: {e}")