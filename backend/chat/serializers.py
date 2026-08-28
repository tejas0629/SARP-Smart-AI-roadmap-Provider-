from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(trim_whitespace=True, allow_blank=False, max_length=4000)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
