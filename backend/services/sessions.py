from collections import defaultdict, deque

from backend.models.schemas import ChatMessage


class SessionMemory:
    def __init__(self, max_messages: int = 12):
        self.max_messages = max_messages
        self._messages: dict[str, deque[ChatMessage]] = defaultdict(lambda: deque(maxlen=max_messages))

    def append(self, session_id: str, role: str, content: str) -> None:
        self._messages[session_id].append(ChatMessage(role=role, content=content))

    def get_history(self, session_id: str) -> list[ChatMessage]:
        return list(self._messages[session_id])


sessions = SessionMemory()

