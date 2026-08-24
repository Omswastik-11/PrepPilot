"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import Link from "next/link";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const login = useAuthStore((state) => state.login);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      // Create FormData as expected by OAuth2PasswordRequestForm
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const data = await fetchApi("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData,
      });

      // Assuming backend returns { access_token: "...", token_type: "bearer" }
      // We also need user details. PrepPilot's login endpoint might just return the token.
      // So we fetch the user profile next.
      const token = data.access_token;
      
      const userData = await fetchApi("/api/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      login(token, userData);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Failed to login");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-[var(--background)]">
      <div className="w-full max-w-md p-8 space-y-6 bg-[var(--sidebar-background)] rounded-2xl border border-[var(--border)] shadow-sm">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-[var(--foreground)]">Welcome back</h1>
          <p className="text-sm text-[var(--muted-foreground)] mt-2">Sign in to PrepPilot</p>
        </div>

        {error && (
          <div className="p-3 text-sm text-red-500 bg-red-500/10 rounded-lg text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
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
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            {isLoading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div className="text-center text-sm text-[var(--muted-foreground)] mt-4">
          Don't have an account?{" "}
          <Link href="/register" className="text-blue-600 hover:underline">
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
}
