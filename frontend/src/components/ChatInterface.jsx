import { ChevronDown, ChevronUp, FileSearch, Loader2, Send, ShieldCheck, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { formatMs, formatPage } from "../utils/format";

const promptIdeas = [
  "Summarize the key points",
  "What decisions are mentioned?",
  "List risks and dependencies",
  "Show important dates"
];

function Message({ message }) {
  const isUser = message.role === "user";
  const [showWhy, setShowWhy] = useState(false);
  return (
    <div className="flex justify-start">
      <div
        className={`w-fit max-w-[94%] rounded px-4 py-3 text-left shadow-sm md:max-w-[760px] ${
          isUser
            ? "border border-slate-200 bg-slate-900 text-white shadow-soft"
            : "border border-line bg-white/95 text-gray-900 shadow-soft"
        }`}
      >
        {message.pending ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Loader2 size={16} className="animate-spin text-accent" />
            Thinking through the documents...
          </div>
        ) : (
          <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
        )}
        {!isUser && message.sources?.length ? (
          <div className="mt-4 border-t border-line pt-3">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-semibold capitalize text-emerald-700">
                {message.confidenceLabel || "low"} confidence
              </span>
              <span className="text-xs text-gray-500">
                {Math.round((message.confidence || 0) * 100)}% retrieval confidence
              </span>
            </div>
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
              <ShieldCheck size={14} className="text-accent" />
              Sources
            </div>
            <div className="space-y-2">
              {message.sources.map((source) => (
                <div
                  key={`${source.number}-${source.chunk_id}`}
                  className="rounded border border-line bg-gradient-to-br from-panel to-white p-3 text-xs text-gray-600"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-semibold text-gray-900">
                      [{source.number}] {source.filename}
                    </div>
                    <span className="shrink-0 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700">
                      {Math.round((source.confidence || 0) * 100)}%
                    </span>
                  </div>
                  <div className="mt-1 text-gray-500">{formatPage(source)}</div>
                  {source.preview ? <p className="mt-2 leading-5 text-gray-700">{source.preview}</p> : null}
                </div>
              ))}
            </div>
            <p className="mt-2 text-xs text-gray-400">
              Retrieval {formatMs(message.retrievalMs)} - Generation {formatMs(message.generationMs)}
            </p>
            {message.explanation ? (
              <div className="mt-3">
                <button
                  className="inline-flex items-center gap-1 rounded border border-line bg-white px-2.5 py-1 text-xs font-semibold text-gray-700 transition hover:border-accent hover:text-accent"
                  onClick={() => setShowWhy((value) => !value)}
                >
                  {showWhy ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  Why this answer?
                </button>
                {showWhy ? (
                  <div className="mt-3 space-y-3 rounded border border-line bg-panel/70 p-3 text-xs text-gray-700">
                    <div>
                      <p className="font-semibold text-gray-950">Query understanding</p>
                      <p className="mt-1 capitalize">
                        {message.explanation.query_understanding.query_type.replace("_", " ")} - {message.explanation.query_understanding.rationale}
                      </p>
                      <p className="mt-1 text-gray-500">
                        Expanded queries: {message.explanation.query_understanding.expanded_queries.join(" | ")}
                      </p>
                    </div>
                    <div className="space-y-2">
                      <p className="font-semibold text-gray-950">Retrieved evidence</p>
                      {message.explanation.retrieved_chunks.slice(0, 5).map((chunk) => (
                        <div key={chunk.chunk_id} className="rounded border border-line bg-white p-2">
                          <div className="flex flex-wrap justify-between gap-2 font-medium text-gray-900">
                            <span>[{chunk.citation_number}] {chunk.filename}</span>
                            <span>
                              v {chunk.vector_score.toFixed(2)} / k {chunk.keyword_score.toFixed(2)} / fused {chunk.final_score.toFixed(2)}
                            </span>
                          </div>
                          <p className="mt-1 line-clamp-3 text-gray-600">{chunk.text}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function ChatInterface({ messages, onSend, isStreaming, error, canChat, waitingForIndex }) {
  const [value, setValue] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = (text) => {
    if (!canChat || isStreaming || !text.trim()) return;
    onSend(text);
    setValue("");
  };

  const submit = (event) => {
    event.preventDefault();
    send(value);
  };

  return (
    <main className="app-surface flex h-full min-w-0 flex-1 flex-col bg-white">
      <div className="border-b border-line bg-white/88 px-5 py-4 backdrop-blur">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-950">Chat with your documents</h2>
            <p className="text-sm text-gray-500">Answers stay grounded in retrieved context and cited sources.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
              <ShieldCheck size={14} />
              Cited answers
            </span>
            <span className="inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
              <FileSearch size={14} />
              Hybrid retrieval
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 scrollbar-thin md:p-8">
        <div className="flex max-w-4xl flex-col gap-5">
          {messages.length ? (
            messages.map((message) => <Message key={message.id} message={message} />)
          ) : (
            <div className="mt-16 max-w-2xl text-left">
              <div className="mb-5 flex h-14 w-14 items-center justify-center rounded bg-ink text-white shadow-glow">
                <Sparkles size={24} />
              </div>
              <h3 className="text-3xl font-semibold text-gray-950">Ask a grounded question</h3>
              <p className="mt-3 max-w-xl text-sm leading-6 text-gray-500">
                {canChat
                  ? "Explore summaries, decisions, risks, obligations, timelines, and follow-ups with source-backed answers."
                  : "Upload a document and wait for indexing to complete before chatting."}
              </p>
              <div className="mt-6 grid gap-2 sm:grid-cols-2">
                {promptIdeas.map((idea) => (
                  <button
                    key={idea}
                    className="rounded border border-line bg-white/92 px-4 py-3 text-left text-sm font-medium text-gray-700 shadow-sm transition hover:-translate-y-0.5 hover:border-accent hover:text-accent hover:shadow-soft disabled:cursor-not-allowed disabled:opacity-50"
                    onClick={() => send(idea)}
                    disabled={!canChat || isStreaming}
                  >
                    {idea}
                  </button>
                ))}
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {error ? <div className="border-t border-red-100 bg-red-50 px-5 py-2 text-sm text-red-700">{error}</div> : null}

      <form onSubmit={submit} className="border-t border-line bg-white/90 p-4 backdrop-blur">
        <div className="flex max-w-4xl items-end gap-3 rounded border border-line bg-white p-2 shadow-glow">
          <textarea
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) submit(event);
            }}
            placeholder="Ask a question about uploaded documents"
            rows={1}
            className="max-h-36 min-h-10 flex-1 resize-none border-0 px-2 py-2 text-sm outline-none"
            disabled={isStreaming || !canChat}
          />
          <button
            type="submit"
            className="flex h-10 w-10 items-center justify-center rounded bg-accent text-white shadow-sm transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isStreaming || !value.trim() || !canChat}
            title="Send"
          >
            {isStreaming ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </div>
        {!canChat ? (
          <p className="mt-2 max-w-4xl text-xs text-gray-500">
            {waitingForIndex ? "Indexing is still running. Chat will unlock automatically." : "Upload and index at least one document to start chatting."}
          </p>
        ) : null}
      </form>
    </main>
  );
}
