"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import Link from "next/link";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isGuestLoading, setIsGuestLoading] = useState(false);
  const router = useRouter();
  const login = useAuthStore((state) => state.login);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const errorMsg = params.get("error");
      if (errorMsg) {
        setError(errorMsg);
      }
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      // 1. Register the user
      await fetchApi("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, name }),
      });

      // 2. Automatically log them in right after registration
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const loginData = await fetchApi("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData,
      });

      const token = loginData.access_token;
      
      // 3. Fetch their profile data
      const userData = await fetchApi("/api/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      // 4. Save to global state and redirect
      login(token, userData);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Failed to register account");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGuestLogin = async () => {
    setError("");
    setIsGuestLoading(true);

    try {
      const data = await fetchApi("/api/auth/guest", {
        method: "POST",
      });

      const token = data.access_token;
      const userData = await fetchApi("/api/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      login(token, userData);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Failed to start guest trial");
    } finally {
      setIsGuestLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-[var(--background)] relative overflow-hidden">
      {/* Decorative gradient background */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-500/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-500/20 rounded-full blur-[120px] pointer-events-none" />
      
      <div className="w-full max-w-md p-8 space-y-6 bg-[var(--sidebar-background)]/80 backdrop-blur-xl rounded-3xl border border-[var(--border)] shadow-2xl relative z-10">
        <div className="text-center">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl mx-auto flex items-center justify-center mb-4 shadow-lg shadow-blue-500/20">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" x2="19" y1="8" y2="14"/><line x1="22" x2="16" y1="11" y2="11"/></svg>
          </div>
          <h1 className="text-2xl font-bold text-[var(--foreground)]">Create an account</h1>
          <p className="text-sm text-[var(--muted-foreground)] mt-2">Get started with PrepPilot</p>
        </div>

        {error && (
          <div className="p-3 text-sm text-red-500 bg-red-500/10 rounded-lg text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow"
              placeholder="Optional"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow"
              required
              minLength={8}
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            {isLoading ? "Creating account..." : "Sign Up"}
          </button>
        </form>

        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-[var(--border)]" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-[var(--sidebar-background)] px-2 text-[var(--muted-foreground)]">Or continue with</span>
          </div>
        </div>

        <div className="space-y-3">
          <button
            onClick={() => {
              const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
              window.location.href = `${API_BASE_URL}/api/auth/google/login`;
            }}
            className="w-full flex items-center justify-center gap-2 py-2 px-4 bg-[var(--background)] border border-[var(--border)] hover:bg-[var(--muted)] text-[var(--foreground)] font-medium rounded-lg transition-colors"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Google
          </button>

          <button
            type="button"
            onClick={handleGuestLogin}
            disabled={isGuestLoading}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-gradient-to-r from-blue-600/10 via-indigo-600/10 to-purple-600/10 border border-blue-500/30 hover:border-blue-500/60 hover:bg-blue-500/15 text-[var(--foreground)] font-semibold rounded-lg transition-all shadow-sm"
          >
            <span>⚡</span>
            <span>{isGuestLoading ? "Starting Guest Trial..." : "Try 1 Mock Interview as Guest"}</span>
          </button>
        </div>

        <div className="text-center text-sm text-[var(--muted-foreground)] mt-4">
          Already have an account?{" "}
          <Link href="/login" className="text-blue-600 hover:underline">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
