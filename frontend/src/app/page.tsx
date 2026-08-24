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
  const [numQuestions, setNumQuestions] = useState(5);
  const [company, setCompany] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) {
      router.push("/login");
    }
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
          num_questions: numQuestions,
          company: company.trim() || null,
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
              <label className="text-sm font-semibold flex justify-between">
                <span>Number of Questions</span>
                <span className="text-blue-600 bg-blue-600/10 px-2 py-0.5 rounded text-xs">{numQuestions}</span>
              </label>
              <input 
                type="range" 
                min="3" 
                max="10" 
                value={numQuestions}
                onChange={(e) => setNumQuestions(parseInt(e.target.value))}
                className="w-full accent-blue-600"
              />
              <div className="flex justify-between text-xs text-[var(--muted-foreground)]">
                <span>Short (3)</span>
                <span>Long (10)</span>
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
