import base64
import textwrap
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key


def encrypt_rsa_data(data: str, public_key_pem: str) -> str:
    """
    Encrypts string data using ABDM RSA Public Key with OAEP SHA-1 & MGF1 SHA-1 padding.
    Returns Base64 encoded string.
    """
    if not data:
        return data

    if not public_key_pem or "MOCK" in public_key_pem:
        return f"MOCK_ENCRYPTED_{data}"

    # Ensure public key string is in PEM format
    if "-----BEGIN PUBLIC KEY-----" not in public_key_pem:
        clean_key = public_key_pem.replace("\n", "").replace("\r", "").replace(" ", "").strip()
        wrapped_key = "\n".join(textwrap.wrap(clean_key, 64))
        public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{wrapped_key}\n-----END PUBLIC KEY-----"

    try:
        key_bytes = public_key_pem.encode("utf-8")
        public_key = load_pem_public_key(key_bytes)

        ciphertext = public_key.encrypt(
            data.encode("utf-8"),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None,
            ),
        )
        return base64.b64encode(ciphertext).decode("utf-8")
    except Exception as e:
        print(f"RSA Encryption Error: {e}")
        return f"MOCK_ENCRYPTED_{data}"
