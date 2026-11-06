"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore, useToastStore } from "@/lib/store";
import { fetchApi } from "@/lib/api";
import { Loader2 } from "lucide-react";

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const login = useAuthStore((state) => state.login);
  const showToast = useToastStore((state) => state.show);

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      showToast("Authentication failed", "error");
      router.push("/login");
      return;
    }

    // Fetch user profile with the new token
    fetchApi("/api/auth/me", {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
      .then((userData) => {
        login(token, userData);
        showToast("Successfully logged in with Google", "success");
        router.push("/");
      })
      .catch((err) => {
        console.error("Failed to fetch user data:", err);
        showToast("Authentication failed", "error");
        router.push("/login");
      });
  }, [searchParams, router, login, showToast]);

  return (
    <div className="flex h-screen items-center justify-center bg-[var(--background)]">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <p className="text-[var(--muted-foreground)] text-sm font-medium">Completing sign in...</p>
      </div>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center bg-[var(--background)]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      </div>
    }>
      <AuthCallbackContent />
    </Suspense>
  );
}
