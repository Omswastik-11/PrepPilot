"use client";

import { useState, useEffect, useRef } from "react";
import { Send, User, ChevronLeft, Maximize2, Minimize2, CheckCircle2 } from "lucide-react";
import { Sidebar } from "@/components/Sidebar";
import { useAuthStore } from "@/lib/store";
import { useRouter, useParams } from "next/navigation";
import { fetchApi } from "@/lib/api";
import Link from "next/link";
import { motion } from "framer-motion";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";

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
  difficulty?: string;
  topic?: string;
  answer?: Answer | null;
}

interface Interview {
  id: string;
  interview_type: string;
  status: string;
  num_questions: number | null;
  duration_minutes: number | null;
  started_at: string | null;
  questions: Question[];
  total_score: number | null;
}

const getGrade = (score: number) => {
  if (score >= 9) return { grade: 'A+', color: 'text-emerald-500' };
  if (score >= 8) return { grade: 'A', color: 'text-emerald-500' };
  if (score >= 7) return { grade: 'B', color: 'text-green-500' };
  if (score >= 5) return { grade: 'C', color: 'text-yellow-500' };
  if (score >= 3) return { grade: 'D', color: 'text-orange-500' };
  return { grade: 'F', color: 'text-red-500' };
};

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
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedIdeal, setExpandedIdeal] = useState<Record<string, boolean>>({});
  const [questionStartTime, setQuestionStartTime] = useState<number>(0);
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [showEndModal, setShowEndModal] = useState(false);
  const [isTimeUp, setIsTimeUp] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const formatTime = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const m = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
    const s = (totalSeconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

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
    if (interview && interview.status === "in_progress" && interview.duration_minutes && interview.started_at) {
      const interval = setInterval(() => {
        const dateStr = interview.started_at!.endsWith('Z') ? interview.started_at! : interview.started_at + 'Z';
        const start = new Date(dateStr).getTime();
        const durationMs = interview.duration_minutes! * 60 * 1000;
        const now = Date.now();
        const remaining = Math.max(0, start + durationMs - now);
        setTimeLeft(remaining);
        
        if (remaining === 0 && !isTimeUp) {
          setIsTimeUp(true);
          setShowEndModal(true);
        }
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [interview, isTimeUp]);

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
      setIsExpanded(false);
    }
  };

  const handleComplete = async () => {
    try {
      await fetchApi(`/api/interviews/${interview.id}/complete`, { method: "POST" });
      setShowEndModal(false);
      await fetchInterview();
    } catch (err: any) {
      setError(err.message || "Failed to complete interview");
      setShowEndModal(false);
    }
  };

  const handleTerminate = async () => {
    try {
      await fetchApi(`/api/interviews/${interview.id}/abandon`, { method: "POST" });
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Failed to terminate interview");
      setShowEndModal(false);
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
          <div className="flex items-center gap-3">
            {timeLeft !== null && interview.status === "in_progress" && (
              <div className={`font-mono text-sm font-semibold px-3 py-1 rounded-full ${
                timeLeft < 60000 ? "bg-red-500/10 text-red-500" : timeLeft < 300000 ? "bg-yellow-500/10 text-yellow-600" : "bg-green-500/10 text-green-600"
              }`}>
                {formatTime(timeLeft)}
              </div>
            )}
            {interview.status === "in_progress" && (
              <button 
                onClick={() => setShowEndModal(true)}
                className="text-xs font-semibold px-3 py-1.5 bg-[var(--muted)] hover:bg-red-500/10 hover:text-red-500 transition-colors rounded-lg text-[var(--muted-foreground)]"
              >
                End Interview
              </button>
            )}
            <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1 bg-[var(--sidebar-background)] border border-[var(--border)] rounded-full text-[var(--muted-foreground)]">
              {interview.status.replace("_", " ")}
            </div>
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
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="flex gap-4">
                  <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0 mt-1">
                    <span className="text-white text-xs font-bold">AI</span>
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-sm">PrepPilot <span className="text-[var(--muted-foreground)] font-normal text-xs ml-2">Question {q.question_order} of {interview.num_questions}</span></p>
                      {q.difficulty && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 font-medium">
                          {q.difficulty}
                        </span>
                      )}
                      {q.topic && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-500 font-medium">
                          {q.topic}
                        </span>
                      )}
                    </div>
                    <div className="text-[var(--foreground)] leading-relaxed pt-1">
                      <MarkdownRenderer content={q.question_text} />
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Answer Bubble */}
              {q.answer && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: 0.1 }} className="flex gap-4 flex-row-reverse">
                  <div className="h-8 w-8 rounded-full bg-[var(--muted)] flex items-center justify-center shrink-0 mt-1">
                    <User className="h-4 w-4 text-[var(--muted-foreground)]" />
                  </div>
                  <div className="flex-1 flex flex-col items-end space-y-1">
                    <p className="font-semibold text-sm">You <span className="text-[var(--muted-foreground)] font-normal text-xs mr-2">{q.answer.time_taken_seconds}s</span></p>
                    <div className="bg-[var(--muted)] rounded-2xl rounded-tr-sm px-4 py-3 text-[var(--foreground)] leading-relaxed max-w-[85%] whitespace-pre-wrap">
                      <MarkdownRenderer content={q.answer.user_answer} />
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Evaluation Card */}
              {q.answer && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.2 }} className="flex gap-4">
                  <div className="h-8 w-8 shrink-0"></div>
                  <div className="flex-1 bg-[var(--sidebar-background)] border border-[var(--border)] rounded-2xl p-5 space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-sm text-[var(--muted-foreground)] uppercase tracking-wider">AI Evaluation</h4>
                      <div className={`font-bold text-lg ${q.answer.score >= 8 ? 'text-green-500' : q.answer.score >= 5 ? 'text-yellow-500' : 'text-red-500'}`}>
                        {q.answer.score}/10
                      </div>
                    </div>
                    <div className="text-sm leading-relaxed">
                      <MarkdownRenderer content={q.answer.feedback} />
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                      {q.answer.strengths?.length > 0 && (
                        <div className="space-y-2">
                          <h5 className="text-xs font-semibold text-green-600 flex items-center gap-1">Strengths</h5>
                          <ul className="text-sm space-y-1 text-[var(--muted-foreground)] list-disc pl-4">
                            {q.answer.strengths.map((s, i) => (
                              <li key={i}><MarkdownRenderer content={s} inline /></li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {q.answer.weaknesses?.length > 0 && (
                        <div className="space-y-2">
                          <h5 className="text-xs font-semibold text-red-600 flex items-center gap-1">Areas to Improve</h5>
                          <ul className="text-sm space-y-1 text-[var(--muted-foreground)] list-disc pl-4">
                            {q.answer.weaknesses.map((w, i) => (
                              <li key={i}><MarkdownRenderer content={w} inline /></li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    <button 
                      onClick={() => setExpandedIdeal(prev => ({ ...prev, [q.id]: !prev[q.id] }))} 
                      className="text-xs text-blue-500 hover:underline mt-4 font-medium"
                    >
                      {expandedIdeal[q.id] ? "Hide" : "Show"} Ideal Approach Hints
                    </button>
                    
                    {expandedIdeal[q.id] && (
                      <div className="text-sm mt-2 p-3 bg-[var(--muted)]/50 rounded-lg border border-[var(--border)] leading-relaxed">
                        <strong className="block text-xs uppercase tracking-wider text-[var(--muted-foreground)] mb-1">Based on feedback:</strong>
                        <MarkdownRenderer content={q.answer.feedback} />
                      </div>
                    )}
                  </div>
                </motion.div>
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
            <div className="flex flex-col items-center justify-center pt-8 pb-12 space-y-8">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5 }}>
                <div className="flex items-center gap-2 text-xs text-emerald-500 bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-500/20 shadow-sm">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Your strengths & areas for improvement have been updated
                </div>
              </motion.div>
              
              <div className="text-center space-y-2">
                <div className="h-20 w-20 bg-green-500/20 text-green-500 rounded-full flex items-center justify-center text-4xl mx-auto mb-4">🏆</div>
                <h2 className="text-3xl font-bold">Interview Complete</h2>
                <p className="text-[var(--muted-foreground)]">Here is your overall performance verdict.</p>
              </div>

              <div className="w-full max-w-2xl bg-[var(--sidebar-background)] border border-[var(--border)] rounded-2xl p-8 shadow-xl space-y-8">
                <div className="flex flex-col md:flex-row items-center justify-between gap-6 pb-8 border-b border-[var(--border)]">
                  <div className="space-y-1 text-center md:text-left">
                    <div className="text-sm font-semibold text-[var(--muted-foreground)] uppercase tracking-wider">Overall Score</div>
                    <div className={`text-6xl font-black ${interview.total_score! >= 8 ? 'text-green-500' : interview.total_score! >= 5 ? 'text-yellow-500' : 'text-red-500'}`}>
                      {interview.total_score || 0}<span className="text-2xl text-[var(--muted-foreground)]">/10</span>
                    </div>
                  </div>
                  
                  <div className="space-y-1 text-center md:text-right">
                    <div className="text-sm font-semibold text-[var(--muted-foreground)] uppercase tracking-wider">Grade</div>
                    <div className={`text-6xl font-black ${getGrade(interview.total_score || 0).color}`}>
                      {getGrade(interview.total_score || 0).grade}
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">Question Breakdown</h3>
                  <div className="overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--background)]">
                    <table className="w-full text-sm text-left">
                      <thead className="bg-[var(--muted)] text-[var(--muted-foreground)] text-xs uppercase font-semibold">
                        <tr>
                          <th className="px-4 py-3 w-12 text-center">#</th>
                          <th className="px-4 py-3">Topic</th>
                          <th className="px-4 py-3 w-24 text-right">Score</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[var(--border)]">
                        {interview.questions.map((q) => (
                          <tr key={q.id} className="hover:bg-[var(--muted)]/50 transition-colors">
                            <td className="px-4 py-3 text-center font-medium text-[var(--muted-foreground)]">{q.question_order}</td>
                            <td className="px-4 py-3 font-medium truncate max-w-xs" title={q.topic}>{q.topic || 'General'}</td>
                            <td className={`px-4 py-3 text-right font-bold ${q.answer?.score && q.answer.score >= 8 ? 'text-green-500' : q.answer?.score && q.answer.score >= 5 ? 'text-yellow-500' : 'text-red-500'}`}>
                              {q.answer?.score ? `${q.answer.score}/10` : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                
                <div className="flex gap-4 justify-center pt-4">
                  <Link href="/profile">
                    <button className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors shadow-lg shadow-blue-600/20">
                      View Profile Analytics
                    </button>
                  </Link>
                  <Link href="/">
                    <button className="px-6 py-3 bg-[var(--muted)] hover:bg-[var(--border)] font-semibold rounded-xl transition-colors">
                      Start Another
                    </button>
                  </Link>
                </div>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        {!isComplete && (
          <>
            {isExpanded && (
              <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40" onClick={() => setIsExpanded(false)} />
            )}
            <div className={isExpanded 
              ? "fixed inset-4 md:inset-10 lg:inset-x-32 lg:inset-y-16 z-50 bg-[var(--sidebar-background)] border border-[var(--border)] rounded-2xl shadow-2xl flex flex-col"
              : "absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[var(--background)] via-[var(--background)] to-transparent pt-10"}>
              
              <div className={isExpanded ? "flex-1 flex flex-col h-full relative" : "max-w-4xl mx-auto w-full"}>
                {isExpanded && (
                  <div className="flex justify-between items-center p-4 border-b border-[var(--border)]">
                    <h3 className="font-semibold text-[var(--foreground)]">Write Answer</h3>
                    <button onClick={() => setIsExpanded(false)} className="p-2 text-[var(--muted-foreground)] hover:bg-[var(--muted)] rounded-lg transition-colors">
                      <Minimize2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
                
                <div className={`relative flex flex-col items-center bg-[var(--sidebar-background)] ${!isExpanded ? 'rounded-2xl border border-[var(--border)] focus-within:ring-1 focus-within:ring-[var(--border)] shadow-lg' : 'flex-1'} ${submitting ? 'opacity-50' : ''} transition-shadow`}>
                  <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit();
                      }
                    }}
                    placeholder="Type your answer here... (Press Shift + Enter for new line)"
                    className={`w-full bg-transparent resize-none p-4 focus:outline-none text-sm text-[var(--foreground)] ${isExpanded ? 'flex-1 min-h-0' : 'max-h-48 min-h-[56px] pr-24'}`}
                    rows={isExpanded ? undefined : 2}
                    disabled={submitting}
                  />
                  
                  <div className={`flex items-center gap-2 ${isExpanded ? 'p-4 border-t border-[var(--border)] w-full justify-between' : 'absolute right-3 bottom-3'}`}>
                    {isExpanded && (
                      <div className="text-xs text-[var(--muted-foreground)] hidden sm:block">
                        AI responses may be inaccurate. Press Shift + Enter for a new line.
                      </div>
                    )}
                    
                    <div className="flex items-center gap-2 ml-auto">
                      {!isExpanded && (
                        <button 
                          onClick={() => setIsExpanded(true)}
                          className="p-2 rounded-xl text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--foreground)] transition-colors"
                          title="Expand input"
                        >
                          <Maximize2 className="h-4 w-4" />
                        </button>
                      )}
                      <button 
                        onClick={handleSubmit}
                        className="p-2.5 rounded-xl bg-blue-600 text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:hover:bg-blue-600 flex items-center gap-2" 
                        disabled={!input.trim() || submitting}
                      >
                        {isExpanded && <span className="text-sm font-medium px-1">Submit</span>}
                        <Send className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
                
                {!isExpanded && (
                  <div className="text-center mt-2 text-xs text-[var(--muted-foreground)] font-medium">
                    AI responses may be inaccurate. Press Shift + Enter for a new line.
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* End Interview Modal */}
        {showEndModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4" onClick={(e) => { if (!isTimeUp && e.target === e.currentTarget) setShowEndModal(false); }}>
            <div className="bg-[var(--sidebar-background)] border border-[var(--border)] p-6 rounded-2xl max-w-md w-full shadow-2xl space-y-6 animate-in zoom-in-95 duration-200">
              <div>
                <h3 className="text-xl font-bold">{isTimeUp ? "Time's Up!" : "End Interview"}</h3>
                <p className="text-[var(--muted-foreground)] mt-2">
                  What would you like to do with this interview?
                </p>
              </div>
              
              <div className="space-y-3">
                <button 
                  onClick={() => handleComplete()}
                  className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors text-left flex justify-between items-center"
                >
                  <span>Finish & Generate Verdict</span>
                  <span className="text-blue-200 text-xs font-normal">Save progress</span>
                </button>
                
                <button 
                  onClick={handleTerminate}
                  className="w-full px-4 py-3 bg-[var(--muted)] hover:bg-red-500/10 hover:text-red-500 rounded-xl font-medium transition-colors text-left flex justify-between items-center"
                >
                  <span>Terminate</span>
                  <span className="text-[var(--muted-foreground)] text-xs font-normal group-hover:text-red-400">No data saved</span>
                </button>
              </div>
              
              {!isTimeUp && (
                <button 
                  onClick={() => setShowEndModal(false)}
                  className="w-full py-2 text-sm font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
                >
                  Cancel, return to interview
                </button>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
