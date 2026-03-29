export default function AboutPage() {
  return (
    <section className="mx-auto max-w-3xl px-6 py-20">
      <h1 className="text-4xl font-bold">About</h1>
      <div className="mt-8 space-y-6 text-gray-600 leading-relaxed">
        <p>
          SaaS Starter is a production-ready template for building modern web
          applications. It combines a Python/FastAPI backend with a Next.js
          frontend, deployed on Railway.
        </p>
        <p>
          Built with best practices in mind: type-safe code, test-driven
          development, secure authentication, and automated CI/CD. Everything
          you need to go from idea to production.
        </p>
        <h2 className="text-2xl font-bold text-gray-900 pt-4">Tech Stack</h2>
        <ul className="list-disc pl-6 space-y-2">
          <li>
            <strong>Backend:</strong> Python, FastAPI, SQLAlchemy, PostgreSQL, Redis
          </li>
          <li>
            <strong>Frontend:</strong> Next.js, React, Tailwind CSS, shadcn/ui
          </li>
          <li>
            <strong>Auth:</strong> JWT tokens, Google OAuth, httpOnly cookies
          </li>
          <li>
            <strong>Deploy:</strong> Railway with auto-deploy from GitHub
          </li>
          <li>
            <strong>CI/CD:</strong> GitHub Actions for tests and linting
          </li>
        </ul>
      </div>
    </section>
  );
}
