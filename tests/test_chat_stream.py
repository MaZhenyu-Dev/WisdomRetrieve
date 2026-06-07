import json
import unittest

from app.api.chat import _format_sse
from app.schemas.chat import ChatRequest


class ChatStreamTests(unittest.TestCase):
    def test_chat_request_stream_defaults_to_false(self) -> None:
        request = ChatRequest(session_id="demo", question="hello")

        self.assertFalse(request.stream)

    def test_chat_request_accepts_stream_true(self) -> None:
        request = ChatRequest(session_id="demo", question="hello", stream=True)

        self.assertTrue(request.stream)

    def test_format_sse_serializes_event_data(self) -> None:
        event = _format_sse("answer_delta", {"content": "hello"})

        self.assertTrue(event.startswith("event: answer_delta\n"))
        payload = event.split("data: ", 1)[1].strip()
        self.assertEqual(json.loads(payload), {"content": "hello"})


if __name__ == "__main__":
    unittest.main()
