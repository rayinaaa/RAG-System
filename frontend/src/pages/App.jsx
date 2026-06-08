import { ChatInterface } from "../components/ChatInterface";
import { Dashboard } from "../components/Dashboard";
import { Sidebar } from "../components/Sidebar";
import { useChat } from "../hooks/useChat";
import { useDocuments } from "../hooks/useDocuments";

export default function App() {
  const documents = useDocuments();
  const chat = useChat();
  const hasReadyDocument = documents.documents.some((doc) => doc.status === "ready");
  const hasProcessingDocument = documents.documents.some((doc) => doc.status === "queued" || doc.status === "processing");

  return (
    <div className="flex h-full flex-col bg-panel md:flex-row">
      <Sidebar
        documents={documents.documents}
        busy={documents.busy}
        error={documents.error}
        onUpload={documents.upload}
        onDelete={documents.remove}
      />
      <div className="flex min-w-0 flex-1 flex-col xl:flex-row">
        <ChatInterface
          messages={chat.messages}
          onSend={chat.sendMessage}
          isStreaming={chat.isStreaming}
          error={chat.error}
          canChat={hasReadyDocument}
          waitingForIndex={hasProcessingDocument}
        />
        <Dashboard />
      </div>
    </div>
  );
}
