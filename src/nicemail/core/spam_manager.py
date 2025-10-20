"""Integrate ChatGPT spam filtering."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Sequence

import httpx

from .config import SpamConfig
from .mail_client import MailMessage


@dataclass(slots=True)
class SpamAssessment:
    message_id: str
    is_spam: bool
    confidence: float


class SpamManager:
    """Coordinate spam filtering leveraging ChatGPT (or other providers)."""

    def __init__(self, config: SpamConfig) -> None:
        self._config = config

    def filter_messages(self, messages: Sequence[MailMessage]) -> Sequence[MailMessage]:
        if not self._config.enabled or not self._config.api_key:
            return messages
        try:
            assessments = self._assess_messages(messages)
        except Exception:
            return messages
        allowed = []
        blocklist = {assessment.message_id for assessment in assessments if assessment.is_spam}
        for message in messages:
            if message.id in blocklist:
                continue
            allowed.append(message)
        return allowed

    # ------------------------ private helpers ------------------------------
    def _assess_messages(self, messages: Sequence[MailMessage]) -> Sequence[SpamAssessment]:
        if not messages:
            return []
        payload = self._build_payload(messages)
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            content=json.dumps(payload),
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        assessments: list[SpamAssessment] = []
        for entry in data.get("choices", []):
            message_id = entry.get("metadata", {}).get("message_id")
            if not message_id:
                continue
            result = entry.get("content", [{}])[0].get("text", "")
            try:
                parsed = json.loads(result)
            except json.JSONDecodeError:
                continue
            assessments.append(
                SpamAssessment(
                    message_id=message_id,
                    is_spam=parsed.get("is_spam", False),
                    confidence=float(parsed.get("confidence", 0.5)),
                )
            )
        return assessments

    def _build_payload(self, messages: Sequence[MailMessage]) -> dict:
        prompts = []
        for message in messages:
            prompts.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "You are a security assistant. "
                                "Classify the following email as spam or legitimate. "
                                "Return JSON with keys 'is_spam' and 'confidence'.\n\n"
                                f"Subject: {message.subject}\n"
                                f"From: {message.sender}\n"
                                f"Preview: {message.preview}"
                            ),
                        }
                    ],
                    "metadata": {"message_id": message.id},
                }
            )
        return {
            "model": self._config.model,
            "input": prompts,
            "temperature": 0,
        }


__all__ = ["SpamManager", "SpamAssessment"]
