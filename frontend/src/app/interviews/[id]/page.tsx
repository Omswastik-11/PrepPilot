"use client";

import { useState, useEffect, useRef } from "react";
import { Send, User, ChevronLeft } from "lucide-react";
import { Sidebar } from "@/components/Sidebar";
import { useAuthStore } from "@/lib/store";
import { useRouter, useParams } from "next/navigation";
import { fetchApi } from "@/lib/api";
import Link from "next/link";

interface Answer {
  id: string;
  user_answer: string;
  time_taken_seconds: number;
  score: number;
  feedback: string;
  strengths: string[];
  weaknesses: string[];
}

interface Question {
  id: string;
  question_text: string;
  question_order: number;
  answer?: Answer | null;
}

interface Interview {
  id: string;
  interview_type: string;
  status: string;
  num_questions: number;
  questions: Question[];
}

export default function InterviewChat() {
  const { user } = useAuthStore();
  const router = useRouter();
  const params = useParams();
  const interviewId = params.id as string;

  const [interview, setInterview] = useState<Interview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [input, setInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [questionStartTime, setQuestionStartTime] = useState<number>(0);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const fetchInterview = async () => {
    try {
      const data = await fetchApi(`/api/interviews/${interviewId}`);
      setInterview(data);
      
      // Update timer if there's a new active question
      const activeQ = data.questions.find((q: Question) => !q.answer);
      if (activeQ) {
        setQuestionStartTime(Date.now());
      }
    } catch (err: any) {
      setError(err.message || "Failed to load interview");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!user) {
      router.push("/login");
      return;
    }
    if (interviewId) {
      fetchInterview();
    }
  }, [user, interviewId, router]);

  useEffect(() => {
    // Auto-scroll to bottom
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [interview, submitting]);

  if (loading) {
    return (
      <div className="flex h-screen overflow-hidden bg-[var(--background)]">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <div className="animate-pulse flex space-x-2">
            <div className="h-3 w-3 bg-blue-600 rounded-full"></div>
            <div className="h-3 w-3 bg-blue-600 rounded-full animation-delay-200"></div>
            <div className="h-3 w-3 bg-blue-600 rounded-full animation-delay-400"></div>
          </div>
        </main>
      </div>
    );
  }

  if (error || !interview) {
    return (
      <div className="flex h-screen overflow-hidden bg-[var(--background)]">
        <Sidebar />
        <main className="flex-1 flex flex-col items-center justify-center space-y-4">
          <div className="text-red-500 bg-red-500/10 px-6 py-4 rounded-xl border border-red-500/20">
            {error || "Interview not found"}
          </div>
          <Link href="/">
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium">Return Home</button>
          </Link>
        </main>
      </div>
    );
  }

  const activeQuestion = interview.questions.find(q => !q.answer);
  const isComplete = interview.status === "completed" || !activeQuestion;

  const handleSubmit = async () => {
    if (!input.trim() || !activeQuestion || submitting) return;

    const timeTaken = Math.max(1, Math.floor((Date.now() - questionStartTime) / 1000));
    setSubmitting(true);
    setError("");

    try {
      await fetchApi(`/api/interviews/${interview.id}/questions/${activeQuestion.id}/answer`, {
        method: "POST",
        body: JSON.stringify({
          user_answer: input.trim(),
          time_taken_seconds: timeTaken,
        }),
      });

      setInput("");
      await fetchInterview(); // Reload the whole interview state
      
      // If no active question left after reload, we should mark complete
      // (Backend might auto-complete or we might need to call complete endpoint)
      // For now, let's just reload. The next render will see if it's complete.
    } catch (err: any) {
      setError(err.message || "Failed to submit answer");
    } finally {
      setSubmitting(false);
    }
  };

  const handleComplete = async () => {
    try {
      await fetchApi(`/api/interviews/${interview.id}/complete`, { method: "POST" });
      await fetchInterview();
    } catch (err: any) {
      setError(err.message || "Failed to complete interview");
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--background)]">
      <Sidebar />

      <main className="flex-1 flex flex-col relative">
        <header className="flex h-14 items-center justify-between px-4 border-b border-[var(--border)]">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors">
              <ChevronLeft className="h-5 w-5" />
            </Link>
            <div className="font-medium capitalize">{interview.interview_type} Interview</div>
          </div>
          <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1 bg-[var(--muted)] rounded-full text-[var(--muted-foreground)]">
            {interview.status.replace("_", " ")}
          </div>
        </header>

        {error && (
          <div className="m-4 p-3 text-sm text-red-500 bg-red-500/10 rounded-lg text-center absolute top-14 left-0 right-0 z-10 mx-auto max-w-xl">
            {error}
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-4 space-y-8 max-w-4xl mx-auto w-full pb-32">
          {interview.questions.map((q, idx) => (
            <div key={q.id} className="space-y-6">
              {/* Question Bubble */}
              {((q.answer) || (activeQuestion?.id === q.id)) && (
                <div className="flex gap-4">
                  <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0 mt-1">
                    <span className="text-white text-xs font-bold">AI</span>
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="font-semibold text-sm">PrepPilot <span className="text-[var(--muted-foreground)] font-normal text-xs ml-2">Question {q.question_order} of {interview.num_questions}</span></p>
                    <div className="text-[var(--foreground)] leading-relaxed pt-1">
                      {q.question_text}
                    </div>
                  </div>
                </div>
              )}

              {/* Answer Bubble */}
              {q.answer && (
                <div className="flex gap-4 flex-row-reverse">
                  <div className="h-8 w-8 rounded-full bg-[var(--muted)] flex items-center justify-center shrink-0 mt-1">
                    <User className="h-4 w-4 text-[var(--muted-foreground)]" />
                  </div>
                  <div className="flex-1 flex flex-col items-end space-y-1">
                    <p className="font-semibold text-sm">You <span className="text-[var(--muted-foreground)] font-normal text-xs mr-2">{q.answer.time_taken_seconds}s</span></p>
                    <div className="bg-[var(--muted)] rounded-2xl rounded-tr-sm px-4 py-3 text-[var(--foreground)] leading-relaxed max-w-[85%] whitespace-pre-wrap">
                      {q.answer.user_answer}
                    </div>
                  </div>
                </div>
              )}

              {/* Evaluation Card */}
              {q.answer && (
                <div className="flex gap-4">
                  <div className="h-8 w-8 shrink-0"></div>
                  <div className="flex-1 bg-[var(--sidebar-background)] border border-[var(--border)] rounded-2xl p-5 space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-sm text-[var(--muted-foreground)] uppercase tracking-wider">AI Evaluation</h4>
                      <div className={`font-bold text-lg ${q.answer.score >= 8 ? 'text-green-500' : q.answer.score >= 5 ? 'text-yellow-500' : 'text-red-500'}`}>
                        {q.answer.score}/10
                      </div>
                    </div>
                    <p className="text-sm leading-relaxed">{q.answer.feedback}</p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                      {q.answer.strengths?.length > 0 && (
                        <div className="space-y-2">
                          <h5 className="text-xs font-semibold text-green-600 flex items-center gap-1">Strengths</h5>
                          <ul className="text-sm space-y-1 text-[var(--muted-foreground)] list-disc pl-4">
                            {q.answer.strengths.map((s, i) => <li key={i}>{s}</li>)}
                          </ul>
                        </div>
                      )}
                      {q.answer.weaknesses?.length > 0 && (
                        <div className="space-y-2">
                          <h5 className="text-xs font-semibold text-red-600 flex items-center gap-1">Areas to Improve</h5>
                          <ul className="text-sm space-y-1 text-[var(--muted-foreground)] list-disc pl-4">
                            {q.answer.weaknesses.map((w, i) => <li key={i}>{w}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}

          {submitting && (
            <div className="flex gap-4">
              <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
                <span className="text-white text-xs font-bold">AI</span>
              </div>
              <div className="flex-1 space-y-2 pt-1">
                <div className="flex space-x-1 items-center h-6">
                  <div className="h-2 w-2 bg-[var(--muted-foreground)] rounded-full animate-bounce"></div>
                  <div className="h-2 w-2 bg-[var(--muted-foreground)] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="h-2 w-2 bg-[var(--muted-foreground)] rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                </div>
                <p className="text-xs text-[var(--muted-foreground)]">Evaluating your answer...</p>
              </div>
            </div>
          )}

          {isComplete && interview.status !== "completed" && !submitting && (
            <div className="flex justify-center pt-8">
              <button 
                onClick={handleComplete}
                className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-xl transition-colors shadow-lg shadow-green-600/20"
              >
                Complete Interview
              </button>
            </div>
          )}

          {interview.status === "completed" && (
            <div className="flex flex-col items-center justify-center pt-12 space-y-4">
              <div className="h-16 w-16 bg-green-500/20 text-green-500 rounded-full flex items-center justify-center text-3xl mb-2">🎉</div>
              <h2 className="text-2xl font-bold">Interview Complete!</h2>
              <p className="text-[var(--muted-foreground)]">You have successfully finished all questions.</p>
              <Link href="/">
                <button className="mt-4 px-6 py-3 bg-[var(--sidebar-background)] border border-[var(--border)] hover:bg-[var(--muted)] font-semibold rounded-xl transition-colors">
                  Return to Dashboard
                </button>
              </Link>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        {!isComplete && (
          <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[var(--background)] via-[var(--background)] to-transparent pt-10">
            <div className="max-w-4xl mx-auto w-full">
              <div className={`relative flex items-center bg-[var(--sidebar-background)] rounded-2xl border border-[var(--border)] focus-within:ring-1 focus-within:ring-[var(--border)] transition-shadow shadow-lg ${submitting ? 'opacity-50' : ''}`}>
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit();
                    }
                  }}
                  placeholder="Type your answer here..."
                  className="w-full bg-transparent resize-none py-4 pl-4 pr-16 focus:outline-none max-h-48 min-h-[56px] text-sm"
                  rows={2}
                  disabled={submitting}
                />
                <button 
                  onClick={handleSubmit}
                  className="absolute right-3 p-2.5 rounded-xl bg-blue-600 text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:hover:bg-blue-600" 
                  disabled={!input.trim() || submitting}
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
              <div className="text-center mt-2 text-xs text-[var(--muted-foreground)] font-medium">
                AI responses may be inaccurate. Press Shift + Enter for a new line.
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
