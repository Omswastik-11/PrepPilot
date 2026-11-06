"use client";

import React, { useState } from "react";

interface MarkdownRendererProps {
  content?: string | null;
  className?: string;
  inline?: boolean;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button
      onClick={handleCopy}
      type="button"
      className="inline-flex items-center gap-1.5 px-2 py-1 text-xs rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors focus:outline-none"
      title="Copy code"
    >
      {copied ? (
        <>
          <svg className="w-3.5 h-3.5 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <span className="text-emerald-400 text-[11px] font-medium">Copied!</span>
        </>
      ) : (
        <>
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
            <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
          </svg>
          <span className="text-[11px]">Copy</span>
        </>
      )}
    </button>
  );
}

// Lightweight syntax token colorizer for code blocks
function highlightCode(code: string, language?: string): React.ReactNode {
  const lang = (language || "").toLowerCase().trim();

  // If no known language, render clean plain text
  if (!["python", "py", "javascript", "js", "typescript", "ts", "json", "sql", "bash", "sh"].includes(lang)) {
    return code;
  }

  const lines = code.split("\n");
  return lines.map((line, lineIdx) => {
    // Check for comment
    const isPythonComment = (lang === "python" || lang === "py" || lang === "bash" || lang === "sh") && line.trim().startsWith("#");
    const isJsComment = (lang === "js" || lang === "ts" || lang === "javascript" || lang === "typescript") && line.trim().startsWith("//");
    const isSqlComment = lang === "sql" && line.trim().startsWith("--");

    if (isPythonComment || isJsComment || isSqlComment) {
      return (
        <span key={lineIdx} className="block text-emerald-600 dark:text-emerald-400 italic">
          {line}
        </span>
      );
    }

    // Tokenize line with regex
    // 1. Strings: "..." or '...'
    // 2. Numbers: \b\d+\b
    // 3. Keywords
    const keywordsPython = new Set([
      "def", "class", "return", "import", "from", "for", "while", "in", "if", "elif", "else",
      "try", "except", "finally", "with", "as", "async", "await", "lambda", "yield", "raise",
      "pass", "break", "continue", "and", "or", "not", "is", "None", "True", "False", "self"
    ]);

    const keywordsJs = new Set([
      "function", "const", "let", "var", "return", "import", "from", "export", "default",
      "class", "extends", "if", "else", "switch", "case", "for", "while", "try", "catch",
      "finally", "async", "await", "new", "this", "typeof", "instanceof", "true", "false", "null", "undefined"
    ]);

    const keywords = (lang === "python" || lang === "py") ? keywordsPython : keywordsJs;

    const parts = line.split(/("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b[a-zA-Z_]\w*\b|\b\d+\b|[^\w\s"']+)/g);

    return (
      <span key={lineIdx} className="block">
        {parts.filter(Boolean).map((token, tokenIdx) => {
          if (token.startsWith('"') || token.startsWith("'")) {
            return (
              <span key={tokenIdx} className="text-amber-600 dark:text-amber-300">
                {token}
              </span>
            );
          }
          if (keywords.has(token)) {
            return (
              <span key={tokenIdx} className="text-purple-600 dark:text-purple-400 font-semibold">
                {token}
              </span>
            );
          }
          if (/^\d+$/.test(token)) {
            return (
              <span key={tokenIdx} className="text-sky-600 dark:text-sky-400">
                {token}
              </span>
            );
          }
          return <span key={tokenIdx}>{token}</span>;
        })}
      </span>
    );
  });
}

// Parses inline Markdown: `code`, **bold**, *italic*, ~~strikethrough~~, [link](url)
function parseInlineMarkdown(text: string): React.ReactNode[] {
  // Regex pattern matching:
  // 1. `inline code`
  // 2. **bold** or __bold__
  // 3. *italic* or _italic_
  // 4. ~~strike~~
  // 5. [label](url)
  const pattern = /(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_|~~[^~]+~~|\[[^\]]+\]\([^)]+\))/g;
  const parts = text.split(pattern);

  return parts.map((part, idx) => {
    if (!part) return null;

    // Inline Code
    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      const code = part.slice(1, -1);
      return (
        <code
          key={idx}
          className="mx-0.5 px-1.5 py-0.5 text-[0.88em] font-mono font-medium rounded-md bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20"
        >
          {code}
        </code>
      );
    }

    // Bold
    if ((part.startsWith("**") && part.endsWith("**") && part.length >= 4) ||
        (part.startsWith("__") && part.endsWith("__") && part.length >= 4)) {
      return (
        <strong key={idx} className="font-semibold text-[var(--foreground)]">
          {parseInlineMarkdown(part.slice(2, -2))}
        </strong>
      );
    }

    // Italic
    if ((part.startsWith("*") && part.endsWith("*") && part.length >= 2) ||
        (part.startsWith("_") && part.endsWith("_") && part.length >= 2)) {
      return (
        <em key={idx} className="italic text-[var(--foreground)]">
          {parseInlineMarkdown(part.slice(1, -1))}
        </em>
      );
    }

    // Strikethrough
    if (part.startsWith("~~") && part.endsWith("~~") && part.length >= 4) {
      return (
        <del key={idx} className="line-through text-[var(--muted-foreground)]">
          {parseInlineMarkdown(part.slice(2, -2))}
        </del>
      );
    }

    // Link
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      const [, label, url] = linkMatch;
      return (
        <a
          key={idx}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-500 hover:text-blue-600 underline underline-offset-2"
        >
          {label}
        </a>
      );
    }

    return <React.Fragment key={idx}>{part}</React.Fragment>;
  });
}

export function MarkdownRenderer({ content, className = "", inline = false }: MarkdownRendererProps) {
  if (!content) return null;

  if (inline) {
    return <span className={className}>{parseInlineMarkdown(content)}</span>;
  }

  // Block-level parsing
  const rawText = content.replace(/\r\n/g, "\n");
  const blocks: React.ReactNode[] = [];

  // Split by code blocks first
  const codeBlockRegex = /```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  let blockKey = 0;

  const processTextBlocks = (textChunk: string) => {
    if (!textChunk) return;
    const lines = textChunk.split("\n");
    let currentList: { type: "ul" | "ol"; items: string[] } | null = null;
    let currentTable: { headers: string[]; rows: string[][] } | null = null;

    const flushList = () => {
      if (!currentList) return;
      const { type, items } = currentList;
      if (type === "ul") {
        blocks.push(
          <ul key={`list-${blockKey++}`} className="my-2 space-y-1 list-disc pl-5 text-[var(--foreground)]">
            {items.map((it, idx) => (
              <li key={idx} className="leading-relaxed">
                {parseInlineMarkdown(it)}
              </li>
            ))}
          </ul>
        );
      } else {
        blocks.push(
          <ol key={`list-${blockKey++}`} className="my-2 space-y-1 list-decimal pl-5 text-[var(--foreground)]">
            {items.map((it, idx) => (
              <li key={idx} className="leading-relaxed">
                {parseInlineMarkdown(it)}
              </li>
            ))}
          </ol>
        );
      }
      currentList = null;
    };

    const flushTable = () => {
      if (!currentTable) return;
      const { headers, rows } = currentTable;
      blocks.push(
        <div key={`table-${blockKey++}`} className="my-3 overflow-x-auto rounded-xl border border-[var(--border)]">
          <table className="w-full text-sm text-left border-collapse">
            <thead className="bg-[var(--muted)] text-[var(--foreground)] font-semibold border-b border-[var(--border)]">
              <tr>
                {headers.map((h, i) => (
                  <th key={i} className="px-3.5 py-2.5">
                    {parseInlineMarkdown(h)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)] bg-[var(--sidebar-background)]">
              {rows.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-[var(--muted)]/40 transition-colors">
                  {row.map((cell, cIdx) => (
                    <td key={cIdx} className="px-3.5 py-2 text-[var(--foreground)]">
                      {parseInlineMarkdown(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      currentTable = null;
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();

      // Horizontal Rule
      if (trimmed === "---" || trimmed === "***" || trimmed === "___") {
        flushList();
        flushTable();
        blocks.push(<hr key={`hr-${blockKey++}`} className="my-4 border-[var(--border)]" />);
        continue;
      }

      // Markdown Table Line (e.g. | col1 | col2 |)
      if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
        flushList();
        const cells = trimmed.split("|").slice(1, -1).map((c) => c.trim());
        // Check if separator line (e.g. |---|---|)
        const isSeparator = cells.every((c) => /^:?-+:?$/.test(c));
        if (isSeparator) {
          continue; // skip separator row
        }
        if (!currentTable) {
          currentTable = { headers: cells, rows: [] };
        } else {
          currentTable.rows.push(cells);
        }
        continue;
      } else if (currentTable) {
        flushTable();
      }

      // Blockquote (> ...)
      if (trimmed.startsWith(">")) {
        flushList();
        const quoteContent = trimmed.replace(/^>\s?/, "");
        blocks.push(
          <blockquote
            key={`quote-${blockKey++}`}
            className="my-2 pl-4 py-1.5 border-l-4 border-blue-500 bg-blue-500/5 text-[var(--foreground)] italic rounded-r-lg"
          >
            {parseInlineMarkdown(quoteContent)}
          </blockquote>
        );
        continue;
      }

      // Headers (# ...)
      const h1Match = line.match(/^#\s+(.+)$/);
      if (h1Match) {
        flushList();
        blocks.push(
          <h1 key={`h1-${blockKey++}`} className="text-xl font-bold text-[var(--foreground)] mt-4 mb-2">
            {parseInlineMarkdown(h1Match[1])}
          </h1>
        );
        continue;
      }

      const h2Match = line.match(/^##\s+(.+)$/);
      if (h2Match) {
        flushList();
        blocks.push(
          <h2 key={`h2-${blockKey++}`} className="text-lg font-bold text-[var(--foreground)] mt-3.5 mb-1.5">
            {parseInlineMarkdown(h2Match[1])}
          </h2>
        );
        continue;
      }

      const h3Match = line.match(/^###\s+(.+)$/);
      if (h3Match) {
        flushList();
        blocks.push(
          <h3 key={`h3-${blockKey++}`} className="text-base font-semibold text-[var(--foreground)] mt-3 mb-1">
            {parseInlineMarkdown(h3Match[1])}
          </h3>
        );
        continue;
      }

      const h4Match = line.match(/^####\s+(.+)$/);
      if (h4Match) {
        flushList();
        blocks.push(
          <h4 key={`h4-${blockKey++}`} className="text-sm font-semibold text-[var(--foreground)] mt-2.5 mb-1">
            {parseInlineMarkdown(h4Match[1])}
          </h4>
        );
        continue;
      }

      // Unordered List (- item or * item)
      const ulMatch = line.match(/^[-*]\s+(.+)$/);
      if (ulMatch) {
        if (!currentList || currentList.type !== "ul") {
          flushList();
          currentList = { type: "ul", items: [] };
        }
        currentList.items.push(ulMatch[1]);
        continue;
      }

      // Ordered List (1. item)
      const olMatch = line.match(/^\d+\.\s+(.+)$/);
      if (olMatch) {
        if (!currentList || currentList.type !== "ol") {
          flushList();
          currentList = { type: "ol", items: [] };
        }
        currentList.items.push(olMatch[1]);
        continue;
      }

      // Plain line / Paragraph
      flushList();

      if (trimmed === "") {
        // Blank line -> spacer
        blocks.push(<div key={`blank-${blockKey++}`} className="h-2" />);
      } else {
        blocks.push(
          <p key={`p-${blockKey++}`} className="leading-relaxed text-[var(--foreground)]">
            {parseInlineMarkdown(line)}
          </p>
        );
      }
    }

    flushList();
    flushTable();
  };

  while ((match = codeBlockRegex.exec(rawText)) !== null) {
    const textBefore = rawText.slice(lastIndex, match.index);
    processTextBlocks(textBefore);

    const lang = match[1] || "";
    const codeSnippet = match[2].trimEnd();

    blocks.push(
      <div
        key={`codeblock-${blockKey++}`}
        className="my-3 rounded-xl overflow-hidden border border-[var(--border)] bg-[#0f141c] text-[#f8fafc] shadow-md"
      >
        <div className="flex items-center justify-between px-3.5 py-1.5 bg-[#18202f] border-b border-[#243046]">
          <div className="flex items-center gap-2">
            <svg className="w-3.5 h-3.5 text-blue-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="4 17 10 11 4 5" />
              <line x1="12" x2="20" y1="19" y2="19" />
            </svg>
            <span className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold">
              {lang || "code"}
            </span>
          </div>
          <CopyButton text={codeSnippet} />
        </div>
        <pre className="p-4 overflow-x-auto font-mono text-xs md:text-sm leading-relaxed">
          <code>{highlightCode(codeSnippet, lang)}</code>
        </pre>
      </div>
    );

    lastIndex = match.index + match[0].length;
  }

  const remainingText = rawText.slice(lastIndex);
  processTextBlocks(remainingText);

  return <div className={`space-y-1 ${className}`}>{blocks}</div>;
}
