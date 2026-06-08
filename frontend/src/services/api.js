const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";

export async function uploadDocuments(files) {
  const body = new FormData();
  Array.from(files).forEach((file) => body.append("files", file));
  const response = await fetch(`${API_BASE}/upload`, { method: "POST", body });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function listDocuments() {
  const response = await fetch(`${API_BASE}/documents`);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function deleteDocument(id) {
  const response = await fetch(`${API_BASE}/documents/${id}`, { method: "DELETE" });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function getDocumentSummary(id) {
  const response = await fetch(`${API_BASE}/documents/${id}/summary`);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function getHealth() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export function subscribeToDocuments({ onDocuments, onError }) {
  const source = new EventSource(`${API_BASE}/documents/events`);
  const update = (event) => {
    const payload = JSON.parse(event.data);
    onDocuments(payload.documents || []);
  };

  source.addEventListener("snapshot", update);
  source.addEventListener("document_added", update);
  source.addEventListener("document_updated", update);
  source.addEventListener("document_deleted", update);
  source.onerror = () => onError?.("Live document updates disconnected. Reconnecting...");
  return () => source.close();
}

export async function streamChat({ message, sessionId, onToken, onDone, onError }) {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId })
  });

  if (!response.ok || !response.body) {
    throw new Error(await response.text());
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";
    for (const event of events) {
      const line = event.split("\n").find((item) => item.startsWith("data: "));
      if (!line) continue;
      const payload = JSON.parse(line.slice(6));
      if (payload.type === "token") onToken(payload.token);
      if (payload.type === "retrieval_done") continue;
      if (payload.type === "done") onDone(payload.payload);
      if (payload.type === "error") {
        onError(payload.error);
        throw new Error(payload.error);
      }
    }
  }
}
