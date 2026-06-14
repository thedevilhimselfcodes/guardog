import os

def generate_massive_log(filename="1GB_test_payload.log", target_size_gb=1):
    target_bytes = target_size_gb * 1024 * 1024 * 1024
    current_bytes = 0
    
    # A mix of clean logs and logs containing mock secrets
    log_lines = [
        b"INFO 2026-06-14: Server health check passed. CPU at 12%.\n",
        b"DEBUG 2026-06-14: Connection established from 10.0.0.4.\n",
        b"WARN 2026-06-14: API_KEY=AKIAIOSFODNN7EXAMPLE used for transaction.\n",
        b"ERROR 2026-06-14: Payment failed for CREDIT_CARD=4000-1234-5678-9010.\n"
    ]

    print(f"Generating {target_size_gb}GB payload. This might take a minute...")
    with open(filename, "wb") as f:
        while current_bytes < target_bytes:
            for line in log_lines:
                f.write(line)
                current_bytes += len(line)
    
    print(f"Done. Created {filename} ({os.path.getsize(filename) / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    generate_massive_log()