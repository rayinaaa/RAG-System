export function formatPage(source) {
  if (source.page_number) return `Page ${source.page_number}`;
  if (source.section_title) return source.section_title;
  return "Document";
}

export function formatMs(value) {
  return `${Math.round(value || 0)} ms`;
}

