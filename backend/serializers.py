from rest_framework import serializers

class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(
        allow_empty_file=False,
        use_url=False,
        # 허용할 이미지 타입 명시
        allow_null=False,
        required=True
    )

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError("이미지 파일이 필요합니다.")
        return value