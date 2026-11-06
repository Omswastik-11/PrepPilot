"use client";

import { MessageSquare, Plus, Settings, LogOut, User } from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { useRouter } from "next/navigation";

interface Interview {
  id: string;
  interview_type: string;
  status: string;
  created_at: string;
  title?: string;
  total_score?: number | null;
}

export function Sidebar() {
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const { user, logout } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (user) {
      fetchApi("/api/interviews?limit=10")
        .then((data) => setInterviews(data.items || []))
        .catch(console.error);
    }
  }, [user]);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const handleSaveTitle = async (id: string) => {
    if (!editTitle.trim()) {
      setEditingId(null);
      return;
    }
    try {
      const updated = await fetchApi(`/api/interviews/${id}/title`, {
        method: "PATCH",
        body: JSON.stringify({ title: editTitle.trim() }),
      });
      setInterviews((prev) => 
        prev.map((inv) => (inv.id === id ? { ...inv, title: updated.title } : inv))
      );
    } catch (e) {
      console.error(e);
    }
    setEditingId(null);
  };

  return (
    <div className="flex h-full w-[260px] flex-col bg-[var(--sidebar-background)] border-r border-[var(--border)] p-3 text-sm text-[var(--sidebar-foreground)]">
      <Link href="/">
        <div className="flex items-center gap-3 rounded-lg border border-[var(--border)] p-3 transition-colors hover:bg-[var(--muted)] cursor-pointer">
          <Plus className="h-4 w-4" />
          <span className="font-medium">New Interview</span>
        </div>
      </Link>

      <div className="flex-1 overflow-y-auto mt-4 space-y-2">
        <div className="text-xs font-semibold text-[var(--muted-foreground)] px-2 pb-2">Previous Interviews</div>
        {interviews.length === 0 ? (
          <div className="px-2 text-xs text-[var(--muted-foreground)]">No previous interviews</div>
        ) : (
          interviews.map((interview) => (
            <div key={interview.id} className="group relative flex items-center gap-3 rounded-lg p-2 transition-colors hover:bg-[var(--muted)]">
              <Link href={`/interviews/${interview.id}`} className="flex flex-1 items-center gap-3 overflow-hidden pr-2">
                <div className="relative shrink-0">
                  <MessageSquare className="h-4 w-4 text-[var(--muted-foreground)]" />
                  {interview.status === 'in_progress' && <div className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-blue-500 border border-[var(--sidebar-background)]" title="In Progress" />}
                  {interview.status === 'completed' && <div className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-green-500 border border-[var(--sidebar-background)]" title="Completed" />}
                </div>
                {editingId === interview.id ? (
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleSaveTitle(interview.id);
                      if (e.key === "Escape") setEditingId(null);
                    }}
                    onBlur={() => handleSaveTitle(interview.id)}
                    autoFocus
                    className="flex-1 bg-transparent border-b border-white/20 outline-none text-sm text-[var(--foreground)]"
                    onClick={(e) => e.preventDefault()}
                  />
                ) : (
                  <>
                    <span className="truncate flex-1">{interview.title || `${interview.interview_type} Interview`}</span>
                    {interview.status === 'completed' && interview.total_score !== null && interview.total_score !== undefined && (
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0 ${interview.total_score >= 8 ? 'bg-green-500/10 text-green-500' : interview.total_score >= 5 ? 'bg-yellow-500/10 text-yellow-500' : 'bg-red-500/10 text-red-500'}`}>
                        {interview.total_score}
                      </span>
                    )}
                  </>
                )}
              </Link>
              {editingId !== interview.id && (
                <button 
                  onClick={(e) => {
                    e.preventDefault();
                    setEditTitle(interview.title || `${interview.interview_type} Interview`);
                    setEditingId(interview.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-opacity"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
                </button>
              )}
            </div>
          ))
        )}
      </div>

      <div className="mt-auto border-t border-[var(--border)] pt-2 space-y-1">
        <Link href="/profile">
          <div className="flex items-center gap-3 rounded-lg p-3 transition-colors hover:bg-[var(--muted)] cursor-pointer">
            <User className="h-4 w-4 text-[var(--muted-foreground)]" />
            <span>Profile</span>
          </div>
        </Link>
        <Link href="/settings">
          <div className="flex items-center gap-3 rounded-lg p-3 transition-colors hover:bg-[var(--muted)] cursor-pointer">
            <Settings className="h-4 w-4 text-[var(--muted-foreground)]" />
            <span>Settings</span>
          </div>
        </Link>
        <div 
          onClick={handleLogout}
          className="flex items-center gap-3 rounded-lg p-3 transition-colors hover:bg-red-500/10 hover:text-red-500 cursor-pointer text-[var(--muted-foreground)]"
        >
          <LogOut className="h-4 w-4" />
          <span>Log out {user?.email}</span>
        </div>
      </div>
    </div>
  );
}
