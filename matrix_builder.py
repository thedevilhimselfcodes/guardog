import json
import struct
import hashlib

class DFAMatrixBuilder:
    MAX_STATES = 15000 

    def __init__(self):
        self.states = []
        self.tags = {}
        self._add_state() 
        
    def _add_state(self):
        if len(self.states) >= self.MAX_STATES:
            raise MemoryError("FATAL: State Explosion Detected.")
        self.states.append([0] * 256)
        return len(self.states) - 1

    def _get_valid_ascii(self, char_class):
        valid = []
        if char_class in ["digits", "alphanumeric"]: valid.extend(range(48, 58))
        if char_class == "alphanumeric":
            valid.extend(range(65, 91))
            valid.extend(range(97, 123))
        if char_class == "jwt_chars":
            valid.extend(range(48, 58))
            valid.extend(range(65, 91))
            valid.extend(range(97, 123))
            valid.extend([45, 46, 95]) 
        return valid

    def _apply_class(self, state_idx, target_state, char_class):
        for i in self._get_valid_ascii(char_class):
            if self.states[state_idx][i] == 0:
                self.states[state_idx][i] = target_state

    def _setup_continuation(self, terminal_state, body_class, is_variable):
        if is_variable:
            self._apply_class(terminal_state, -terminal_state, body_class)

    def add_rule(self, name, prefix, body_class, min_length, is_variable):
        current_state = 0
        for idx, char in enumerate(prefix):
            ascii_val = ord(char)
            if self.states[current_state][ascii_val] == 0:
                self.states[current_state][ascii_val] = self._add_state()
            next_state = self.states[current_state][ascii_val]
            
            if min_length == 0 and idx == len(prefix) - 1:
                self.states[current_state][ascii_val] = -next_state
                self.tags[next_state] = f"[{name}]"
                self._setup_continuation(next_state, body_class, is_variable)
            current_state = next_state if next_state > 0 else -next_state
            
        for idx in range(min_length):
            new_state = self._add_state()
            is_last = (idx == min_length - 1)
            target = -new_state if is_last else new_state
            if is_last:
                self.tags[new_state] = f"[{name}]"
                self._setup_continuation(new_state, body_class, is_variable)
            self._apply_class(current_state, target, body_class)
            current_state = new_state

    def export_binary(self, matrix_out="guardog.matrix", meta_out="guardog_meta.json"):
        print(f"[*] Compiling Binary Matrix: {len(self.states)} states...")
        
        binary_data = bytearray()
        for row in self.states:
            binary_data.extend(struct.pack('<256i', *row))
            
        # Write binary file
        with open(matrix_out, "wb") as f:
            f.write(binary_data)
            
        # Generate Cryptographic Hash of the matrix
        matrix_hash = hashlib.sha256(binary_data).hexdigest()
                
        # Package tags AND the security signature
        metadata = {
            "signature": matrix_hash,
            "tags": [self.tags.get(i, "") for i in range(len(self.states))]
        }
        
        with open(meta_out, "w") as f:
            json.dump(metadata, f)
            
        print(f"[+] Security Signature Generated: {matrix_hash[:12]}...")

if __name__ == "__main__":
    with open("secrets.json", "r") as f:
        config = json.load(f)
    builder = DFAMatrixBuilder()
    for rule in config.get("rules", []):
        builder.add_rule(
            rule["name"], rule.get("prefix", ""), rule["body_class"], 
            rule["min_length"], rule.get("is_variable", False)
        )
    builder.export_binary()