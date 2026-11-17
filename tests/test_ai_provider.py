import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import ai_provider


class TestAiProvider(unittest.TestCase):
    def test_groq_uses_fixed_model_from_code(self):
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="  Hello  "))]
        )
        messages = [{"role": "user", "content": "Hi"}]
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            with patch.object(ai_provider, "Groq") as groq:
                groq.return_value.chat.completions.create.return_value = response
                reply = ai_provider.generate_chat_reply(messages)

        self.assertEqual(reply, "Hello")
        groq.return_value.chat.completions.create.assert_called_once_with(
            model="openai/gpt-oss-20b",
            messages=messages,
            max_tokens=600,
        )


if __name__ == "__main__":
    unittest.main()
