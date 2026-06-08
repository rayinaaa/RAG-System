import { useCallback, useEffect, useState } from "react";
import { deleteDocument, listDocuments, subscribeToDocuments, uploadDocuments } from "../services/api";

export function useDocuments() {
  const [documents, setDocuments] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const data = await listDocuments();
      setDocuments(data);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    refresh();
    let fallback = null;
    const unsubscribe = subscribeToDocuments({
      onDocuments: (data) => {
        setDocuments(data);
        setError("");
        if (fallback) {
          window.clearInterval(fallback);
          fallback = null;
        }
      },
      onError: (message) => {
        setError(message);
        if (!fallback) fallback = window.setInterval(refresh, 5000);
      }
    });
    return () => {
      unsubscribe();
      if (fallback) window.clearInterval(fallback);
    };
  }, [refresh]);

  const upload = async (files) => {
    if (!files?.length) return;
    setBusy(true);
    try {
      await uploadDocuments(files);
      await refresh();
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id) => {
    setBusy(true);
    try {
      await deleteDocument(id);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return { documents, busy, error, upload, remove, refresh };
}
