Backup an openssh Ed25519 privkey by extracting the 32B scalar & comment and generating a QR code. It just stores the 32B scalar (and comment if there is one) to make the QR code smaller. This is intended to be used with a receipt printer so targets a 72mm printing with for 80mm receipt paper. 

## Requirements

To generate the QR code:
  - python3
  - python-lxml
  - qrencode
  - librsvg (if you want PDF or PNG output)
  - cups (if you want to directly print it)

To decode the QR code:
  - zbar (if you have a PNG image)

## Tools

### extract-scalar.py

Extract the scalar and comment (if there is one) from an openssh ED25519 privkey, and print it to stdout. The format is a JSON array like `["base64-encoded-scalar","comment"]`.

#### Usage

```bash
./extract-scalar.py path/to/privkey
```

### key-to-qr.py

Extract the scalar and comment (if there is one) from an openssh ED25519 privkey, and generate a QR code image.

This depends on `extract-scalar.py` existing in the same directory.

#### Usage

Dump resulting SVG to STDOUT:

```bash
./key-to-qr.py path/to/privkey --stdout
```

Save the SVG:

```bash
./key-to-pr.py path/to/privkey --svg filename.svg
```

Output as PDF:

```bash
./key-to-pr.py path/to/privkey --pdf filename.pdf
```

Output as PDF:

```bash
./key-to-pr.py path/to/privkey --pdf filename.pdf
```

Output as PNG:

```bash
./key-to-pr.py path/to/privkey --png filename.png
```

Print via lp:

```bash
./key-to-pr.py path/to/privkey --print
```

### qr-to-key.sh

Produce the openssh privkey and/or pubkey given a QR code in a PNG or the JSON it contained. This depends on recontstruct-keys.py existing in the same directory.

#### Usage

Print privkey to stdout from JSON in stdin:

```bash
cat extracted.json | ./qr-to-key.sh -
```

Print privkey to stdout from a QR code in a PNG:

```bash
./qr-to-key.sh qr-code.png
```

Print pubkey to stdout:

```bash
./qr-to-key.sh qr-code.png --pubkey-to-stdout
```

Save the privkey and pubkey to a file, where the privkey will be named foo and the pubkey will be named foo.pub:

```bash
./qr-to-key.sh qr-code.png --out=foo
```

### reconstruct-keys.py

Read JSON from file or stdin, reconstruct the privkey and pubkey, and save them to a file or print one or the other to stdout. This depends on qr-to-key.sh existing in the same directory.

#### Usage

Print privkey to stdout from JSON in stdin:

```bash
cat extracted.json | ./reconstruct-keys.py -
```

Print privkey to stdout from JSON file:

```bash
./reconstruct-keys.py extracted.json
```

Print pubkey to stdout:

```bash
./reconstruct-keys.py extracted.json --pubkey-to-stdout
```

Save the privkey and pubkey to a file, where the privkey will be named foo and the pubkey will be named foo.pub:

```bash
./reconstruct-keys.py extracted.json foo
```
