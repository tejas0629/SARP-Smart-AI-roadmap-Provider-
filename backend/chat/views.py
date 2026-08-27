from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatMessage
from .serializers import ChatRequestSerializer
from .services import GeminiConfigurationError, generate_learning_response


class ChatAPIView(APIView):
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_message = serializer.validated_data['message']

        try:
            ai_response, roadmap = generate_learning_response(user_message)
        except GeminiConfigurationError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            return Response(
                {'error': 'AI service is temporarily unavailable. Please try again shortly.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        try:
            ChatMessage.objects.bulk_create([
                ChatMessage(role='user', message=user_message),
                ChatMessage(role='assistant', message=ai_response),
            ])
        except Exception:
            pass

        payload = {'response': ai_response}
        if roadmap:
            payload['roadmap'] = roadmap
        return Response(payload)
