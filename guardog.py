import guardog_core
import json
import os
import hashlib

class SecurityTamperError(Exception):
    pass

class GuardogSession:
    PARALLEL_THRESHOLD = 5 * 1024 * 1024 

    def __init__(self, matrix_path="guardog.matrix", meta_path="guardog_meta.json"):
        if not os.path.exists(matrix_path) or not os.path.exists(meta_path):
            raise FileNotFoundError("Missing matrix files.")
            
        with open(matrix_path, "rb") as f:
            self.matrix_bytes = f.read()
            
        with open(meta_path, "r") as f:
            metadata = json.load(f)
            
        current_hash = hashlib.sha256(self.matrix_bytes).hexdigest()
        if current_hash != metadata.get("signature", ""):
            raise SecurityTamperError("FATAL: Matrix hash mismatch.")
            
        self.tags_tuple = tuple(metadata.get("tags", []))

    def sanitize(self, payload) -> dict:
        # FAANG FIX: Removed destructive normalization. 
        # Check if input is a string or already a mutable bytearray
        is_string = isinstance(payload, str)
        
        if is_string:
            # String requires allocation and copying
            mutable_buffer = bytearray(payload.encode('utf-8'))
        elif isinstance(payload, bytearray):
            # Bytearray triggers True Zero-Copy path
            mutable_buffer = payload
        else:
            raise TypeError("Payload must be a string or bytearray")
            
        byte_length = len(mutable_buffer)
        
        num_threads = 4 if byte_length > self.PARALLEL_THRESHOLD else 1
        matches = []
        
        guardog_core.redact(
            mutable_buffer, num_threads, self.matrix_bytes, self.tags_tuple, matches
        )
        
        # If a string was passed, return a string. If bytes were passed, return bytes.
        result_data = mutable_buffer.decode('utf-8', errors='replace') if is_string else mutable_buffer
        
        return {"text": result_data, "matches": matches}