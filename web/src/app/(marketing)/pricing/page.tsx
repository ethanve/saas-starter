import Link from "next/link";

export default function PricingPage() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-20">
      <div className="text-center">
        <h1 className="text-4xl font-bold">Simple, transparent pricing</h1>
        <p className="mt-4 text-lg text-gray-600">
          Start free. Scale as you grow.
        </p>
      </div>

      <div className="mt-16 grid gap-8 lg:grid-cols-3">
        {tiers.map((tier) => (
          <div
            key={tier.name}
            className={`rounded-xl border p-8 ${
              tier.featured
                ? "border-gray-900 shadow-lg"
                : "border-gray-200"
            }`}
          >
            <h3 className="text-lg font-semibold">{tier.name}</h3>
            <div className="mt-4">
              <span className="text-4xl font-bold">{tier.price}</span>
              {tier.period && (
                <span className="text-gray-500">/{tier.period}</span>
              )}
            </div>
            <p className="mt-4 text-sm text-gray-600">{tier.description}</p>
            <ul className="mt-8 space-y-3">
              {tier.features.map((feature) => (
                <li key={feature} className="flex items-start gap-2 text-sm">
                  <span className="text-green-600">&#10003;</span>
                  {feature}
                </li>
              ))}
            </ul>
            <Link
              href="/signup"
              className={`mt-8 block rounded-lg px-4 py-2.5 text-center text-sm font-medium ${
                tier.featured
                  ? "bg-gray-900 text-white hover:bg-gray-800"
                  : "border border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              {tier.cta}
            </Link>
          </div>
        ))}
      </div>
    </section>
  );
}

const tiers = [
  {
    name: "Free",
    price: "$0",
    period: "month",
    description: "Perfect for side projects and experimentation.",
    featured: false,
    cta: "Get Started",
    features: [
      "Up to 3 team members",
      "1 GB file storage",
      "Community support",
      "Basic analytics",
    ],
  },
  {
    name: "Pro",
    price: "$29",
    period: "month",
    description: "For growing teams that need more power.",
    featured: true,
    cta: "Start Free Trial",
    features: [
      "Unlimited team members",
      "50 GB file storage",
      "Priority support",
      "Advanced analytics",
      "Custom domains",
      "API access",
    ],
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: null,
    description: "For large organizations with specific needs.",
    featured: false,
    cta: "Contact Sales",
    features: [
      "Everything in Pro",
      "Unlimited storage",
      "Dedicated support",
      "SLA guarantee",
      "SSO / SAML",
      "Audit logs",
    ],
  },
];
