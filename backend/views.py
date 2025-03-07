from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse
import os
from django.conf import settings
import shutil
from pathlib import Path

from backend.serializers import ImageUploadSerializer
import base64
import io
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd

class FecalInfoAPIView(APIView):
    def get(self, request):
        file_path = "../data/fecal/infos.xlsx"
        images_source_dir = "../data/fecal"
        
        print(f"Excel file path: {os.path.abspath(file_path)}")
        print(f"Images source directory: {os.path.abspath(images_source_dir)}")
        
        # 데이터와 메타 정보 시트 읽기
        data_df = pd.read_excel(file_path, sheet_name="infos", engine="openpyxl")
        meta_df = pd.read_excel(file_path, sheet_name="meta", engine="openpyxl")
        
        # 전체 데이터 변환
        data = data_df.to_dict(orient="records")
        
        # filepath 컬럼이 있다면 절대 경로를 상대 경로로 변환하고 파일 복사
        for item in data:
            if 'filepath' in item and item['filepath']:
                # 파일 경로를 정규화
                filepath = str(item['filepath']).replace('\\', '/').strip('/')
                
                # 원본 파일 경로와 대상 파일 경로 설정
                source_path = os.path.join(images_source_dir, filepath)
                target_path = os.path.join(settings.MEDIA_ROOT, filepath)
                
                # 대상 디렉토리가 없으면 생성
                target_dir = os.path.dirname(target_path)
                if not os.path.exists(target_dir):
                    print(f"Creating directory: {target_dir}")
                    os.makedirs(target_dir, exist_ok=True)
                
                # 파일이 존재하고 아직 복사되지 않았다면 복사
                if os.path.exists(source_path) and not os.path.exists(target_path):
                    try:
                        shutil.copy2(source_path, target_path)
                        print(f"파일 복사 성공: {filepath}")
                    except Exception as e:
                        print(f"파일 복사 실패 ({filepath}): {str(e)}")
                elif not os.path.exists(source_path):
                    print(f"원본 파일이 없습니다: {source_path}")
                    # 원본 디렉토리의 파일 목록 출력
                    print("Files in source directory:")
                    source_dir = os.path.dirname(source_path)
                    if os.path.exists(source_dir):
                        for file in os.listdir(source_dir):
                            print(f"- {file}")
                    else:
                        print(f"Source directory does not exist: {source_dir}")
        
        # 메타 정보 변환 (전체 컬럼 정보 포함)
        columns_meta = meta_df[['col_id', 'col_name', 'hide']].to_dict(orient="records")
        
        response_data = {
            'data': data,
            'columns': columns_meta
        }
        
        return Response(response_data)
    

load_dotenv('.env')
XAI_API_KEY = os.getenv("XAI_API_KEY")
    
@api_view(['POST'])
def get_analysis_result(request):
    print("Request data:", request.data)  # 요청 데이터 출력
    print("Files:", request.FILES)  # 파일 데이터 출력
    
    try:
        serializer = ImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
            return Response(
                {'error': '유효하지 않은 이미지 데이터입니다.', 'details': serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        image = serializer.validated_data['image']
        
        # 이미지 처리
        image_bytes = io.BytesIO()
        img = Image.open(image)
        img.save(image_bytes, format=img.format or "PNG")
        image_bytes.seek(0)
        
        base64_image = base64.b64encode(image_bytes.getvalue()).decode("utf-8")
        


        client = OpenAI(
            api_key=XAI_API_KEY,
            base_url="https://api.x.ai/v1",
        )
        
        completion = client.chat.completions.create(
            model="grok-2-vision-1212",
            temperature=0.9,
            messages=[
                {"role": "system", "content": "너는 숙련된 [소화기내과 전문의]고, 나에게 대변 분석결과에 대해 답변을 해줄 [의무]가 있어."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": """
                         [대변 분석항목]:
                         - 질감 : 
                         - 형태 :
                         - 출혈 여부:
                         - 기타 의견 :
                         - Bristol stool scale :
                         - Ulcerative Colitis Endoscopic Index of Severity (UCEIS) score :
                         대변을 분석해서 위의 항목에 대해 자세히 설명해줘
                         """},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                            }
                        },
                    ],
                }
            ],
        )

        return Response(
            {'data': {'result': completion.choices[0].message.content}}, 
            status=status.HTTP_200_OK
        )

    except Exception as e:
        print(f"Error processing image: {str(e)}")  # 에러 로깅 추가
        return Response(
            {'error': '분석 중 오류가 발생했습니다.', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_image(request, image_path):
    try:
        # 이미지 파일의 전체 경로 생성
        full_path = os.path.join(settings.MEDIA_ROOT, image_path)
        
        # media 디렉토리의 파일 목록 출력
        for root, dirs, files in os.walk(settings.MEDIA_ROOT):
            for file in files:
                print(f"- {file}")
        
        # 파일이 존재하는지 확인
        if not os.path.exists(full_path):
            return Response(
                {"error": f"이미지를 찾을 수 없습니다. 요청된 경로: {full_path}"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # 이미지 파일 반환
        return FileResponse(open(full_path, 'rb'))
        
    except Exception as e:
        print(f"Error in get_image: {str(e)}")
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_image_by_id(request, image_id):
    try:
        # Excel 파일에서 해당 ID의 filepath 찾기
        data_dir = "../data/fecal"
        file_path = os.path.join(data_dir, "infos.xlsx")
        data_df = pd.read_excel(file_path, sheet_name="infos", engine="openpyxl")
        
        # ID로 데이터 찾기
        row = data_df[data_df['id'] == image_id]
        if row.empty:
            return Response(
                {"error": f"ID {image_id}에 해당하는 데이터를 찾을 수 없습니다."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # filepath 가져오기
        filepath = row['filepath'].iloc[0]
        if pd.isna(filepath):
            return Response(
                {"error": f"ID {image_id}에 해당하는 이미지 경로가 없습니다."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # 파일 경로 정규화
        filepath = str(filepath).replace('\\', '/').strip('/')
        
        
        # 이미지 파일의 전체 경로 생성
        full_path = os.path.join(data_dir, filepath)
        
        
        # 파일이 존재하는지 확인
        if not os.path.exists(full_path):
            return Response(
                {"error": f"이미지 파일을 찾을 수 없습니다. (ID: {image_id}, 경로: {filepath})"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # 이미지 파일 반환
        return FileResponse(open(full_path, 'rb'))
        
    except Exception as e:
        print(f"Error in get_image_by_id: {str(e)}")
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )