from django.http import JsonResponse
import time
import base64
import os
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from dotenv import load_dotenv
from django.conf import settings

load_dotenv()

class RSAAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_paths = ['/admin']
        
        # 개인 키 로드
        try:
            key_path = os.path.abspath(os.path.join(settings.BASE_DIR, 'backend', 'private_key.pem'))

            with open(key_path, 'rb') as key_file:
                self.private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None
                )
        except Exception as e:
            print(f"개인 키 로드 실패: {str(e)}")
            self.private_key = None

    def __call__(self, request):
        # 개인 키가 로드되지 않았으면 오류 반환
        if self.private_key is None:
            return JsonResponse({"error": "서버 인증 시스템이 초기화되지 않았습니다"}, status=500)
            
        # 제외 경로 확인
        if any(request.path.startswith(path) for path in self.exempt_paths):
            return self.get_response(request)

        # 헤더에서 암호화된 타임스탬프 확인
        encrypted_data = request.headers.get('X-Encrypted-Data')
        
        if not encrypted_data:
            return JsonResponse({"error": "인증 데이터가 누락되었습니다"}, status=401)
        
        try:
            # Base64 디코딩 및 복호화
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted_data = self.private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # 복호화된 데이터 파싱 (타임스탬프)
            timestamp = int(decrypted_data.decode('utf-8'))
            
            # 타임스탬프 검증 (5분 이내만 가능)
            current_time = int(time.time())
            if current_time - timestamp > 300:  # 5분
                return JsonResponse({"error": "인증 시간이 만료되었습니다"}, status=401)
                
        except Exception as e:
            return JsonResponse({"error": f"인증 처리 중 오류가 발생했습니다: {str(e)}"}, status=401)
        
        response = self.get_response(request)
        return response