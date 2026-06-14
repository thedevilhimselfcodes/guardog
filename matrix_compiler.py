import json
import struct
import hashlib

def compile_rules_to_matrix(rules_dict, output_matrix_path="guardog.matrix", output_meta_path="guardog_meta.json"):
    """
    Compiles text tokens/rules into a highly optimized 256-column DFA state transition table.
    Expects a dictionary mapping tags to exact structural keyword prefixes.
    """
    print(f"[*] Compiling {len(rules_dict)} security signatures into O(1) DFA Matrix...")
    
    tags = list(rules_dict.keys())
    
    # Base state allocation
    # Row 0: Root state. Columns 0-255 map to next state states.
    # Terminal states are designated as negative integers corresponding to the rule index.
    matrix = [0] * 256
    next_free_state = 1
    
    for rule_idx, (tag, keywords) in enumerate(rules_dict.items()):
        for keyword in keywords:
            current_state = 0
            byte_sequence = keyword.encode('utf-8')
            
            for i, byte in enumerate(byte_sequence):
                lookup_idx = (current_state * 256) + byte
                
                # Expand matrix if we are forging a new state pathway
                while len(matrix) <= lookup_idx:
                    matrix.extend([0] * 256)
                    
                if i == len(byte_sequence) - 1:
                    # Final character maps to a negative terminal state index
                    matrix[lookup_idx] = -rule_idx
                else:
                    if matrix[lookup_idx] <= 0:
                        matrix[lookup_idx] = next_free_state
                        next_free_state += 1
                    current_state = abs(matrix[lookup_idx])

    # Serialize matrix to high-performance binary file
    binary_data = bytearray()
    for val in matrix:
        binary_data.extend(struct.pack("i", val))
        
    matrix_hash = hashlib.sha256(binary_data).hexdigest()
    
    with open(output_matrix_path, "wb") as f:
        f.write(binary_data)
        
    metadata = {
        "tags": tags,
        "signature": matrix_hash
    }
    
    with open(output_meta_path, "w") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"[+] Compilation complete. Matrix footprint: {len(binary_data) / 1024:.2f} KB. Signature locked.")

if __name__ == "__main__":
    # Standard template rules that match common hardcoded high-risk credentials
    DEFAULT_RULES = {
        "AWS_KEY": ["AKIAIOSFODNN7EXAMPLE", "AKIAI4769QXI7EXAMPLE"],
        "CREDIT_CARD": ["4111222233334444", "5555444433332222"],
        "JWT_TOKEN": ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"]
    }
    compile_rules_to_matrix(DEFAULT_RULES)