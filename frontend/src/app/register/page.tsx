"use client";

import { useState } from "react";
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
  const router = useRouter();
  const login = useAuthStore((state) => state.login);

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

  return (
    <div className="flex h-screen items-center justify-center bg-[var(--background)]">
      <div className="w-full max-w-md p-8 space-y-6 bg-[var(--sidebar-background)] rounded-2xl border border-[var(--border)] shadow-sm">
        <div className="text-center">
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
