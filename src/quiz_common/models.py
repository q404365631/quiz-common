"""Shared data models used by quiz components."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class Option(BaseModel):
    """Single answer option for a question."""

    answer: str
    correct: bool

    @field_validator("answer", mode="before")
    @classmethod
    def convert_to_string(cls, v: str | bool | float) -> str:  # noqa: FBT001
        """Allow int, float, bool and convert them to string."""
        if isinstance(v, (int, float, bool)):
            return str(v)
        return v


class Question(BaseModel):
    """Quiz question with text, options and optional time limit."""

    text: str
    time_limit: int | None = None
    options: list[Option] = Field(default_factory=list)

    def ask(self) -> dict:
        """Return a representation of the question which is sent to the players."""
        return {
            "type": "question",
            "text": self.text,
            "options": [opt.answer for opt in self.options],
        }


class Quiz(BaseModel):
    """Collection of questions with iteration state."""

    name: str
    questions: list[Question] = Field(default_factory=list)
    current_question: int = -1

    def __next__(self) -> Question:
        """Return the next question or raise StopIteration."""
        self.current_question += 1
        try:
            question = self.questions[self.current_question]
        except IndexError as exc:
            raise StopIteration from exc

        return question

    def __len__(self) -> int:
        """Return the number of questions in the quiz."""
        return len(self.questions)

    @property
    def question(self) -> Question:
        """Return the current question."""
        return self.questions[self.current_question]


class Message(BaseModel):
    """Unified message format for all websocket communications.

    Encapsulates any data sent between Server, Admin and Players so that
    every message on the wire is a well-formed JSON dict.
    """

    msg_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    sender: str | None = None

    @field_validator("msg_type", mode="before")
    @classmethod
    def ensure_string(cls, v: Any) -> str:
        """Coerce the message type to a string."""
        return str(v)

    def to_json(self) -> str:
        """Serialize the message to a JSON string."""
        return self.model_dump_json()

    @classmethod
    def from_raw(cls, data: str | bytes | dict[str, Any]) -> "Message":
        """Parse raw websocket data into a Message.

        Accepts:
            - A JSON-encoded string or bytes object.
            - An already-parsed dict.
        """
        if isinstance(data, dict):
            return cls.model_validate(data)
        return cls.model_validate_json(data)

    def to_dict(self) -> dict[str, Any]:
        """Return the message as a plain dict suitable for JSON transmission."""
        return self.model_dump()
