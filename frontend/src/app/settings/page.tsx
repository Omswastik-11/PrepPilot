"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/Sidebar";
import { useAuthStore, useToastStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { Settings, Save, Loader2, Download, Moon, Sun, Monitor, Command, Keyboard } from "lucide-react";
import Link from "next/link";

const TONE_OPTIONS = [
  { value: "professional", label: "Professional", description: "Standard, objective, and structured evaluation." },
  { value: "casual", label: "Casual", description: "Friendly, relaxed, and conversational." },
  { value: "strict", label: "Strict", description: "Rigorous, highly critical, mimicking top-tier FAANG interviews." },
  { value: "encouraging", label: "Encouraging", description: "Supportive, highlights positives, builds confidence." }
];

export default function SettingsPage() {
  const { user } = useAuthStore();
  const router = useRouter();

  const [tone, setTone] = useState("professional");
  const [defaults, setDefaults] = useState({
    preferred_interview_types: [] as string[],
    target_companies: [] as string[],
    target_roles: [] as string[],
  });
  const [theme, setTheme] = useState("system"); // simplified for UI demo
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const showToast = useToastStore((state) => state.show);

  useEffect(() => {
    if (!user) {
      router.push("/login");
      return;
    }

    fetchApi("/api/candidate/profiles/me")
      .then((data) => {
        if (data.preferred_tone) setTone(data.preferred_tone);
        setDefaults({
          preferred_interview_types: data.preferred_interview_types || [],
          target_companies: data.target_companies || [],
          target_roles: data.target_roles || [],
        });
      })
      .catch((err) => console.error(err))
      .finally(() => setIsLoading(false));
  }, [user, router]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await fetchApi("/api/candidate/profiles/me", {
        method: "PATCH",
        body: JSON.stringify({ 
          preferred_tone: tone,
          preferred_interview_types: defaults.preferred_interview_types,
          target_companies: defaults.target_companies,
          target_roles: defaults.target_roles
        })
      });
      showToast("Preferences saved successfully!", "success");
    } catch (error: any) {
      console.error(error);
      showToast(error.message || "Failed to save preferences", "error");
    } finally {
      setIsSaving(false);
    }
  };

  if (!user || isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[var(--background)]">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--primary)]" />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--background)]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <div className="mx-auto max-w-4xl space-y-8">
          
          <div className="flex items-center gap-3 border-b border-[var(--border)] pb-6">
            <div className="rounded-lg bg-[var(--muted)] p-2">
              <Settings className="h-6 w-6 text-[var(--foreground)]" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-[var(--foreground)]">Settings</h1>
              <p className="text-sm text-[var(--muted-foreground)] mt-1">Configure your interview preferences and AI persona.</p>
            </div>
          </div>

          <div className="space-y-6 rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <div>
              <h2 className="text-lg font-semibold text-[var(--foreground)]">AI Interviewer Tone</h2>
              <p className="text-sm text-[var(--muted-foreground)] mt-1">
                Select the persona the AI should adopt during your mock interviews.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {TONE_OPTIONS.map((option) => (
                <div 
                  key={option.value}
                  onClick={() => setTone(option.value)}
                  className={`cursor-pointer rounded-lg border p-4 transition-all ${
                    tone === option.value 
                      ? "border-[var(--primary)] bg-[var(--primary)]/10 ring-1 ring-[var(--primary)]" 
                      : "border-[var(--border)] hover:border-[var(--muted-foreground)]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-[var(--foreground)]">{option.label}</span>
                    {tone === option.value && (
                      <div className="h-2 w-2 rounded-full bg-[var(--primary)]" />
                    )}
                  </div>
                  <p className="mt-2 text-xs text-[var(--muted-foreground)]">{option.description}</p>
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-4">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
              >
                {isSaving ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Save Preferences
              </button>
            </div>
          </div>

          <div className="space-y-6 rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <div>
              <h2 className="text-lg font-semibold text-[var(--foreground)] flex items-center gap-2">
                <Moon className="w-5 h-5 text-[var(--muted-foreground)]" />
                Appearance
              </h2>
              <p className="text-sm text-[var(--muted-foreground)] mt-1">Customize how PrepPilot looks on your device.</p>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {[
                { id: 'light', label: 'Light', icon: Sun },
                { id: 'dark', label: 'Dark', icon: Moon },
                { id: 'system', label: 'System', icon: Monitor },
              ].map(t => (
                <button
                  key={t.id}
                  onClick={() => {
                    setTheme(t.id);
                    document.documentElement.setAttribute('data-theme', t.id);
                    localStorage.setItem('theme', t.id);
                  }}
                  className={`flex flex-col items-center gap-2 p-3 rounded-xl border ${theme === t.id ? 'border-blue-500 bg-blue-500/10 text-blue-500' : 'border-[var(--border)] text-[var(--muted-foreground)] hover:border-[var(--foreground)]'} transition-colors`}
                >
                  <t.icon className="w-5 h-5" />
                  <span className="text-xs font-medium">{t.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-6 rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <div>
              <h2 className="text-lg font-semibold text-[var(--foreground)]">Interview Defaults</h2>
              <p className="text-sm text-[var(--muted-foreground)] mt-1">Set defaults to save time when starting new interviews.</p>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[var(--foreground)] mb-1">Target Companies (comma separated)</label>
                <input 
                  type="text" 
                  value={defaults.target_companies.join(', ')}
                  onChange={e => setDefaults({...defaults, target_companies: e.target.value.split(',').map(s => s.trim()).filter(Boolean)})}
                  className="w-full bg-[var(--background)] border border-[var(--border)] rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Google, Amazon, Meta"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--foreground)] mb-1">Target Roles (comma separated)</label>
                <input 
                  type="text" 
                  value={defaults.target_roles.join(', ')}
                  onChange={e => setDefaults({...defaults, target_roles: e.target.value.split(',').map(s => s.trim()).filter(Boolean)})}
                  className="w-full bg-[var(--background)] border border-[var(--border)] rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Software Engineer, Data Scientist"
                />
              </div>
            </div>
            <div className="flex justify-end pt-4">
              <button onClick={handleSave} disabled={isSaving} className="flex items-center gap-2 rounded-lg bg-[var(--muted)] hover:bg-[var(--border)] px-4 py-2 text-sm font-medium transition-colors">
                Save Defaults
              </button>
            </div>
          </div>

          <div className="space-y-6 rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <div>
              <h2 className="text-lg font-semibold text-[var(--foreground)]">Account Settings</h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-[var(--border)]">
                <div>
                  <div className="font-medium">Account Status</div>
                  <div className="text-sm text-[var(--muted-foreground)]">
                    {user?.is_guest ? "Guest Account (1 free mock interview)" : (user?.email || "Registered")}
                  </div>
                </div>
                {user?.is_guest && (
                  <Link
                    href="/register"
                    className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg text-xs transition-colors shadow-sm"
                  >
                    Upgrade to Full Account
                  </Link>
                )}
              </div>
              
              <div className="flex justify-between items-center py-2 border-b border-[var(--border)]">
                <div>
                  <div className="font-medium">Export My Data</div>
                  <div className="text-sm text-[var(--muted-foreground)]">Download all your interviews and profile data as JSON.</div>
                </div>
                <button onClick={async () => {
                  const interviews = await fetchApi("/api/interviews?limit=100").catch(() => []);
                  const profile = await fetchApi("/api/candidate/profiles/me").catch(() => null);
                  const blob = new Blob([JSON.stringify({ profile, interviews }, null, 2)], { type: "application/json" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a"); a.href = url; a.download = "preppilot-data.json"; a.click();
                  showToast("Data exported successfully", "success");
                }} className="px-3 py-1.5 bg-[var(--muted)] hover:bg-[var(--border)] rounded-lg text-sm font-medium flex items-center gap-2">
                  <Download className="w-4 h-4" /> Export
                </button>
              </div>
              
              <div className="flex justify-between items-center py-2">
                <div>
                  <div className="font-medium text-red-500">Delete Account</div>
                  <div className="text-sm text-[var(--muted-foreground)]">Permanently delete your account and all data.</div>
                </div>
                <button disabled className="px-3 py-1.5 bg-red-500/10 text-red-500 rounded-lg text-sm font-medium opacity-50 cursor-not-allowed">
                  Coming Soon
                </button>
              </div>
            </div>
          </div>

          <div className="space-y-6 rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <div>
              <h2 className="text-lg font-semibold text-[var(--foreground)] flex items-center gap-2">
                <Keyboard className="w-5 h-5 text-[var(--muted-foreground)]" />
                Keyboard Shortcuts
              </h2>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-[var(--muted-foreground)]">Submit Answer</span>
                <kbd className="px-2 py-1 bg-[var(--muted)] border border-[var(--border)] rounded font-mono text-xs">Enter</kbd>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-[var(--muted-foreground)]">New Line</span>
                <kbd className="px-2 py-1 bg-[var(--muted)] border border-[var(--border)] rounded font-mono text-xs">Shift + Enter</kbd>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-[var(--muted-foreground)]">Close Expanded Editor</span>
                <kbd className="px-2 py-1 bg-[var(--muted)] border border-[var(--border)] rounded font-mono text-xs">Esc</kbd>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
