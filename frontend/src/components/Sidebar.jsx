import { BotMessageSquare, CheckCircle2, Clock3, FileText, FileUp, FolderKanban, Layers3, Sparkles, Trash2, UploadCloud, XCircle } from "lucide-react";
import { useState } from "react";
import { getDocumentSummary } from "../services/api";

function statusStyle(status) {
  if (status === "ready") return "bg-emerald-50 text-emerald-700 border-emerald-200";
  if (status === "failed") return "bg-red-50 text-red-700 border-red-200";
  if (status === "processing") return "bg-blue-50 text-blue-700 border-blue-200";
  return "bg-amber-50 text-amber-700 border-amber-200";
}

function StatusIcon({ status }) {
  if (status === "ready") return <CheckCircle2 size={13} />;
  if (status === "failed") return <XCircle size={13} />;
  return <Clock3 size={13} />;
}

export function Sidebar({ documents, busy, error, onUpload, onDelete }) {
  const [insights, setInsights] = useState({});
  const [loadingInsight, setLoadingInsight] = useState("");

  const loadInsights = async (doc) => {
    if (doc.status !== "ready") return;
    if (insights[doc.id]) {
      setInsights((items) => ({ ...items, [doc.id]: null }));
      return;
    }
    setLoadingInsight(doc.id);
    try {
      const payload = await getDocumentSummary(doc.id);
      setInsights((items) => ({ ...items, [doc.id]: payload }));
    } catch (err) {
      setInsights((items) => ({ ...items, [doc.id]: { error: err.message } }));
    } finally {
      setLoadingInsight("");
    }
  };

  return (
    <aside className="flex h-full w-full flex-col border-r border-line bg-white/86 backdrop-blur md:w-80">
      <div className="border-b border-line p-4">
        <div className="mb-4 flex items-center gap-3">
          <div className="relative flex h-11 w-11 items-center justify-center rounded bg-gradient-to-br from-ink via-slate-800 to-ocean text-white shadow-soft">
            <BotMessageSquare size={21} />
            <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-accent text-[9px] font-bold text-white">
              AI
            </span>
          </div>
          <div>
            <h1 className="text-base font-semibold text-gray-950">Docu.Chat AI</h1>
            <p className="text-xs text-gray-500">Evidence-first document AI</p>
          </div>
        </div>
        {error ? <p className="mt-3 rounded border border-red-100 bg-red-50 p-2 text-xs text-red-700">{error}</p> : null}
      </div>

      <div className="border-b border-line p-3">
        <div className="mb-3 flex items-center gap-2 px-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
          <span className="flex h-7 w-7 items-center justify-center rounded bg-slate-100 text-slate-600">
            <Layers3 size={15} />
          </span>
          Workspace
        </div>
        <label className="group flex cursor-pointer items-center gap-3 rounded border border-dashed border-emerald-300 bg-gradient-to-r from-emerald-50 via-white to-blue-50 px-3 py-3 text-sm font-semibold text-emerald-800 shadow-sm transition hover:border-accent hover:bg-emerald-50 hover:shadow-soft">
          <span className="relative flex h-11 w-11 shrink-0 items-center justify-center rounded bg-white text-emerald-700 shadow-sm ring-1 ring-emerald-100 transition group-hover:-translate-y-0.5 group-hover:ring-emerald-300">
            {busy ? <UploadCloud size={20} className="animate-pulse" /> : <FolderKanban size={20} />}
            <span className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-accent text-white shadow-sm">
              <FileUp size={12} />
            </span>
          </span>
          <span className="flex flex-col leading-tight">
            <span>{busy ? "Uploading..." : "Add documents"}</span>
            <span className="mt-0.5 text-[11px] font-medium text-gray-500">PDF, DOCX, TXT, CSV</span>
          </span>
          <input
            className="hidden"
            type="file"
            multiple
            accept=".pdf,.docx,.txt,.csv"
            onChange={(event) => onUpload(event.target.files)}
            disabled={busy}
          />
        </label>
      </div>

      <div className="flex-1 overflow-y-auto p-3 scrollbar-thin">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500">Documents</h2>
          <span className="rounded-full bg-panel px-2 py-0.5 text-xs text-gray-500">{documents.length}</span>
        </div>
        <div className="space-y-3">
          {documents.map((doc) => (
            <div key={doc.id} className="rounded border border-line bg-white p-3 shadow-sm transition hover:-translate-y-0.5 hover:shadow-soft">
              <div className="flex gap-2">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-panel text-gray-600">
                  <FileText size={17} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-gray-950" title={doc.filename}>
                    {doc.filename}
                  </p>
                  <div className="mt-1 flex flex-wrap items-center gap-1.5">
                    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${statusStyle(doc.status)}`}>
                      <StatusIcon status={doc.status} />
                      {doc.status}
                    </span>
                    {doc.chunk_count ? <span className="text-[11px] text-gray-500">{doc.chunk_count} chunks</span> : null}
                  </div>
                </div>
                <button
                  className="h-7 w-7 rounded text-gray-400 transition hover:bg-red-50 hover:text-red-600"
                  onClick={() => onDelete(doc.id)}
                  title="Delete document"
                >
                  <Trash2 size={15} className="mx-auto" />
                </button>
              </div>
              <div className="mt-3 h-1.5 overflow-hidden rounded bg-gray-100">
                <div
                  className={`h-full rounded ${doc.status === "failed" ? "bg-red-500" : "bg-gradient-to-r from-accent to-ocean"}`}
                  style={{ width: `${doc.progress || 0}%` }}
                />
              </div>
              {doc.error ? <p className="mt-2 rounded bg-red-50 p-2 text-xs text-red-600">{doc.error}</p> : null}
              {doc.status === "ready" ? (
                <button
                  className="mt-3 inline-flex items-center gap-1 rounded border border-line bg-panel px-2 py-1 text-xs font-semibold text-gray-700 transition hover:border-accent hover:text-accent"
                  onClick={() => loadInsights(doc)}
                >
                  <Sparkles size={13} />
                  {loadingInsight === doc.id ? "Loading insights..." : insights[doc.id] ? "Hide insights" : "Document insights"}
                </button>
              ) : null}
              {insights[doc.id] ? (
                <div className="mt-3 space-y-2 rounded border border-line bg-panel/70 p-3 text-xs text-gray-700">
                  {insights[doc.id].error ? (
                    <p className="text-red-600">{insights[doc.id].error}</p>
                  ) : (
                    <>
                      <p className="font-semibold text-gray-950">Executive summary</p>
                      <p className="leading-5">{insights[doc.id].summary}</p>
                      <p className="font-semibold text-gray-950">Key topics</p>
                      <div className="flex flex-wrap gap-1">
                        {(insights[doc.id].key_topics || []).map((topic) => (
                          <span key={topic} className="rounded-full bg-white px-2 py-0.5 text-[11px] text-gray-700">
                            {topic}
                          </span>
                        ))}
                      </div>
                      {insights[doc.id].important_dates?.length ? (
                        <>
                          <p className="font-semibold text-gray-950">Important dates</p>
                          <p>{insights[doc.id].important_dates.join(", ")}</p>
                        </>
                      ) : null}
                      {insights[doc.id].action_items?.length ? (
                        <>
                          <p className="font-semibold text-gray-950">Action items</p>
                          <ul className="list-inside list-disc space-y-1">
                            {insights[doc.id].action_items.slice(0, 3).map((item) => (
                              <li key={item}>{item}</li>
                            ))}
                          </ul>
                        </>
                      ) : null}
                    </>
                  )}
                </div>
              ) : null}
            </div>
          ))}
          {!documents.length ? (
            <div className="rounded border border-line bg-white p-4 text-sm text-gray-500 shadow-sm">
              <div className="mb-2 flex h-9 w-9 items-center justify-center rounded bg-panel text-gray-600">
                <FileText size={18} />
              </div>
              Upload PDF, DOCX, TXT, or CSV files to begin.
            </div>
          ) : null}
        </div>
      </div>
    </aside>
  );
}
