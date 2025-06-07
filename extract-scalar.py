#!/usr/bin/env python3
import base64
import struct
import sys
import json

def read_string(data, offset):
    if offset + 4 > len(data):
        raise ValueError("Unexpected end of data while reading length")
    length = struct.unpack(">I", data[offset:offset+4])[0]
    start = offset + 4
    end = start + length
    if end > len(data):
        raise ValueError("Unexpected end of data while reading string content")
    return data[start:end], end

def extract_scalar_and_comment(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    if not (lines[0].startswith('-----BEGIN OPENSSH PRIVATE KEY-----') and
            lines[-1].startswith('-----END OPENSSH PRIVATE KEY-----')):
        raise ValueError("Not a valid OpenSSH private key file")

    b64 = ''.join(lines[1:-1]).replace('\n', '')
    blob = base64.b64decode(b64)

    offset = len(b'openssh-key-v1\0')
    _, offset = read_string(blob, offset)  # cipher name
    _, offset = read_string(blob, offset)  # kdf name
    _, offset = read_string(blob, offset)  # kdf options
    offset += 4                             # number of keys
    _, offset = read_string(blob, offset)  # public key
    private_block, _ = read_string(blob, offset)

    poffset = 8                             # skip checkints
    _, poffset = read_string(private_block, poffset)  # key type
    _, poffset = read_string(private_block, poffset)  # pubkey
    privkey_inner, poffset = read_string(private_block, poffset)
    comment, _ = read_string(private_block, poffset)

    scalar_b64 = base64.b64encode(privkey_inner[:32]).decode()
    comment_str = comment.decode(errors="replace").strip()

    return [scalar_b64] if not comment_str else [scalar_b64, comment_str]

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: extract-scalar.py id_ed25519", file=sys.stderr)
        sys.exit(1)

    result = extract_scalar_and_comment(sys.argv[1])
    print(json.dumps(result, separators=(",", ":")))

