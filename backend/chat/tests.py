from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory

from .services import generate_learning_response
from .views import ChatAPIView


@override_settings(
    GEMINI_API_KEY='gemini-test-key',
    GEMINI_MODEL='gemini-test-model',
    GROQ_API_KEY='groq-test-key',
    GROQ_MODEL='groq-test-model',
    DEBUG=False,
)
class ProviderFallbackTests(SimpleTestCase):
    gemini_payload = '{"response":"Gemini response","roadmap":null}'
    groq_payload = '{"response":"Groq response","roadmap":{"goal":"Python"}}'

    def make_gemini_client(self, response_text=None, error=None):
        client = Mock()
        if error:
            client.models.generate_content.side_effect = error
        else:
            client.models.generate_content.return_value = SimpleNamespace(text=response_text)
        return client

    def make_groq_client(self, response_text=None, error=None):
        client = Mock()
        if error:
            client.chat.completions.create.side_effect = error
        else:
            client.chat.completions.create.return_value = SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=response_text))]
            )
        return client

    @patch('chat.services.Groq')
    @patch('chat.services.genai.Client')
    def test_gemini_success_does_not_call_groq(self, gemini_client, groq_client):
        gemini_client.return_value = self.make_gemini_client(self.gemini_payload)

        response = generate_learning_response('Create a roadmap.')

        self.assertEqual(response, ('Gemini response', None))
        gemini_client.assert_called_once()
        groq_client.assert_not_called()

    @patch('chat.services.Groq')
    @patch('chat.services.genai.Client')
    def test_rate_limit_uses_groq_fallback(self, gemini_client, groq_client):
        error = RuntimeError('rate limited')
        error.status_code = 429
        gemini_client.return_value = self.make_gemini_client(error=error)
        groq_client.return_value = self.make_groq_client(self.groq_payload)

        history = [SimpleNamespace(role='user', message='I want to become a Java developer.')]
        response = generate_learning_response('Current exp 0', history)

        self.assertEqual(response, ('Groq response', {'goal': 'Python'}))
        gemini_client.assert_called_once()
        groq_client.assert_called_once()
        groq_messages = groq_client.return_value.chat.completions.create.call_args.kwargs['messages']
        self.assertEqual(groq_messages[1]['content'], 'I want to become a Java developer.')
        self.assertEqual(groq_messages[-1]['content'], 'Current exp 0')

    @patch('chat.services.Groq')
    @patch('chat.services.genai.Client')
    def test_multi_turn_history_is_sent_to_gemini(self, gemini_client, groq_client):
        gemini_client.return_value = self.make_gemini_client(self.gemini_payload)
        history = [
            SimpleNamespace(role='user', message='I want to become a Java developer.'),
            SimpleNamespace(role='assistant', message='What is your current experience?'),
        ]

        generate_learning_response('Current exp 0', history)

        contents = gemini_client.return_value.models.generate_content.call_args.kwargs['contents']
        self.assertEqual(contents[0]['parts'][0]['text'], 'I want to become a Java developer.')
        self.assertEqual(contents[1]['role'], 'model')
        self.assertEqual(contents[-1]['parts'][0]['text'], 'Current exp 0')
        groq_client.assert_not_called()

    @patch('chat.services.genai.Client')
    def test_separate_conversation_history_is_not_mixed(self, gemini_client):
        gemini_client.return_value = self.make_gemini_client(self.gemini_payload)
        first_conversation = [SimpleNamespace(role='user', message='Java developer')]
        second_conversation = [SimpleNamespace(role='user', message='Data analyst')]

        generate_learning_response('Current exp 0', first_conversation)
        generate_learning_response('Current exp 0', second_conversation)

        calls = gemini_client.return_value.models.generate_content.call_args_list
        first_contents = calls[0].kwargs['contents']
        second_contents = calls[1].kwargs['contents']
        self.assertEqual(first_contents[0]['parts'][0]['text'], 'Java developer')
        self.assertEqual(second_contents[0]['parts'][0]['text'], 'Data analyst')
        self.assertNotIn('Java developer', str(second_contents))

    @patch('chat.services.Groq')
    @patch('chat.services.genai.Client')
    def test_server_error_uses_groq_fallback(self, gemini_client, groq_client):
        error = RuntimeError('server error')
        error.status_code = 503
        gemini_client.return_value = self.make_gemini_client(error=error)
        groq_client.return_value = self.make_groq_client(self.groq_payload)

        response = generate_learning_response('Create a roadmap.')

        self.assertEqual(response[0], 'Groq response')
        groq_client.assert_called_once()

    @patch('chat.services.Groq')
    @patch('chat.services.genai.Client')
    def test_timeout_uses_groq_fallback(self, gemini_client, groq_client):
        gemini_client.return_value = self.make_gemini_client(error=TimeoutError())
        groq_client.return_value = self.make_groq_client(self.groq_payload)

        response = generate_learning_response('Create a roadmap.')

        self.assertEqual(response[0], 'Groq response')
        groq_client.assert_called_once()

    @patch('chat.views.ChatMessage.objects.create')
    @patch('chat.views.Conversation.objects.create')
    @patch('chat.services.Groq')
    @patch('chat.services.genai.Client')
    def test_groq_failure_returns_safe_api_error(self, gemini_client, groq_client, create_conversation, create_message):
        gemini_client.return_value = self.make_gemini_client(error=TimeoutError())
        groq_client.return_value = self.make_groq_client(error=RuntimeError('provider detail must stay hidden'))
        create_conversation.return_value.id = 1
        create_conversation.return_value.messages.order_by.return_value = []
        request = APIRequestFactory().post('/api/chat/', {'message': 'Create a roadmap.'}, format='json')

        response = ChatAPIView.as_view()(request)

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data['error'], 'AI service is temporarily unavailable. Please try again shortly.')
        self.assertNotIn('provider detail', response.data['error'])

    @patch('chat.services.Groq')
    @patch('chat.services.genai.Client')
    def test_non_temporary_gemini_error_does_not_use_groq(self, gemini_client, groq_client):
        gemini_client.return_value = self.make_gemini_client(error=ValueError('invalid request'))

        with self.assertRaises(ValueError):
            generate_learning_response('Create a roadmap.')

        groq_client.assert_not_called()
