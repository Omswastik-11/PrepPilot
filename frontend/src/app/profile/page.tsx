"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Heatmap } from "@/components/Heatmap";
import { ScoreTrend } from "@/components/ScoreTrend";
import { useAuthStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { User, FileText, Upload, Briefcase, Code, Loader2, MapPin, GraduationCap, Building, Edit2, CheckCircle2, TrendingUp, X, Sparkles } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export default function Profile() {
  const { user } = useAuthStore();
  const router = useRouter();

  const [profile, setProfile] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [recentInterviews, setRecentInterviews] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  
  // Edit Profile State
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: "",
    bio: "",
    institute: "",
    qualification: "",
  });

  useEffect(() => {
    if (!user) {
      router.push("/login");
      return;
    }
    fetchData();
  }, [user, router]);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [profileData, analyticsData, interviewsData] = await Promise.all([
        fetchApi("/api/candidate/profiles/me").catch(() => null),
        fetchApi("/api/candidate/analytics").catch(() => null),
        fetchApi("/api/interviews?limit=10").catch(() => [])
      ]);
      setProfile(profileData);
      setAnalytics(analyticsData);
      setRecentInterviews(interviewsData.items || interviewsData || []);
      if (profileData) {
        setEditForm({
          name: profileData.name || "",
          bio: profileData.bio || "",
          institute: profileData.institute || "",
          qualification: profileData.qualification || "",
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSynthesize = async () => {
    try {
      setIsSynthesizing(true);
      await fetchApi("/api/candidate/synthesize", { method: "POST" });
      await fetchData();
    } catch (err) {
      console.error("Failed to synthesize profile:", err);
    } finally {
      setIsSynthesizing(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setIsUploading(true);
      const formData = new FormData();
      formData.append("file", file);

      const token = useAuthStore.getState().token;
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_BASE_URL}/api/candidate/documents`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      
      if (!res.ok) throw new Error("Upload failed");
      await fetchData(); 
    } catch (err) {
      console.error(err);
    } finally {
      setIsUploading(false);
      if (e.target) e.target.value = "";
    }
  };

  const handleSaveProfile = async () => {
    try {
      const data = await fetchApi("/api/candidate/profiles/me", {
        method: "PATCH",
        body: JSON.stringify(editForm)
      });
      setProfile(data);
      setIsEditing(false);
    } catch (err) {
      console.error(err);
    }
  };

  if (!user) return null;

  if (isLoading) {
    return (
      <div className="flex h-screen overflow-hidden bg-[var(--background)]">
        <Sidebar />
        <main className="flex-1 p-4 md:p-8 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            <p className="text-[var(--muted-foreground)]">Loading profile...</p>
          </div>
        </main>
      </div>
    );
  }

  // Calculate donut chart segments
  const diffs = analytics?.difficulty_breakdown || { easy: 0, medium: 0, hard: 0 };
  const totalQuestions = (diffs.easy || 0) + (diffs.medium || 0) + (diffs.hard || 0);
  
  // Circumference for SVG circle (r=15.9155 => c=100)
  const easyPct = totalQuestions ? ((diffs.easy || 0) / totalQuestions) * 100 : 0;
  const mediumPct = totalQuestions ? ((diffs.medium || 0) / totalQuestions) * 100 : 0;
  const hardPct = totalQuestions ? ((diffs.hard || 0) / totalQuestions) * 100 : 0;

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--background)]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-4 md:p-8">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row gap-8">
          
          {/* LEFT COLUMN: IDENTITY */}
          <div className="w-full md:w-80 shrink-0 space-y-6">
            <div className="bg-[var(--sidebar-background)] border border-[var(--border)]/50 rounded-xl p-5 shadow-sm relative">
              <button 
                onClick={() => setIsEditing(true)}
                className="absolute top-4 right-4 p-1.5 bg-transparent hover:bg-[var(--muted)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] rounded-md transition-colors"
                title="Edit Profile"
              >
                <Edit2 className="w-3.5 h-3.5" />
              </button>
              
              <div className="flex flex-col items-center text-center">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-blue-500/20 mb-3">
                  {profile?.name ? profile.name.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                </div>
                <h1 className="text-lg font-bold text-[var(--foreground)]">
                  {profile?.name || "Anonymous User"}
                </h1>
                <p className="text-xs text-[var(--muted-foreground)] mb-3">
                  @{user.email.split('@')[0]}
                </p>
                <p className="text-xs text-[var(--muted-foreground)] mb-5 leading-relaxed">
                  {profile?.bio || "A candidate who is enthusiastic about coding and interview prep."}
                </p>
              </div>

              <div className="space-y-2.5 text-xs text-[var(--muted-foreground)] border-t border-[var(--border)]/50 pt-5">
                <div className="flex items-center gap-2">
                  <GraduationCap className="w-3.5 h-3.5" />
                  <span className="truncate">{profile?.institute || "No Institute Specified"}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Briefcase className="w-3.5 h-3.5" />
                  <span className="truncate">{profile?.qualification || "No Qualification Specified"}</span>
                </div>
              </div>

              <div className="mt-5 pt-5 border-t border-[var(--border)]/50">
                <h3 className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted-foreground)] mb-2">Resume</h3>
                <label className="relative cursor-pointer group w-full flex items-center justify-center gap-2 py-1.5 px-3 bg-[var(--muted)]/50 hover:bg-[var(--muted)] text-[var(--foreground)] text-xs font-medium rounded-lg transition-colors border border-[var(--border)]/50">
                  {isUploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
                  {isUploading ? "Uploading..." : "Upload Resume PDF"}
                  <input 
                    type="file" 
                    className="hidden" 
                    accept=".pdf,.docx"
                    onChange={handleFileUpload}
                    disabled={isUploading}
                  />
                </label>
              </div>
            </div>

            {/* Resume Extracted Skills (Left column continuation) */}
            {profile?.skills?.length > 0 && (
              <div className="bg-[var(--sidebar-background)] border border-[var(--border)]/50 rounded-xl p-5 shadow-sm">
                <h3 className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted-foreground)] mb-3">Extracted Skills</h3>
                <div className="flex flex-wrap gap-1.5">
                  {profile.skills.map((skill: string, i: number) => (
                    <span key={i} className="px-2 py-0.5 bg-[var(--muted)]/50 text-[var(--foreground)] text-[11px] font-medium rounded-md border border-[var(--border)]/50">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* RIGHT COLUMN: ANALYTICS & DASHBOARD */}
          <div className="flex-1 space-y-6">
            
            {/* Top Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Left Column - Takes 1/3 of space */}
              <div className="flex flex-col gap-4 col-span-1">
                <div className="bg-[var(--sidebar-background)] border border-[var(--border)]/50 rounded-xl p-4 flex flex-col justify-between shadow-sm flex-1">
                  <span className="text-xs font-medium text-[var(--muted-foreground)]">Interviews Taken</span>
                  <div className="flex items-end gap-2 mt-2">
                    <span className="text-2xl font-bold">{analytics?.total_interviews || 0}</span>
                  </div>
                </div>
                <div className="bg-[var(--sidebar-background)] border border-[var(--border)]/50 rounded-xl p-4 flex flex-col justify-between shadow-sm flex-1 relative overflow-hidden">
                  <div className="flex justify-between items-start relative z-10">
                    <span className="text-xs font-medium text-[var(--muted-foreground)]">Average Score</span>
                    {recentInterviews?.length > 1 && (
                      <span className="text-[10px] text-blue-500 bg-blue-500/10 px-1.5 py-0.5 rounded font-medium">Trend</span>
                    )}
                  </div>
                  <div className="flex items-end gap-2 mt-2 relative z-10">
                    <span className="text-2xl font-bold">{analytics?.average_overall_score || "N/A"}</span>
                    {analytics?.average_overall_score && <span className="text-xs text-[var(--muted-foreground)] mb-1">/ 10</span>}
                  </div>
                  
                  {recentInterviews?.length > 1 && (
                    <div className="absolute bottom-0 left-0 right-0 h-16 opacity-30 pointer-events-none">
                      <ScoreTrend scores={recentInterviews
                        .filter(i => i.status === 'completed' && i.total_score !== null)
                        .map(i => i.total_score)
                        .reverse()} 
                      />
                    </div>
                  )}
                </div>
              </div>
              
              {/* Right Column - Takes 2/3 of space. LeetCode style Donut Chart */}
              <div className="bg-[var(--sidebar-background)] border border-[var(--border)]/50 rounded-xl p-5 shadow-sm h-full col-span-1 md:col-span-2 flex flex-col">
                <span className="text-xs font-medium text-[var(--muted-foreground)] block mb-4">Interview Difficulty</span>
                <div className="flex items-center justify-around flex-1">
                  {/* Large Pie Chart */}
                  <div className="relative w-32 h-32 md:w-40 md:h-40 flex items-center justify-center">
                    <svg viewBox="0 0 36 36" className="w-full h-full transform -rotate-90">
                      <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="var(--border)" strokeWidth="1.5" />
                      {/* Using slightly thicker strokes for emphasis */}
                      <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#10b981" strokeWidth="2.5" strokeDasharray={`${easyPct} ${100 - easyPct}`} strokeDashoffset="0" strokeLinecap="round" />
                      <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#eab308" strokeWidth="2.5" strokeDasharray={`${mediumPct} ${100 - mediumPct}`} strokeDashoffset={`-${easyPct}`} strokeLinecap="round" />
                      <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#ef4444" strokeWidth="2.5" strokeDasharray={`${hardPct} ${100 - hardPct}`} strokeDashoffset={`-${easyPct + mediumPct}`} strokeLinecap="round" />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                      <span className="text-3xl font-bold text-[var(--foreground)]">{totalQuestions}</span>
                      <span className="text-[10px] text-[var(--muted-foreground)]">Questions</span>
                    </div>
                  </div>
                  
                  {/* Right side stats blocks (LeetCode style) */}
                  <div className="flex flex-col gap-2 w-32 md:w-40">
                    <div className="bg-[var(--muted)]/40 rounded-lg p-2.5 flex flex-col items-center justify-center border border-[var(--border)]/30">
                      <span className="text-[11px] font-medium text-emerald-500 mb-0.5">Easy</span>
                      <span className="text-sm font-semibold text-[var(--foreground)]">{diffs.easy || 0}</span>
                    </div>
                    <div className="bg-[var(--muted)]/40 rounded-lg p-2.5 flex flex-col items-center justify-center border border-[var(--border)]/30">
                      <span className="text-[11px] font-medium text-yellow-500 mb-0.5">Med.</span>
                      <span className="text-sm font-semibold text-[var(--foreground)]">{diffs.medium || 0}</span>
                    </div>
                    <div className="bg-[var(--muted)]/40 rounded-lg p-2.5 flex flex-col items-center justify-center border border-[var(--border)]/30">
                      <span className="text-[11px] font-medium text-red-500 mb-0.5">Hard</span>
                      <span className="text-sm font-semibold text-[var(--foreground)]">{diffs.hard || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Activity Heatmap */}
            <div className="bg-[var(--sidebar-background)] border border-[var(--border)]/50 rounded-xl p-5 shadow-sm">
              <h3 className="font-semibold text-sm text-[var(--foreground)] mb-4 pb-3 border-b border-[var(--border)]/50">Submissions in the past one year</h3>
              <Heatmap data={analytics?.activity_heatmap || []} />
            </div>

            {/* Strengths & Weaknesses (Badges) */}
            <div className="flex justify-end mb-4">
               <button 
                 onClick={handleSynthesize}
                 disabled={isSynthesizing || !recentInterviews?.length}
                 className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
                 title="Analyze past interviews to generate high-level strengths and weaknesses"
               >
                 {isSynthesizing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                 Synthesize AI Profile
               </button>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="bg-[var(--sidebar-background)] border border-[var(--border)]/50 rounded-xl p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-4 pb-3 border-b border-[var(--border)]/50">
                  <TrendingUp className="w-4 h-4 text-emerald-500" />
                  <h3 className="font-semibold text-sm text-[var(--foreground)]">Identified Strengths</h3>
                </div>
                {analytics?.strengths?.length > 0 ? (
                  <ul className="space-y-3">
                    {analytics.strengths.map((s: string, i: number) => (
                      <li key={i} className="flex items-start gap-2.5 text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500/70 shrink-0 mt-0.5" />
                        <span className="leading-relaxed">{s}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-center py-6">
                    <p className="text-xs text-[var(--muted-foreground)] mb-4">Complete interviews to discover your strengths.</p>
                    <Link href="/">
                      <button className="px-3 py-1.5 bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/20 text-xs font-medium rounded-lg transition-colors">
                        Start Interview
                      </button>
                    </Link>
                  </div>
                )}
              </div>
              
              <div className="bg-[var(--sidebar-background)] border border-[var(--border)]/50 rounded-xl p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-4 pb-3 border-b border-[var(--border)]/50">
                  <TrendingUp className="w-4 h-4 text-red-500 transform rotate-180" />
                  <h3 className="font-semibold text-sm text-[var(--foreground)]">Areas for Improvement</h3>
                </div>
                {analytics?.areas_for_improvement?.length > 0 ? (
                  <ul className="space-y-3">
                    {analytics.areas_for_improvement.map((w: string, i: number) => (
                      <li key={i} className="flex items-start gap-2.5 text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors">
                        <div className="w-1.5 h-1.5 rounded-full bg-red-500/70 shrink-0 mt-1.5" />
                        <span className="leading-relaxed">{w}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-center py-6">
                    <p className="text-xs text-[var(--muted-foreground)] mb-4">Complete interviews to discover your areas for improvement.</p>
                    <Link href="/">
                      <button className="px-3 py-1.5 bg-red-500/10 text-red-600 hover:bg-red-500/20 text-xs font-medium rounded-lg transition-colors">
                        Start Interview
                      </button>
                    </Link>
                  </div>
                )}
              </div>
            </div>

          </div>
        </div>
      </main>

      {/* Edit Profile Modal */}
      {isEditing && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--sidebar-background)] border border-[var(--border)] rounded-3xl w-full max-w-md p-6 shadow-2xl relative">
            <button 
              onClick={() => setIsEditing(false)}
              className="absolute top-4 right-4 p-2 text-[var(--muted-foreground)] hover:text-[var(--foreground)] bg-[var(--muted)] rounded-full transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
            <h2 className="text-xl font-bold mb-6 text-[var(--foreground)]">Edit Profile</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-[var(--muted-foreground)] mb-1">Name</label>
                <input 
                  type="text" 
                  value={editForm.name}
                  onChange={e => setEditForm({...editForm, name: e.target.value})}
                  className="w-full bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2 text-sm text-[var(--foreground)] focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[var(--muted-foreground)] mb-1">Institute / University</label>
                <input 
                  type="text" 
                  value={editForm.institute}
                  onChange={e => setEditForm({...editForm, institute: e.target.value})}
                  className="w-full bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2 text-sm text-[var(--foreground)] focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[var(--muted-foreground)] mb-1">Qualification</label>
                <input 
                  type="text" 
                  value={editForm.qualification}
                  onChange={e => setEditForm({...editForm, qualification: e.target.value})}
                  className="w-full bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2 text-sm text-[var(--foreground)] focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[var(--muted-foreground)] mb-1">Bio</label>
                <textarea 
                  value={editForm.bio}
                  onChange={e => setEditForm({...editForm, bio: e.target.value})}
                  rows={3}
                  className="w-full bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2 text-sm text-[var(--foreground)] focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-none"
                />
              </div>
              <button 
                onClick={handleSaveProfile}
                className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-xl transition-colors shadow-lg shadow-blue-600/25"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
