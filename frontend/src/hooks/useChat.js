import { useMemo, useRef, useState } from "react";
import { streamChat } from "../services/api";

export function useChat() {
  const sessionId = useMemo(() => crypto.randomUUID(), []);
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState("");
  const activeAssistantId = useRef(null);

  const sendMessage = async (content) => {
    const trimmed = content.trim();
    if (!trimmed || isStreaming) return;

    const userMessage = { id: crypto.randomUUID(), role: "user", content: trimmed };
    const assistantId = crypto.randomUUID();
    activeAssistantId.current = assistantId;

    setMessages((items) => [
      ...items,
      userMessage,
      { id: assistantId, role: "assistant", content: "", sources: [], pending: true }
    ]);
    setIsStreaming(true);
    setError("");

    try {
      await streamChat({
        message: trimmed,
        sessionId,
        onToken: (token) => {
          setMessages((items) =>
            items.map((item) =>
              item.id === activeAssistantId.current
                ? { ...item, content: `${item.content}${token}`, pending: false }
                : item
            )
          );
        },
        onDone: (payload) => {
          setMessages((items) =>
            items.map((item) =>
              item.id === activeAssistantId.current
                ? {
                    ...item,
                    content: payload.answer,
                    sources: payload.sources,
                    retrievalMs: payload.retrieval_ms,
                    generationMs: payload.generation_ms,
                    confidence: payload.confidence,
                    confidenceLabel: payload.confidence_label,
                    explanation: payload.explanation,
                    pending: false
                  }
                : item
            )
          );
        },
        onError: (message) => setError(message)
      });
    } catch (err) {
      const message = err.message || "The request failed. Please try again.";
      setError(message);
      setMessages((items) =>
        items.map((item) =>
          item.id === activeAssistantId.current
            ? { ...item, content: message, pending: false }
            : item
        )
      );
    } finally {
      setIsStreaming(false);
    }
  };

  return { messages, sendMessage, isStreaming, error };
}
