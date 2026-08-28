from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatMessage, Conversation
from .serializers import ChatRequestSerializer
from .services import (
    GeminiConfigurationError,
    GeminiResponseError,
    GroqConfigurationError,
    GroqResponseError,
    generate_learning_response,
)


class ChatAPIView(APIView):
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_message = serializer.validated_data['message']
        conversation_id = serializer.validated_data.get('conversation_id')
        if conversation_id is None:
            conversation = Conversation.objects.create()
        else:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
            except Conversation.DoesNotExist:
                return Response({'error': 'Conversation not found.'}, status=status.HTTP_404_NOT_FOUND)

        previous_messages = list(conversation.messages.order_by('created_at', 'id'))
        ChatMessage.objects.create(conversation=conversation, role='user', message=user_message)
        conversation.save(update_fields=['updated_at'])

        try:
            ai_response, roadmap = generate_learning_response(user_message, previous_messages)
        except GeminiConfigurationError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except GeminiResponseError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except (GroqConfigurationError, GroqResponseError):
            return Response(
                {'error': 'AI service is temporarily unavailable. Please try again shortly.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception:
            return Response(
                {'error': 'AI service is temporarily unavailable. Please try again shortly.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        try:
            ChatMessage.objects.create(conversation=conversation, role='assistant', message=ai_response)
        except Exception:
            pass

        payload = {'response': ai_response, 'conversation_id': conversation.id}
        if roadmap:
            payload['roadmap'] = roadmap
        return Response(payload)
