"""Encrypt and decrypt backup files (AES-256-GCM, streamed in 1 MiB chunks).

    python ffcrypt.py encrypt <in> <out>      key from FLOWFORGE_BACKUP_KEY (base64, 32 bytes)
    python ffcrypt.py decrypt <in> <out>
    python ffcrypt.py verify  <encrypted> <plain>   exit 0 when they match
    python ffcrypt.py encrypt-tree <folder>   every file not already .enc -> .enc, verified,
                                              then the plain file is deleted

File: b"KRVBK1" + 4-byte key id + 8-byte nonce prefix, then chunks of
[4-byte length][ciphertext+tag]. Each chunk's nonce is prefix + counter and its
authenticated data marks the last chunk, so reordering, truncation or tampering fails.
"""

import base64
import hashlib
import os
import struct
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"KRVBK1"
CHUNK = 1024 * 1024


def _key() -> bytes:
    raw = os.environ.get("FLOWFORGE_BACKUP_KEY", "")
    key = base64.b64decode(raw) if raw else b""
    if len(key) != 32:
        sys.exit("FLOWFORGE_BACKUP_KEY must be set to 32 random bytes, base64-encoded")
    return key


def _kid(key: bytes) -> bytes:
    return hashlib.sha256(b"krov-backup-key" + key).digest()[:4]


def encrypt(src: Path, dst: Path) -> None:
    key = _key()
    aes = AESGCM(key)
    prefix = os.urandom(8)
    tmp = dst.with_name(dst.name + ".part")
    with src.open("rb") as fin, tmp.open("wb") as fout:
        fout.write(MAGIC + _kid(key) + prefix)
        counter = 0
        chunk = fin.read(CHUNK)
        while True:
            following = fin.read(CHUNK)
            last = not following
            nonce = prefix + struct.pack(">I", counter)
            sealed = aes.encrypt(nonce, chunk, MAGIC + struct.pack(">I?", counter, last))
            fout.write(struct.pack(">I", len(sealed)) + sealed)
            if last:
                break
            chunk = following
            counter += 1
    tmp.replace(dst)


def decrypt_chunks(src: Path):  # type: ignore[no-untyped-def]
    key = _key()
    aes = AESGCM(key)
    with src.open("rb") as fin:
        header = fin.read(len(MAGIC) + 12)
        if header[: len(MAGIC)] != MAGIC:
            sys.exit(f"{src} is not an encrypted Krov WorkAgent backup")
        if header[len(MAGIC) : len(MAGIC) + 4] != _kid(key):
            sys.exit(f"{src} was encrypted with a different backup key")
        prefix = header[len(MAGIC) + 4 :]
        counter = 0
        while True:
            size_raw = fin.read(4)
            if len(size_raw) != 4:
                sys.exit(f"{src} is incomplete (cut off)")
            sealed = fin.read(struct.unpack(">I", size_raw)[0])
            nonce = prefix + struct.pack(">I", counter)
            for last in (False, True):
                try:
                    plain = aes.decrypt(nonce, sealed, MAGIC + struct.pack(">I?", counter, last))
                    break
                except Exception:  # noqa: BLE001,S112 - try the other "last" flag
                    continue
            else:
                sys.exit(f"{src} is damaged or was changed")
            yield plain
            if last:
                if fin.read(1):
                    sys.exit(f"{src} has extra data after the end")
                return
            counter += 1


def decrypt(src: Path, dst: Path) -> None:
    tmp = dst.with_name(dst.name + ".part")
    with tmp.open("wb") as fout:
        for plain in decrypt_chunks(src):
            fout.write(plain)
    tmp.replace(dst)


def digest_plain(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def digest_encrypted(path: Path) -> str:
    h = hashlib.sha256()
    for plain in decrypt_chunks(path):
        h.update(plain)
    return h.hexdigest()


def encrypt_verified(src: Path) -> Path:
    dst = src.with_name(src.name + ".enc")
    encrypt(src, dst)
    if digest_encrypted(dst) != digest_plain(src):
        dst.unlink(missing_ok=True)
        sys.exit(f"verification failed for {src}; the plain file was kept")
    src.unlink()
    return dst


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    command = sys.argv[1]
    if command == "encrypt":
        encrypt(Path(sys.argv[2]), Path(sys.argv[3]))
    elif command == "decrypt":
        decrypt(Path(sys.argv[2]), Path(sys.argv[3]))
    elif command == "verify":
        same = digest_encrypted(Path(sys.argv[2])) == digest_plain(Path(sys.argv[3]))
        sys.exit(0 if same else 1)
    elif command == "encrypt-file":
        print(encrypt_verified(Path(sys.argv[2])))
    elif command == "encrypt-tree":
        count = 0
        for path in sorted(Path(sys.argv[2]).rglob("*")):
            if path.is_file() and not path.name.endswith((".enc", ".part")):
                encrypt_verified(path)
                count += 1
        print(f"encrypted {count} file(s) under {sys.argv[2]}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
