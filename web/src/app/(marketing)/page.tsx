import Link from "next/link";

export default function HomePage() {
  return (
    <div>
      {/* Hero */}
      <section className="mx-auto max-w-4xl px-6 py-24 text-center">
        <h1 className="text-5xl font-bold tracking-tight">
          Build your SaaS faster
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-gray-600">
          A production-ready starter template with authentication, teams,
          file uploads, and deployment — so you can focus on what makes your
          product unique.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link
            href="/signup"
            className="rounded-lg bg-gray-900 px-6 py-3 text-sm font-medium text-white hover:bg-gray-800"
          >
            Get Started Free
          </Link>
          <Link
            href="/about"
            className="rounded-lg border border-gray-300 px-6 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Learn More
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-gray-200 bg-gray-50 py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-3xl font-bold">
            Everything you need to launch
          </h2>
          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div key={feature.title} className="rounded-xl bg-white p-6 shadow-sm">
                <div className="text-2xl">{feature.icon}</div>
                <h3 className="mt-4 text-lg font-semibold">{feature.title}</h3>
                <p className="mt-2 text-sm text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="mx-auto max-w-2xl px-6 text-center">
          <h2 className="text-3xl font-bold">Ready to get started?</h2>
          <p className="mt-4 text-gray-600">
            Create your account and start building in minutes.
          </p>
          <Link
            href="/signup"
            className="mt-8 inline-block rounded-lg bg-gray-900 px-8 py-3 text-sm font-medium text-white hover:bg-gray-800"
          >
            Start Building
          </Link>
        </div>
      </section>
    </div>
  );
}

const features = [
  {
    icon: "\uD83D\uDD10",
    title: "Authentication",
    description:
      "JWT + OAuth with Google. Secure httpOnly cookies, account lockout, and password hashing with Argon2.",
  },
  {
    icon: "\uD83D\uDC65",
    title: "Teams & Organizations",
    description:
      "Multi-tenant architecture with organizations, role-based access control, and member management.",
  },
  {
    icon: "\uD83D\uDCC1",
    title: "File Uploads",
    description:
      "Upload files through the API with automatic storage management. Works with Railway volumes in production.",
  },
  {
    icon: "\uD83D\uDE80",
    title: "One-Click Deploy",
    description:
      "Deploy to Railway with PostgreSQL, Redis, and persistent volumes. GitHub auto-deploy on every push.",
  },
  {
    icon: "\uD83E\uDDEA",
    title: "Test-Driven Development",
    description:
      "Pytest for the API, with fixtures and test client ready to go. CI runs tests on every pull request.",
  },
  {
    icon: "\uD83E\uDD16",
    title: "AI-Powered Development",
    description:
      "Built for Claude Code with gstack skills. Ship features faster with AI-assisted coding and review.",
  },
];
