"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, setToken, storeUser } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api.post<{ access_token: string; user: any }>(
        "/auth/login", { email, password }
      );
      setToken(data.access_token);
      storeUser(data.user);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-base-950 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-accent-500">
            <span className="text-sm font-bold text-white">OA</span>
          </div>
          <h1 className="text-xl font-semibold text-base-100">Welcome back</h1>
          <p className="mt-1 text-sm text-base-500">Sign in to your account</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-2.5 text-sm text-red-400">
              {error}
            </div>
          )}
          <Input id="email" label="Email" type="email" value={email}
            onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required />
          <Input id="password" label="Password" type="password" value={password}
            onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required />
          <Button type="submit" loading={loading} className="w-full">Sign In</Button>
        </form>
        <p className="mt-6 text-center text-sm text-base-500">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-accent-400 hover:text-accent-300 transition-colors">Register</Link>
        </p>
      </div>
    </div>
  );
}
