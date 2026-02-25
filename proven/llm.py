"""LLM client wrapper supporting OpenAI-compatible and Anthropic APIs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict
    raw: object


def _is_anthropic_model(model: str) -> bool:
    return model.startswith("claude-")


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.model = model
        self._use_anthropic = _is_anthropic_model(model)

        if self._use_anthropic:
            from anthropic import Anthropic
            self._anthropic = Anthropic(api_key=api_key)
        else:
            from openai import OpenAI
            self._openai = OpenAI(base_url=base_url, api_key=api_key)

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """Single chat completion."""
        return self.complete_with_history(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def complete_with_history(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """Chat completion with full conversation history (for retry loops)."""
        if self._use_anthropic:
            return self._anthropic_complete(system_prompt, messages, temperature, max_tokens)
        return self._openai_complete(system_prompt, messages, temperature, max_tokens)

    def _openai_complete(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        all_messages = [{"role": "system", "content": system_prompt}] + messages
        response = self._openai.chat.completions.create(
            model=self.model,
            messages=all_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage=usage,
            raw=response,
        )

    def _anthropic_complete(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        response = self._anthropic.messages.create(
            model=self.model,
            system=system_prompt,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        usage = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text
        return LLMResponse(
            content=content,
            model=response.model,
            usage=usage,
            raw=response,
        )
