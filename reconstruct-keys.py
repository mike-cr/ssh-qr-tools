#!/usr/bin/env python3
import base64
import struct
import sys
import json
import argparse
from cryptography.hazmat.primitives.asymmetric import ed25519

def encode_string(s):
    return struct.pack(">I", len(s)) + s

def build_openssh_key(scalar, comment=b""):
    if len(scalar) != 32:
        raise ValueError("Scalar must be exactly 32 bytes")

    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(scalar)
    public_key = private_key.public_key().public_bytes_raw()

    key_type = b"ssh-ed25519"
    pubkey_blob = encode_string(key_type) + encode_string(public_key)
    privkey_blob = scalar + public_key
    openssh_pubkey = encode_string(key_type) + encode_string(public_key)

    checkint = struct.pack(">I", 0x11223344)
    private_inner = (
        checkint + checkint +
        encode_string(key_type) +
        encode_string(public_key) +
        encode_string(privkey_blob) +
        encode_string(comment)
    )

    pad_len = 8 - (len(private_inner) % 8)
    padding = bytes((i + 1 for i in range(pad_len)))
    private_inner += padding

    openssh_blob = b''.join([
        b"openssh-key-v1\0",
        encode_string(b"none"),
        encode_string(b"none"),
        encode_string(b""),
        struct.pack(">I", 1),
        encode_string(openssh_pubkey),
        encode_string(private_inner)
    ])

    privkey_text = (
        b"-----BEGIN OPENSSH PRIVATE KEY-----\n" +
        base64.encodebytes(openssh_blob) +
        b"-----END OPENSSH PRIVATE KEY-----\n"
    )

    pubkey_b64 = base64.b64encode(pubkey_blob).decode()
    pubkey_line = f"ssh-ed25519 {pubkey_b64} {comment.decode(errors='replace')}\n"

    return privkey_text, pubkey_line

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstruct OpenSSH Ed25519 key from scalar JSON array.")
    parser.add_argument("json_input", help="Path to JSON array input or '-' for stdin")
    parser.add_argument("output_prefix", nargs="?", help="Output filename (omit for stdout)")
    parser.add_argument("--pubkey-to-stdout", action="store_true", help="Print only the pubkey to stdout")

    args = parser.parse_args()

    # Load JSON array input
    if args.json_input == "-":
        data = json.load(sys.stdin)
    else:
        with open(args.json_input, "r") as f:
            data = json.load(f)

    if not isinstance(data, list) or not (1 <= len(data) <= 2):
        print("❌ Input must be a JSON array with 1 or 2 elements: [scalar_b64, optional_comment]", file=sys.stderr)
        sys.exit(1)

    scalar = base64.b64decode(data[0])
    comment = data[1].encode() if len(data) > 1 else b""

    privkey_text, pubkey_line = build_openssh_key(scalar, comment)

    if args.output_prefix:
        with open(args.output_prefix, "wb") as f:
            f.write(privkey_text)
        with open(args.output_prefix + ".pub", "w") as f:
            f.write(pubkey_line)
        print(f"✅ Private key written to {args.output_prefix}")
        print(f"✅ Public key written to {args.output_prefix}.pub")
    elif args.pubkey_to_stdout:
        sys.stdout.write(pubkey_line)
    else:
        sys.stdout.buffer.write(privkey_text)

