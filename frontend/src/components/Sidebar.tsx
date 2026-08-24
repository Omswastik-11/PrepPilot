"use client";

import { MessageSquare, Plus, Settings, LogOut } from "lucide-react";
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
}

export function Sidebar() {
  const [interviews, setInterviews] = useState<Interview[]>([]);
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
            <Link href={`/interviews/${interview.id}`} key={interview.id}>
              <div className="flex items-center gap-3 rounded-lg p-2 transition-colors hover:bg-[var(--muted)] cursor-pointer">
                <MessageSquare className="h-4 w-4 shrink-0 text-[var(--muted-foreground)]" />
                <span className="truncate capitalize">{interview.interview_type} Interview</span>
              </div>
            </Link>
          ))
        )}
      </div>

      <div className="mt-auto border-t border-[var(--border)] pt-2 space-y-1">
        <div className="flex items-center gap-3 rounded-lg p-3 transition-colors hover:bg-[var(--muted)] cursor-pointer">
          <Settings className="h-4 w-4 text-[var(--muted-foreground)]" />
          <span>Settings</span>
        </div>
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
