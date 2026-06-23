"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useAuthStore } from "@/stores/auth"

export default function RegisterPage() {
  const [form, setForm] = useState({ email: "", username: "", password: "", full_name: "" })
  const [error, setError] = useState("")
  const { register, loading } = useAuthStore()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    try {
      await register(form)
      router.push("/dashboard")
    } catch {
      setError("Registration failed. Try a different email or username.")
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-white">OpenPaper</h1>
          <p className="text-muted-foreground text-sm">Create your account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg p-3">
              {error}
            </div>
          )}

          {(["full_name", "username", "email", "password"] as const).map((field) => (
            <div key={field} className="space-y-2">
              <label className="text-sm text-muted-foreground capitalize">
                {field.replace("_", " ")}
              </label>
              <input
                type={field === "password" ? "password" : field === "email" ? "email" : "text"}
                value={form[field]}
                onChange={(e) => setForm({ ...form, [field]: e.target.value })}
                className="flex h-10 w-full rounded-lg border border-border bg-base-950/50 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent-500/50"
                placeholder={field === "email" ? "you@example.com" : field === "password" ? "••••••••" : field.replace("_", " ")}
                required={field !== "full_name"}
              />
            </div>
          ))}

          <button
            type="submit"
            disabled={loading}
            className="w-full h-10 bg-accent-500 text-white rounded-lg font-medium hover:bg-accent-600 transition-colors disabled:opacity-50"
          >
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="text-accent-400 hover:text-accent-300">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
