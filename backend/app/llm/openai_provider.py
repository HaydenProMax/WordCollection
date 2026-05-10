import json

import httpx
from pydantic import ValidationError

from app.config import Settings
from app.llm.base import LLMProvider
from app.schemas import LookupExplanation


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, settings: Settings):
        self.api_key = settings.openai_api_key
        self.model_name = settings.openai_model
        self.base_url = settings.openai_base_url.rstrip("/")

    async def explain(self, text: str) -> LookupExplanation:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        payload = {
            "model": self.model_name,
            "input": self._build_prompt(text),
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(
                    f"{self.base_url}/responses",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                raw = response.json()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"OpenAI request failed with HTTP {exc.response.status_code}.") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError("OpenAI request failed.") from exc

        output_text = raw.get("output_text") or self._extract_output_text(raw)
        if not output_text:
            raise RuntimeError("OpenAI response did not contain output text.")

        try:
            parsed = json.loads(output_text)
            parsed["raw_response"] = raw
            parsed["original"] = text
            return LookupExplanation.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise RuntimeError("OpenAI response did not match the required schema.") from exc

    def _build_prompt(self, text: str) -> str:
        return f"""
You are an English learning assistant for a native Chinese speaker.
You support bidirectional lookup:
- If the input is English, explain it in Chinese.
- If the input is Chinese, provide natural English expressions for it.
Return only valid JSON. Do not return Markdown. Do not include any text outside JSON.

Required JSON schema:
{{
  "original": "string",
  "source_language": "en | zh",
  "target_language": "zh | en",
  "query_type": "word | phrase | sentence",
  "pronunciation": "string, use IPA for English words or phrases; empty string if unsuitable",
  "explanation": "For English input, write a Chinese explanation. For Chinese input, give the most natural English expression and explain usage differences in Chinese when there are alternatives.",
  "examples": [
    {{
      "english": "natural English example",
      "chinese": "Chinese translation"
    }}
  ]
}}

Rules:
- Keep the Chinese explanation concise and practical.
- Provide 2 examples for words and phrases.
- Provide 1-2 examples for sentences.
- Infer whether the input is a word, phrase, or sentence.
- For Chinese input, set source_language to "zh" and target_language to "en".
- For English input, set source_language to "en" and target_language to "zh".
- For Chinese input with multiple natural English options, mention 2-4 options in explanation, then provide examples using the best options.

Input:
{text}
""".strip()

    def _extract_output_text(self, raw: dict) -> str:
        chunks: list[str] = []
        for item in raw.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    chunks.append(content["text"])
        return "\n".join(chunks).strip()
