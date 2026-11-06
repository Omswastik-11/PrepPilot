"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/Sidebar";
import { useAuthStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { Play } from "lucide-react";

export default function Home() {
  const { user } = useAuthStore();
  const router = useRouter();

  const [type, setType] = useState("technical");
  const [difficulty, setDifficulty] = useState("medium");
  const [durationMinutes, setDurationMinutes] = useState(40);
  const [company, setCompany] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [profileRoles, setProfileRoles] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) {
      router.push("/login");
      return;
    }
    
    async function fetchProfile() {
      try {
        const profile = await fetchApi("/api/candidate/profiles/me");
        if (profile && profile.target_roles && profile.target_roles.length > 0) {
          setProfileRoles(profile.target_roles);
          setTargetRole(profile.target_roles[0]);
        }
      } catch (err) {
        // Profile might not exist yet, that's fine
      }
    }
    fetchProfile();
  }, [user, router]);

  if (!user) {
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      const data = await fetchApi("/api/interviews", {
        method: "POST",
        body: JSON.stringify({
          interview_type: type,
          difficulty,
          duration_minutes: durationMinutes,
          company: company.trim() || null,
          role: targetRole.trim() || null,
        }),
      });
      // Redirect to the newly created interview chat interface
      router.push(`/interviews/${data.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to start interview");
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--background)]">
      <Sidebar />

      <main className="flex-1 flex flex-col relative overflow-y-auto p-4 md:p-8">
        <div className="max-w-2xl mx-auto w-full mt-12">
          <div className="mb-10 text-center">
            <h1 className="text-3xl font-bold mb-2">Configure Your Interview</h1>
            <p className="text-[var(--muted-foreground)]">Customize your mock interview experience with AI.</p>
          </div>

          {error && (
            <div className="mb-6 p-4 text-sm text-red-500 bg-red-500/10 rounded-xl border border-red-500/20 text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-8 bg-[var(--sidebar-background)] p-6 md:p-8 rounded-3xl border border-[var(--border)] shadow-sm">
            
            <div className="space-y-3">
              <label className="text-sm font-semibold">Interview Type</label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {["behavioral", "technical", "system_design"].map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setType(t)}
                    className={`py-3 px-4 rounded-xl border text-sm font-medium transition-all ${
                      type === t 
                      ? "border-blue-600 bg-blue-600/10 text-blue-600" 
                      : "border-[var(--border)] hover:bg-[var(--muted)] text-[var(--foreground)]"
                    }`}
                  >
                    {t.replace("_", " ").replace(/\b\w/g, l => l.toUpperCase())}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-sm font-semibold">Difficulty</label>
              <div className="grid grid-cols-3 gap-3">
                {["easy", "medium", "hard"].map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setDifficulty(d)}
                    className={`py-3 px-4 rounded-xl border text-sm font-medium transition-all ${
                      difficulty === d 
                      ? "border-blue-600 bg-blue-600/10 text-blue-600" 
                      : "border-[var(--border)] hover:bg-[var(--muted)] text-[var(--foreground)]"
                    }`}
                  >
                    {d.charAt(0).toUpperCase() + d.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-sm font-semibold">Interview Duration</label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {[
                  { value: 20, label: "20 min", desc: "~4-6 questions" },
                  { value: 40, label: "40 min", desc: "~8-12 questions" },
                  { value: 60, label: "60 min", desc: "~15-20 questions" },
                ].map((d) => (
                  <button
                    key={d.value}
                    type="button"
                    onClick={() => setDurationMinutes(d.value)}
                    className={`py-3 px-4 rounded-xl border flex flex-col items-center justify-center transition-all ${
                      durationMinutes === d.value 
                      ? "border-blue-600 bg-blue-600/10 text-blue-600" 
                      : "border-[var(--border)] hover:bg-[var(--muted)] text-[var(--foreground)]"
                    }`}
                  >
                    <span className="text-sm font-medium">{d.label}</span>
                    <span className={`text-xs mt-1 ${durationMinutes === d.value ? "text-blue-500/80" : "text-[var(--muted-foreground)]"}`}>
                      {d.desc}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-sm font-semibold">Target Company (Optional)</label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g. Google, Amazon, Stripe"
                className="w-full px-4 py-3 bg-[var(--background)] border border-[var(--border)] rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow"
              />
              <p className="text-xs text-[var(--muted-foreground)]">
                The AI will tailor the questions towards this company's interview style if provided.
              </p>
            </div>

            <div className="space-y-3">
              <label className="text-sm font-semibold">Target Role (Optional)</label>
              {profileRoles.length > 0 ? (
                <div className="flex flex-col gap-2">
                  <select 
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                    className="w-full px-4 py-3 bg-[var(--background)] border border-[var(--border)] rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow appearance-none"
                  >
                    <option value="">Select a role or type custom below...</option>
                    {profileRoles.map(role => (
                      <option key={role} value={role}>{role}</option>
                    ))}
                  </select>
                  <input
                    type="text"
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                    placeholder="Or type a custom role (e.g. Frontend Engineer)"
                    className="w-full px-4 py-3 bg-[var(--background)] border border-[var(--border)] rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow"
                  />
                </div>
              ) : (
                <input
                  type="text"
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  placeholder="e.g. Software Engineer, Data Scientist"
                  className="w-full px-4 py-3 bg-[var(--background)] border border-[var(--border)] rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow"
                />
              )}
              <p className="text-xs text-[var(--muted-foreground)]">
                Tailor the interview focus to a specific job title.
              </p>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-4 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-all shadow-lg hover:shadow-blue-600/25 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                "Preparing Interview..."
              ) : (
                <>
                  <Play className="h-4 w-4 fill-current" />
                  Start Interview
                </>
              )}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
