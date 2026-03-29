export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <p className="mt-2 text-gray-600">
        Welcome to your SaaS application. Start building from here.
      </p>
      <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-xl border border-gray-200 p-6">
          <h3 className="font-semibold">Getting Started</h3>
          <p className="mt-2 text-sm text-gray-600">
            Edit this page at{" "}
            <code className="rounded bg-gray-100 px-1 py-0.5 text-xs">
              src/app/(app)/dashboard/page.tsx
            </code>
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 p-6">
          <h3 className="font-semibold">API Routes</h3>
          <p className="mt-2 text-sm text-gray-600">
            Your API is running at{" "}
            <code className="rounded bg-gray-100 px-1 py-0.5 text-xs">
              localhost:8000/api/v1
            </code>
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 p-6">
          <h3 className="font-semibold">Documentation</h3>
          <p className="mt-2 text-sm text-gray-600">
            Check CLAUDE.md for architecture docs, deployment guides, and
            coding conventions.
          </p>
        </div>
      </div>
    </div>
  );
}
