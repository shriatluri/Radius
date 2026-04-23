import { useState } from 'react'

// ─── Waitlist Form ───────────────────────────────────────────────────────────

function WaitlistForm({ center = false }) {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (email) setSubmitted(true)
  }

  if (submitted) {
    return (
      <p className={`text-[#888] text-sm ${center ? 'text-center' : ''}`}>
        You're on the list. We'll reach out to <span className="text-white">{email}</span>.
      </p>
    )
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={`flex flex-col sm:flex-row gap-3 ${center ? 'max-w-md mx-auto' : 'max-w-md'}`}
    >
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="you@company.com"
        required
        className="flex-1 bg-[#0a0a0a] border border-[#222] rounded-lg px-4 py-2.5 text-sm text-white placeholder-[#444] focus:outline-none focus:border-[#444] transition-colors"
      />
      <button
        type="submit"
        className="bg-white text-black px-6 py-2.5 rounded-lg font-medium text-sm hover:bg-[#e5e5e5] transition-colors whitespace-nowrap"
      >
        Join waitlist
      </button>
    </form>
  )
}

// ─── Nav ─────────────────────────────────────────────────────────────────────

function Nav() {
  const [open, setOpen] = useState(false)

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[#141414] bg-black/90 backdrop-blur-md">
      <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-[#7c3aed]" />
          <span className="font-semibold text-white text-sm tracking-tight">Radius</span>
        </div>

        <div className="hidden md:flex items-center gap-8 text-sm text-[#555]">
          <a href="#how-it-works" className="hover:text-white transition-colors">How it works</a>
          <a href="#features" className="hover:text-white transition-colors">Features</a>
          <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
        </div>

        <a
          href="#waitlist"
          className="hidden md:block text-sm bg-white text-black px-4 py-1.5 rounded-lg font-medium hover:bg-[#e5e5e5] transition-colors"
        >
          Join the waitlist
        </a>

        <button
          onClick={() => setOpen(!open)}
          className="md:hidden text-[#555] hover:text-white p-1"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            {open
              ? <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              : <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />}
          </svg>
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-[#141414] bg-black px-6 py-5 flex flex-col gap-4 text-sm">
          <a href="#how-it-works" onClick={() => setOpen(false)} className="text-[#555] hover:text-white">How it works</a>
          <a href="#features" onClick={() => setOpen(false)} className="text-[#555] hover:text-white">Features</a>
          <a href="#pricing" onClick={() => setOpen(false)} className="text-[#555] hover:text-white">Pricing</a>
          <a
            href="#waitlist"
            onClick={() => setOpen(false)}
            className="bg-white text-black px-4 py-2 rounded-lg font-medium text-center mt-2"
          >
            Join the waitlist
          </a>
        </div>
      )}
    </nav>
  )
}

// ─── Hero ─────────────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section className="pt-32 pb-24 px-6">
      <div className="max-w-5xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 border border-[#1a1a1a] bg-[#0a0a0a] text-[#666] text-xs font-medium px-4 py-1.5 rounded-full mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-[#22c55e]" />
          OFAC + EU + UN sanctions screening
        </div>

        <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold text-white leading-[1.05] tracking-tight mb-7 max-w-4xl mx-auto">
          The paper trail your
          <br className="hidden sm:block" />
          blockchain never had.
        </h1>

        <p className="text-lg text-[#777] max-w-2xl mx-auto leading-relaxed mb-10">
          Radius screens every stablecoin transfer against sanctions lists,
          checks Travel Rule thresholds across 30 jurisdictions, and hands you
          back a structured compliance record. One API call before you send. One after.
        </p>

        <div id="waitlist" className="mb-20">
          <WaitlistForm center />
          <p className="text-xs text-[#333] mt-3">Early access opening soon.</p>
        </div>

        {/* Code blocks */}
        <div className="w-full max-w-4xl mx-auto grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="border border-[#161616] rounded-2xl overflow-hidden bg-[#080808] text-left">
            <div className="flex items-center gap-1.5 px-4 py-3 border-b border-[#131313]">
              <div className="w-2.5 h-2.5 rounded-full bg-[#1a1a1a]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#1a1a1a]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#1a1a1a]" />
              <span className="ml-3 text-xs text-[#333] font-mono">request</span>
            </div>
            <div className="p-5 font-mono text-[13px] leading-7 overflow-x-auto">
              <div className="text-[#444]">// check before sending</div>
              <div>
                <span className="text-[#8b9dc3]">const </span>
                <span className="text-[#ddd]">result</span>
                <span className="text-[#555]"> = </span>
                <span className="text-[#8b9dc3]">await </span>
                <span className="text-[#ddd]">radius</span>
                <span className="text-[#555]">.</span>
                <span className="text-[#ddd]">check</span>
                <span className="text-[#555]">({'{'}</span>
              </div>
              <div className="pl-5">
                <span className="text-[#c9a87c]">from</span>
                <span className="text-[#555]">: </span>
                <span className="text-[#a5c5a0]">"0x742d35Cc..."</span>
                <span className="text-[#555]">,</span>
              </div>
              <div className="pl-5">
                <span className="text-[#c9a87c]">to</span>
                <span className="text-[#555]">: </span>
                <span className="text-[#a5c5a0]">"0x3fC91A3a..."</span>
                <span className="text-[#555]">,</span>
              </div>
              <div className="pl-5">
                <span className="text-[#c9a87c]">amount</span>
                <span className="text-[#555]">: </span>
                <span className="text-[#a5c5a0]">"2500.00"</span>
                <span className="text-[#555]">,</span>
              </div>
              <div className="pl-5">
                <span className="text-[#c9a87c]">asset</span>
                <span className="text-[#555]">: </span>
                <span className="text-[#a5c5a0]">"USDC"</span>
                <span className="text-[#555]">,</span>
              </div>
              <div className="pl-5">
                <span className="text-[#c9a87c]">purpose</span>
                <span className="text-[#555]">: </span>
                <span className="text-[#a5c5a0]">"contractor_payout"</span>
              </div>
              <div><span className="text-[#555]">{'}'})</span></div>
            </div>
          </div>

          <div className="border border-[#161616] rounded-2xl overflow-hidden bg-[#080808] text-left">
            <div className="flex items-center gap-1.5 px-4 py-3 border-b border-[#131313]">
              <div className="w-2.5 h-2.5 rounded-full bg-[#1a1a1a]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#1a1a1a]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#1a1a1a]" />
              <span className="ml-3 text-xs text-[#333] font-mono">response</span>
            </div>
            <div className="p-5 font-mono text-[13px] leading-7 overflow-x-auto">
              <div className="text-[#444]">// returns in ~200ms</div>
              <div className="text-[#555]">{'{'}</div>
              <div className="pl-5">
                <span className="text-[#c9a87c]">risk_level</span>
                <span className="text-[#555]">: </span>
                <span className="text-[#a5c5a0]">"low"</span>
                <span className="text-[#555]">,</span>
              </div>
              <div className="pl-5">
                <span className="text-[#c9a87c]">sanctions</span>
                <span className="text-[#555]">: </span>
                <span className="text-[#a5c5a0]">"clear"</span>
                <span className="text-[#555]">,</span>
              </div>
              <div className="pl-5">
                <span className="text-[#c9a87c]">travel_rule</span>
                <span className="text-[#555]">: </span>
                <span className="text-[#a5c5a0]">"not_required"</span>
                <span className="text-[#555]">,</span>
              </div>
              <div className="pl-5">
                <span className="text-[#c9a87c]">audit_id</span>
                <span className="text-[#555]">: </span>
                <span className="text-[#a5c5a0]">"aud_01HX8KmR9..."</span>
              </div>
              <div className="text-[#555]">{'}'}</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

// ─── Stats ───────────────────────────────────────────────────────────────────

function Stats() {
  const items = [
    { value: '751+', label: 'sanctioned addresses indexed' },
    { value: '30+', label: 'jurisdictions covered' },
    { value: '<300ms', label: 'average response time' },
    { value: 'Daily', label: 'OFAC SDN refresh cycle' },
  ]

  return (
    <div className="border-y border-[#111]">
      <div className="max-w-5xl mx-auto px-6 py-10 grid grid-cols-2 md:grid-cols-4 gap-8">
        {items.map((s) => (
          <div key={s.value} className="text-center">
            <div className="text-2xl sm:text-3xl font-bold text-white mb-1">{s.value}</div>
            <div className="text-sm text-[#444]">{s.label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Before / After ──────────────────────────────────────────────────────────

function BeforeAfter() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="max-w-2xl mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4 leading-tight">
            Your auditor can't read a blockchain.
          </h2>
          <p className="text-[#666] text-base leading-relaxed">
            A transaction hash proves money moved. It says nothing about who sent it,
            why, or whether the recipient is sanctioned. That gap is what gets you stuck
            at accounting close, bank review, or fundraising diligence.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-3">
          <div className="bg-[#080808] border border-[#161616] rounded-2xl p-6">
            <div className="text-xs font-medium text-[#444] uppercase tracking-wider mb-4">
              What your accountant gets today
            </div>
            <div className="font-mono text-sm text-[#2a2a2a] leading-8 break-all">
              0x5d3a1Bf4A11E5c8e9fC2b7d...
              <br />
              0x8f9e2Cc7B23A6d1f04a8e7c...
              <br />
              0x1a2b3c4d5e6f7a8b9c0d1e2...
            </div>
            <p className="text-xs text-[#333] mt-4">
              Three transfers. No idea who, why, or whether they were compliant.
            </p>
          </div>

          <div className="bg-[#070710] border border-[#18182a] rounded-2xl p-6">
            <div className="text-xs font-medium text-[#666] uppercase tracking-wider mb-4">
              What Radius gives them
            </div>
            <div className="font-mono text-xs text-[#666] leading-7">
              <span className="text-[#444]">{'{'}</span>
              <br />
              <span className="pl-4 text-[#c9a87c]">entity</span>
              <span className="text-[#444]">: </span>
              <span className="text-[#bbb]">"Acme Inc → Alice Smith"</span>
              <br />
              <span className="pl-4 text-[#c9a87c]">amount</span>
              <span className="text-[#444]">: </span>
              <span className="text-[#bbb]">"$2,500 USDC"</span>
              <br />
              <span className="pl-4 text-[#c9a87c]">purpose</span>
              <span className="text-[#444]">: </span>
              <span className="text-[#bbb]">"contractor_payout"</span>
              <br />
              <span className="pl-4 text-[#c9a87c]">sanctions</span>
              <span className="text-[#444]">: </span>
              <span className="text-[#7dab7d]">"clear"</span>
              <br />
              <span className="pl-4 text-[#c9a87c]">jurisdiction</span>
              <span className="text-[#444]">: </span>
              <span className="text-[#bbb]">"US → DE"</span>
              <br />
              <span className="text-[#444]">{'}'}</span>
            </div>
            <p className="text-xs text-[#555] mt-4">Same transfer. Now it's a financial record.</p>
          </div>
        </div>
      </div>
    </section>
  )
}

// ─── How It Works ────────────────────────────────────────────────────────────

function HowItWorks() {
  const steps = [
    {
      n: '01',
      title: 'Check before sending',
      endpoint: 'POST /v1/transactions/ingest',
      body: 'Submit sender, receiver, amount, and asset. Radius screens both wallets against OFAC, EU, and UN sanctions lists, scores risk 0\u2013100, and checks Travel Rule thresholds for the relevant jurisdictions.',
    },
    {
      n: '02',
      title: 'Link the on-chain hash',
      endpoint: 'POST /v1/payments/annotate',
      body: 'After the transfer broadcasts, send the tx hash. Radius links it to the compliance record and marks the audit trail as reconciled.',
    },
    {
      n: '03',
      title: 'Pull the record anytime',
      endpoint: 'GET /v1/transactions/:id/audit',
      body: 'Retrieve the full record as JSON or CSV. Entity names, risk score, sanctions result, Travel Rule status, approval chain. Hand it to your accountant, bank, or regulator.',
    },
  ]

  return (
    <section id="how-it-works" className="py-24 px-6 border-t border-[#111]">
      <div className="max-w-5xl mx-auto">
        <div className="max-w-2xl mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4 leading-tight">
            Three API calls. Full audit trail.
          </h2>
          <p className="text-[#666] text-base leading-relaxed">
            Radius sits between your payment logic and the blockchain. You don't
            change how you send. You just check first.
          </p>
        </div>

        <div className="space-y-3">
          {steps.map((s) => (
            <div key={s.n} className="bg-[#080808] border border-[#161616] rounded-2xl p-7 flex flex-col sm:flex-row sm:items-start gap-5">
              <div className="font-mono text-3xl font-bold text-[#161616] select-none flex-shrink-0 leading-none">
                {s.n}
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-3 mb-3">
                  <h3 className="text-base font-semibold text-white">{s.title}</h3>
                  <span className="font-mono text-xs text-[#444] border border-[#181818] bg-[#060606] px-3 py-1 rounded-full">
                    {s.endpoint}
                  </span>
                </div>
                <p className="text-sm text-[#555] leading-relaxed">{s.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── Features ────────────────────────────────────────────────────────────────

function Features() {
  const features = [
    {
      title: 'Sanctions Screening',
      body: 'Real-time checks against OFAC SDN (refreshed daily from Treasury.gov), EU consolidated list, and UN Security Council list via OpenSanctions. Risk scores 0\u2013100 on every check.',
      items: ['751+ OFAC-sanctioned addresses', 'EU & UN lists via OpenSanctions', 'Automatic daily data refresh', 'Sub-second response times'],
    },
    {
      title: 'Travel Rule Automation',
      body: 'Automatic detection of Travel Rule obligations based on originator and beneficiary jurisdiction. Uses the stricter threshold when transfers cross borders. FATF Recommendation 16 compliant.',
      items: ['30+ jurisdictions with accurate thresholds', 'Self-hosted wallet detection', 'Cross-border threshold resolution', 'VASP data exchange ready'],
    },
    {
      title: 'Audit-Ready Records',
      body: 'Every transaction becomes a structured financial object with entity names, purpose, risk score, sanctions result, and approval chain. Export as CSV or JSON anytime.',
      items: ['Immutable audit trail', 'CSV and JSON export', 'Wallet ownership verification', 'ERP integrations on roadmap'],
    },
  ]

  return (
    <section id="features" className="py-24 px-6 border-t border-[#111]">
      <div className="max-w-5xl mx-auto">
        <div className="max-w-2xl mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4 leading-tight">
            What you get
          </h2>
          <p className="text-[#666] text-base leading-relaxed">
            Sanctions screening, Travel Rule automation, and audit-ready records in a
            single API. No enterprise sales calls. No 6-month integrations.
          </p>
        </div>

        <div className="grid sm:grid-cols-3 gap-3">
          {features.map((f) => (
            <div key={f.title} className="bg-[#080808] border border-[#161616] rounded-2xl p-7">
              <h3 className="text-base font-semibold text-white mb-3">{f.title}</h3>
              <p className="text-sm text-[#555] leading-relaxed mb-5">{f.body}</p>
              <ul className="space-y-2">
                {f.items.map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm text-[#444]">
                    <span className="text-[#333] mt-px flex-shrink-0">-</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── Pricing ─────────────────────────────────────────────────────────────────

function Pricing() {
  const plans = [
    {
      name: 'Starter',
      price: '$99',
      period: '/mo',
      usage: '+ $0.10 per check',
      description: 'For seed-stage teams running stablecoin payments.',
      features: [
        'OFAC SDN screening (refreshed daily)',
        'Travel Rule detection, 30+ jurisdictions',
        'Structured audit records',
        'CSV and JSON export',
        'Email support',
      ],
    },
    {
      name: 'Growth',
      price: '$499',
      period: '/mo',
      usage: '+ $0.05 per check',
      description: 'For Series A companies scaling cross-border volume.',
      highlighted: true,
      features: [
        'OFAC + EU + UN sanctions screening',
        'Travel Rule with VASP data exchange',
        'Priority support, 4-hour SLA',
        'Dedicated Slack channel',
        'Volume discounts at 10K+ checks',
      ],
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      usage: null,
      description: 'Dedicated infrastructure and compliance guarantees.',
      features: [
        'Dedicated instance',
        'Custom uptime SLA',
        'SOC 2 Type II report',
        'ERP integrations (NetSuite, QuickBooks)',
        'Implementation support',
      ],
    },
  ]

  return (
    <section id="pricing" className="py-24 px-6 border-t border-[#111]">
      <div className="max-w-5xl mx-auto">
        <div className="max-w-2xl mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4 leading-tight">
            Pricing
          </h2>
          <p className="text-[#666] text-base leading-relaxed">
            Usage-based. No seat licenses. No annual commitments on Starter or Growth.
          </p>
        </div>

        <div className="grid sm:grid-cols-3 gap-3">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`flex flex-col rounded-2xl ${
                plan.highlighted
                  ? 'bg-[#070710] border border-[#18182a]'
                  : 'bg-[#080808] border border-[#161616]'
              }`}
            >
              <div className="p-6 flex-1">
                <div className="text-sm font-medium text-[#888] mb-4">{plan.name}</div>
                <div className="mb-1">
                  <span className="text-3xl font-bold text-white">{plan.price}</span>
                  {plan.period && (
                    <span className="text-sm text-[#444]">{plan.period}</span>
                  )}
                </div>
                {plan.usage ? (
                  <div className="text-xs text-[#444] mb-5">{plan.usage}</div>
                ) : (
                  <div className="mb-5" />
                )}
                <p className="text-sm text-[#555] mb-6 leading-relaxed">{plan.description}</p>
                <ul className="space-y-2.5">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-sm text-[#555]">
                      <span className="text-[#333] mt-px flex-shrink-0">-</span>
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="px-6 pb-6">
                <a
                  href="#waitlist"
                  className={`block text-center py-2.5 rounded-xl text-sm font-medium transition-colors ${
                    plan.highlighted
                      ? 'bg-white text-black hover:bg-[#e5e5e5]'
                      : 'border border-[#222] text-[#888] hover:border-[#444] hover:text-white'
                  }`}
                >
                  Join waitlist
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── CTA ─────────────────────────────────────────────────────────────────────

function CTA() {
  return (
    <section className="py-24 px-6 border-t border-[#111]">
      <div className="max-w-5xl mx-auto">
        <div className="bg-[#070710] border border-[#18182a] rounded-3xl p-12 md:p-20 text-center">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-5 leading-tight">
            Get early access
          </h2>
          <p className="text-[#666] text-base mb-8 max-w-md mx-auto leading-relaxed">
            We're onboarding design partners now. Drop your email and we'll get you set up.
          </p>
          <WaitlistForm center />
        </div>
      </div>
    </section>
  )
}

// ─── Footer ──────────────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer className="border-t border-[#111] py-12 px-6">
      <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-4 h-4 rounded-full bg-[#7c3aed]" />
            <span className="font-semibold text-white text-sm">Radius</span>
          </div>
          <p className="text-xs text-[#333] leading-relaxed">
            Payment attestation infrastructure<br />for stablecoin transfers.
          </p>
        </div>
        <div className="flex items-center gap-6 text-sm text-[#444]">
          <a href="#how-it-works" className="hover:text-white transition-colors">How it works</a>
          <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
          <a href="mailto:hello@getradius.com" className="hover:text-white transition-colors">Contact</a>
        </div>
      </div>
      <div className="max-w-5xl mx-auto mt-8 pt-6 border-t border-[#111]">
        <p className="text-xs text-[#222]">&copy; 2026 Radius.</p>
      </div>
    </footer>
  )
}

// ─── App ─────────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <div className="min-h-screen bg-black text-white">
      <Nav />
      <main>
        <Hero />
        <Stats />
        <BeforeAfter />
        <HowItWorks />
        <Features />
        <Pricing />
        <CTA />
      </main>
      <Footer />
    </div>
  )
}
