import base64
import time
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes, serialization

# 공개키 (PEM 형식)
PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----

-----END PUBLIC KEY-----
"""

def encrypt_timestamp():
    # 현재 타임스탬프 (초 단위)
    timestamp = str(int(time.time()))
    print("원본 타임스탬프:", timestamp)

    # 공개키 로드
    public_key = serialization.load_pem_public_key(PUBLIC_KEY_PEM.encode())

    # RSA-OAEP 암호화
    encrypted = public_key.encrypt(
        timestamp.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Base64 인코딩
    encrypted_base64 = base64.b64encode(encrypted).decode()
    print("암호화된 타임스탬프:", encrypted_base64)

    return encrypted_base64

if __name__ == "__main__":
    encrypt_timestamp()