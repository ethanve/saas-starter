"use client";

import Link from "next/link";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  function handleLogout() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/api/v1/auth/logout`, {
      method: "POST",
      credentials: "include",
    }).then(() => {
      window.location.href = "/login";
    });
  }

  return (
    <div className="flex min-h-screen">
      <aside className="relative w-64 border-r border-gray-200 bg-gray-50 p-6">
        <Link href="/dashboard" className="text-lg font-semibold">
          SaaS Starter
        </Link>
        <nav className="mt-8 space-y-1">
          <Link
            href="/dashboard"
            className="block rounded-lg px-3 py-2 text-sm font-medium text-gray-900 hover:bg-gray-100"
          >
            Dashboard
          </Link>
        </nav>
        <div className="absolute bottom-6 left-6">
          <button
            onClick={handleLogout}
            className="text-sm text-gray-500 hover:text-gray-900"
          >
            Log out
          </button>
        </div>
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
