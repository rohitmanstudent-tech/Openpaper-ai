import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-base-950 px-4">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-accent-500">
        <span className="text-base font-bold text-white">OA</span>
      </div>
      <h1 className="text-2xl font-bold text-base-100">OpenPaper AI</h1>
      <p className="mt-1 text-base text-base-500">Enterprise AI agent management platform</p>
      <div className="mt-8 flex gap-3">
        <Link
          href="/login"
          className="rounded-md bg-accent-500 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-accent-600"
        >
          Sign In
        </Link>
        <Link
          href="/register"
          className="rounded-md border border-base-700/50 px-5 py-2.5 text-sm font-medium text-base-300 transition-colors hover:bg-base-800"
        >
          Get Started
        </Link>
      </div>
    </div>
  );
}
