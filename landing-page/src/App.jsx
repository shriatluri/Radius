import { useState, useEffect } from 'react'

// ─── Theme ───────────────────────────────────────────────────────────────────

function useTheme() {
  const [dark, setDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') === 'dark'
    }
    return false
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  return [dark, () => setDark((d) => !d)]
}

const Sun = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
  </svg>
)

const Moon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
  </svg>
)

// ─── Signup Form ─────────────────────────────────────────────────────────────

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function SignupForm({ center = false }) {
  const [email, setEmail] = useState('')
  const [company, setCompany] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [copied, setCopied] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email || !company) return
    setLoading(true)
    setError('')

    try {
      const res = await fetch(`${API_URL}/v1/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ business_name: company, email }),
      })

      if (res.status === 409) {
        setError('An account already exists for this email.')
        setLoading(false)
        return
      }
      if (!res.ok) {
        setError('Something went wrong. Please try again.')
        setLoading(false)
        return
      }

      const data = await res.json()
      setApiKey(data.api_key)
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(apiKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (apiKey) {
    return (
      <div className={`max-w-md ${center ? 'mx-auto text-center' : ''}`}>
        <p className="text-sm font-medium mb-2" style={{ color: 'var(--text-1)' }}>
          Your API key
        </p>
        <div
          className="flex items-center gap-2 rounded-lg px-4 py-2.5 font-mono text-sm mb-2"
          style={{ backgroundColor: 'var(--bg-code)', border: '1px solid var(--border)' }}
        >
          <span className="flex-1 truncate text-left" style={{ color: 'var(--text-1)' }}>{apiKey}</span>
          <button
            onClick={handleCopy}
            className="flex-shrink-0 text-xs px-3 py-1 rounded-md font-medium transition-colors"
            style={{ backgroundColor: 'var(--btn-bg)', color: 'var(--btn-text)' }}
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
        <p className="text-xs" style={{ color: 'var(--text-4)' }}>
          Save this key now — it won't be shown again.
        </p>
      </div>
    )
  }

  return (
    <div className={center ? 'max-w-md mx-auto' : 'max-w-md'}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="Company name"
            required
            className="flex-1 rounded-lg px-4 py-2.5 text-sm focus:outline-none transition-colors"
            style={{
              backgroundColor: 'var(--bg-input)',
              border: '1px solid var(--border)',
              color: 'var(--text-1)',
            }}
          />
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            required
            className="flex-1 rounded-lg px-4 py-2.5 text-sm focus:outline-none transition-colors"
            style={{
              backgroundColor: 'var(--bg-input)',
              border: '1px solid var(--border)',
              color: 'var(--text-1)',
            }}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2.5 rounded-lg font-medium text-sm transition-colors whitespace-nowrap disabled:opacity-60"
          style={{
            backgroundColor: 'var(--btn-bg)',
            color: 'var(--btn-text)',
          }}
        >
          {loading ? 'Creating account…' : 'Get API Key'}
        </button>
      </form>
      {error && (
        <p className={`text-sm mt-3 ${center ? 'text-center' : ''}`} style={{ color: '#ef4444' }}>
          {error}
        </p>
      )}
    </div>
  )
}

// ─── Nav ─────────────────────────────────────────────────────────────────────

function Nav({ dark, toggleTheme }) {
  const [open, setOpen] = useState(false)

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md"
      style={{ backgroundColor: 'var(--bg-nav)', borderBottom: '1px solid var(--border)' }}
    >
      <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full" style={{ backgroundColor: 'var(--accent)' }} />
          <span className="font-semibold text-sm tracking-tight" style={{ color: 'var(--text-1)' }}>
            Radius
          </span>
        </div>

        <div className="hidden md:flex items-center gap-8 text-sm" style={{ color: 'var(--text-3)' }}>
          <a href="#how-it-works" className="hover:opacity-80 transition-opacity">How it works</a>
          <a href="#features" className="hover:opacity-80 transition-opacity">Features</a>
          <a href="#pricing" className="hover:opacity-80 transition-opacity">Pricing</a>
          <a href="/docs" className="hover:opacity-80 transition-opacity">Docs</a>
        </div>

        <div className="hidden md:flex items-center gap-3">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg transition-colors"
            style={{ color: 'var(--text-3)', border: '1px solid var(--border)' }}
            aria-label="Toggle theme"
          >
            {dark ? <Sun /> : <Moon />}
          </button>
          <a
            href="#waitlist"
            className="text-sm px-4 py-1.5 rounded-lg font-medium transition-colors"
            style={{ backgroundColor: 'var(--btn-bg)', color: 'var(--btn-text)' }}
          >
            Get API Key
          </a>
        </div>

        <div className="md:hidden flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg"
            style={{ color: 'var(--text-3)' }}
            aria-label="Toggle theme"
          >
            {dark ? <Sun /> : <Moon />}
          </button>
          <button
            onClick={() => setOpen(!open)}
            className="p-1"
            style={{ color: 'var(--text-3)' }}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              {open
                ? <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                : <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />}
            </svg>
          </button>
        </div>
      </div>

      {open && (
        <div
          className="md:hidden px-6 py-5 flex flex-col gap-4 text-sm"
          style={{ backgroundColor: 'var(--bg)', borderTop: '1px solid var(--border)' }}
        >
          <a href="#how-it-works" onClick={() => setOpen(false)} className="hover:opacity-80" style={{ color: 'var(--text-3)' }}>How it works</a>
          <a href="#features" onClick={() => setOpen(false)} className="hover:opacity-80" style={{ color: 'var(--text-3)' }}>Features</a>
          <a href="#pricing" onClick={() => setOpen(false)} className="hover:opacity-80" style={{ color: 'var(--text-3)' }}>Pricing</a>
          <a href="/docs" onClick={() => setOpen(false)} className="hover:opacity-80" style={{ color: 'var(--text-3)' }}>Docs</a>
          <a
            href="#waitlist"
            onClick={() => setOpen(false)}
            className="px-4 py-2 rounded-lg font-medium text-center mt-2"
            style={{ backgroundColor: 'var(--btn-bg)', color: 'var(--btn-text)' }}
          >
            Get API Key
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
        <div
          className="inline-flex items-center gap-2 text-xs font-medium px-4 py-1.5 rounded-full mb-8"
          style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border)',
            color: 'var(--text-3)',
          }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#22c55e]" />
          OFAC + EU + UN sanctions screening
        </div>

        <h1
          className="text-5xl sm:text-6xl md:text-7xl font-bold leading-[1.05] tracking-tight mb-7 max-w-4xl mx-auto"
          style={{ color: 'var(--text-1)' }}
        >
          The paper trail your
          <br className="hidden sm:block" />
          blockchain never had.
        </h1>

        <p className="text-lg max-w-2xl mx-auto leading-relaxed mb-10" style={{ color: 'var(--text-2)' }}>
          Radius screens every stablecoin transfer against sanctions lists,
          checks Travel Rule thresholds across 30 jurisdictions, and hands you
          back a structured compliance record. One API call before you send. One after.
        </p>

        <div id="waitlist" className="mb-20">
          <SignupForm center />
          <p className="text-xs mt-3" style={{ color: 'var(--text-4)' }}>
            Free sandbox — no credit card required.
          </p>
        </div>

        {/* Code blocks */}
        <div className="w-full max-w-4xl mx-auto grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            className="rounded-2xl overflow-hidden text-left"
            style={{ backgroundColor: 'var(--bg-code)', border: '1px solid var(--border)' }}
          >
            <div
              className="flex items-center gap-1.5 px-4 py-3"
              style={{ borderBottom: '1px solid var(--border)' }}
            >
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--dot)' }} />
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--dot)' }} />
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--dot)' }} />
              <span className="ml-3 text-xs font-mono" style={{ color: 'var(--text-4)' }}>request</span>
            </div>
            <div className="p-5 font-mono text-[13px] leading-7 overflow-x-auto">
              <div style={{ color: 'var(--code-cmt)' }}>// check before sending</div>
              <div>
                <span style={{ color: 'var(--code-kw)' }}>const </span>
                <span style={{ color: 'var(--text-1)' }}>result</span>
                <span style={{ color: 'var(--code-punc)' }}> = </span>
                <span style={{ color: 'var(--code-kw)' }}>await </span>
                <span style={{ color: 'var(--text-1)' }}>radius</span>
                <span style={{ color: 'var(--code-punc)' }}>.</span>
                <span style={{ color: 'var(--text-1)' }}>check</span>
                <span style={{ color: 'var(--code-punc)' }}>({'{'}</span>
              </div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>from</span>
                <span style={{ color: 'var(--code-punc)' }}>: </span>
                <span style={{ color: 'var(--code-str)' }}>"0x742d35Cc..."</span>
                <span style={{ color: 'var(--code-punc)' }}>,</span>
              </div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>to</span>
                <span style={{ color: 'var(--code-punc)' }}>: </span>
                <span style={{ color: 'var(--code-str)' }}>"0x3fC91A3a..."</span>
                <span style={{ color: 'var(--code-punc)' }}>,</span>
              </div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>amount</span>
                <span style={{ color: 'var(--code-punc)' }}>: </span>
                <span style={{ color: 'var(--code-str)' }}>"2500.00"</span>
                <span style={{ color: 'var(--code-punc)' }}>,</span>
              </div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>asset</span>
                <span style={{ color: 'var(--code-punc)' }}>: </span>
                <span style={{ color: 'var(--code-str)' }}>"USDC"</span>
                <span style={{ color: 'var(--code-punc)' }}>,</span>
              </div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>purpose</span>
                <span style={{ color: 'var(--code-punc)' }}>: </span>
                <span style={{ color: 'var(--code-str)' }}>"contractor_payout"</span>
              </div>
              <div><span style={{ color: 'var(--code-punc)' }}>{'}'})</span></div>
            </div>
          </div>

          <div
            className="rounded-2xl overflow-hidden text-left"
            style={{ backgroundColor: 'var(--bg-code)', border: '1px solid var(--border)' }}
          >
            <div
              className="flex items-center gap-1.5 px-4 py-3"
              style={{ borderBottom: '1px solid var(--border)' }}
            >
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--dot)' }} />
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--dot)' }} />
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--dot)' }} />
              <span className="ml-3 text-xs font-mono" style={{ color: 'var(--text-4)' }}>response</span>
            </div>
            <div className="p-5 font-mono text-[13px] leading-7 overflow-x-auto">
              <div style={{ color: 'var(--code-cmt)' }}>// returns in ~200ms</div>
              <div style={{ color: 'var(--code-punc)' }}>{'{'}</div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>risk_level</span>
                <span style={{ color: 'var(--code-punc)' }}>: </span>
                <span style={{ color: 'var(--code-str)' }}>"low"</span>
                <span style={{ color: 'var(--code-punc)' }}>,</span>
              </div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>sanctions</span>
                <span style={{ color: 'var(--code-punc)' }}>: </span>
                <span style={{ color: 'var(--code-str)' }}>"clear"</span>
                <span style={{ color: 'var(--code-punc)' }}>,</span>
              </div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>travel_rule</span>
                <span style={{ color: 'var(--code-punc)' }}>: </span>
                <span style={{ color: 'var(--code-str)' }}>"not_required"</span>
                <span style={{ color: 'var(--code-punc)' }}>,</span>
              </div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>audit_id</span>
                <span style={{ color: 'var(--code-punc)' }}>: </span>
                <span style={{ color: 'var(--code-str)' }}>"aud_01HX8KmR9..."</span>
              </div>
              <div style={{ color: 'var(--code-punc)' }}>{'}'}</div>
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
    <div style={{ borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
      <div className="max-w-5xl mx-auto px-6 py-10 grid grid-cols-2 md:grid-cols-4 gap-8">
        {items.map((s) => (
          <div key={s.value} className="text-center">
            <div className="text-2xl sm:text-3xl font-bold mb-1" style={{ color: 'var(--text-1)' }}>
              {s.value}
            </div>
            <div className="text-sm" style={{ color: 'var(--text-3)' }}>{s.label}</div>
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
          <h2 className="text-3xl sm:text-4xl font-bold mb-4 leading-tight" style={{ color: 'var(--text-1)' }}>
            Your auditor can't read a blockchain.
          </h2>
          <p className="text-base leading-relaxed" style={{ color: 'var(--text-2)' }}>
            A transaction hash proves money moved. It says nothing about who sent it,
            why, or whether the recipient is sanctioned. That gap is what gets you stuck
            at accounting close, bank review, or fundraising diligence.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-3">
          <div className="rounded-2xl p-6" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            <div className="text-xs font-medium uppercase tracking-wider mb-4" style={{ color: 'var(--text-3)' }}>
              What your accountant gets today
            </div>
            <div className="font-mono text-sm leading-8 break-all" style={{ color: 'var(--hash-dim)' }}>
              0x5d3a1Bf4A11E5c8e9fC2b7d...
              <br />
              0x8f9e2Cc7B23A6d1f04a8e7c...
              <br />
              0x1a2b3c4d5e6f7a8b9c0d1e2...
            </div>
            <p className="text-xs mt-4" style={{ color: 'var(--text-4)' }}>
              Three transfers. No idea who, why, or whether they were compliant.
            </p>
          </div>

          <div className="rounded-2xl p-6" style={{ backgroundColor: 'var(--bg-accent)', border: '1px solid var(--border-accent)' }}>
            <div className="text-xs font-medium uppercase tracking-wider mb-4" style={{ color: 'var(--text-2)' }}>
              What Radius gives them
            </div>
            <div className="font-mono text-xs leading-7">
              <span style={{ color: 'var(--code-punc)' }}>{'{'}</span>
              <br />
              <span className="pl-4" style={{ color: 'var(--code-prop)' }}>entity</span>
              <span style={{ color: 'var(--code-punc)' }}>: </span>
              <span style={{ color: 'var(--text-1)' }}>"Acme Inc → Alice Smith"</span>
              <br />
              <span className="pl-4" style={{ color: 'var(--code-prop)' }}>amount</span>
              <span style={{ color: 'var(--code-punc)' }}>: </span>
              <span style={{ color: 'var(--text-1)' }}>"$2,500 USDC"</span>
              <br />
              <span className="pl-4" style={{ color: 'var(--code-prop)' }}>purpose</span>
              <span style={{ color: 'var(--code-punc)' }}>: </span>
              <span style={{ color: 'var(--text-1)' }}>"contractor_payout"</span>
              <br />
              <span className="pl-4" style={{ color: 'var(--code-prop)' }}>sanctions</span>
              <span style={{ color: 'var(--code-punc)' }}>: </span>
              <span style={{ color: 'var(--green)' }}>"clear"</span>
              <br />
              <span className="pl-4" style={{ color: 'var(--code-prop)' }}>jurisdiction</span>
              <span style={{ color: 'var(--code-punc)' }}>: </span>
              <span style={{ color: 'var(--text-1)' }}>"US → DE"</span>
              <br />
              <span style={{ color: 'var(--code-punc)' }}>{'}'}</span>
            </div>
            <p className="text-xs mt-4" style={{ color: 'var(--text-3)' }}>Same transfer. Now it's a financial record.</p>
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
    <section id="how-it-works" className="py-24 px-6" style={{ borderTop: '1px solid var(--border)' }}>
      <div className="max-w-5xl mx-auto">
        <div className="max-w-2xl mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4 leading-tight" style={{ color: 'var(--text-1)' }}>
            Three API calls. Full audit trail.
          </h2>
          <p className="text-base leading-relaxed" style={{ color: 'var(--text-2)' }}>
            Radius sits between your payment logic and the blockchain. You don't
            change how you send. You just check first.
          </p>
        </div>

        <div className="space-y-3">
          {steps.map((s) => (
            <div
              key={s.n}
              className="rounded-2xl p-7 flex flex-col sm:flex-row sm:items-start gap-5"
              style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)' }}
            >
              <div className="font-mono text-3xl font-bold select-none flex-shrink-0 leading-none" style={{ color: 'var(--text-5)' }}>
                {s.n}
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-3 mb-3">
                  <h3 className="text-base font-semibold" style={{ color: 'var(--text-1)' }}>{s.title}</h3>
                  <span
                    className="font-mono text-xs px-3 py-1 rounded-full"
                    style={{ color: 'var(--text-3)', backgroundColor: 'var(--bg)', border: '1px solid var(--border)' }}
                  >
                    {s.endpoint}
                  </span>
                </div>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-3)' }}>{s.body}</p>
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
    <section id="features" className="py-24 px-6" style={{ borderTop: '1px solid var(--border)' }}>
      <div className="max-w-5xl mx-auto">
        <div className="max-w-2xl mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4 leading-tight" style={{ color: 'var(--text-1)' }}>
            What you get
          </h2>
          <p className="text-base leading-relaxed" style={{ color: 'var(--text-2)' }}>
            Sanctions screening, Travel Rule automation, and audit-ready records in a
            single API. No enterprise sales calls. No 6-month integrations.
          </p>
        </div>

        <div className="grid sm:grid-cols-3 gap-3">
          {features.map((f) => (
            <div
              key={f.title}
              className="rounded-2xl p-7"
              style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)' }}
            >
              <h3 className="text-base font-semibold mb-3" style={{ color: 'var(--text-1)' }}>{f.title}</h3>
              <p className="text-sm leading-relaxed mb-5" style={{ color: 'var(--text-3)' }}>{f.body}</p>
              <ul className="space-y-2">
                {f.items.map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm" style={{ color: 'var(--text-3)' }}>
                    <span className="mt-px flex-shrink-0" style={{ color: 'var(--text-4)' }}>-</span>
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

// ─── SDKs ───────────────────────────────────────────────────────────────────

function SDKs() {
  return (
    <section id="sdks" className="py-24 px-6" style={{ borderTop: '1px solid var(--border)' }}>
      <div className="max-w-5xl mx-auto">
        <div className="max-w-2xl mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4 leading-tight" style={{ color: 'var(--text-1)' }}>
            Install and ship in minutes
          </h2>
          <p className="text-base leading-relaxed" style={{ color: 'var(--text-2)' }}>
            Native SDKs for Python and TypeScript. Install, configure, and start screening transactions.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            className="rounded-2xl overflow-hidden text-left"
            style={{ backgroundColor: 'var(--bg-code)', border: '1px solid var(--border)' }}
          >
            <div
              className="flex items-center gap-1.5 px-4 py-3"
              style={{ borderBottom: '1px solid var(--border)' }}
            >
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--dot)' }} />
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--dot)' }} />
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--dot)' }} />
              <span className="ml-3 text-xs font-mono" style={{ color: 'var(--text-4)' }}>Python</span>
            </div>
            <div className="p-5 font-mono text-[13px] leading-7 overflow-x-auto">
              <div style={{ color: 'var(--code-cmt)' }}># pip install getradius</div>
              <div>&nbsp;</div>
              <div>
                <span style={{ color: 'var(--code-kw)' }}>from </span>
                <span style={{ color: 'var(--text-1)' }}>radius </span>
                <span style={{ color: 'var(--code-kw)' }}>import </span>
                <span style={{ color: 'var(--text-1)' }}>Radius</span>
              </div>
              <div>&nbsp;</div>
              <div>
                <span style={{ color: 'var(--text-1)' }}>client</span>
                <span style={{ color: 'var(--code-punc)' }}> = </span>
                <span style={{ color: 'var(--text-1)' }}>Radius</span>
                <span style={{ color: 'var(--code-punc)' }}>(</span>
                <span style={{ color: 'var(--code-prop)' }}>api_key</span>
                <span style={{ color: 'var(--code-punc)' }}>=</span>
                <span style={{ color: 'var(--code-str)' }}>"sk_sandbox_..."</span>
                <span style={{ color: 'var(--code-punc)' }}>)</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-1)' }}>result</span>
                <span style={{ color: 'var(--code-punc)' }}> = </span>
                <span style={{ color: 'var(--text-1)' }}>client</span>
                <span style={{ color: 'var(--code-punc)' }}>.</span>
                <span style={{ color: 'var(--text-1)' }}>transactions</span>
                <span style={{ color: 'var(--code-punc)' }}>.</span>
                <span style={{ color: 'var(--text-1)' }}>check</span>
                <span style={{ color: 'var(--code-punc)' }}>(</span>
              </div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>sender</span>
                <span style={{ color: 'var(--code-punc)' }}>=</span>
                <span style={{ color: 'var(--code-str)' }}>"0x742d..."</span>
                <span style={{ color: 'var(--code-punc)' }}>,</span>
              </div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>receiver</span>
                <span style={{ color: 'var(--code-punc)' }}>=</span>
                <span style={{ color: 'var(--code-str)' }}>"0x3fC9..."</span>
                <span style={{ color: 'var(--code-punc)' }}>,</span>
              </div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>amount</span>
                <span style={{ color: 'var(--code-punc)' }}>=</span>
                <span style={{ color: 'var(--code-str)' }}>"2500.00"</span>
              </div>
              <div><span style={{ color: 'var(--code-punc)' }}>)</span></div>
            </div>
          </div>

          <div
            className="rounded-2xl overflow-hidden text-left"
            style={{ backgroundColor: 'var(--bg-code)', border: '1px solid var(--border)' }}
          >
            <div
              className="flex items-center gap-1.5 px-4 py-3"
              style={{ borderBottom: '1px solid var(--border)' }}
            >
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--dot)' }} />
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--dot)' }} />
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--dot)' }} />
              <span className="ml-3 text-xs font-mono" style={{ color: 'var(--text-4)' }}>TypeScript</span>
            </div>
            <div className="p-5 font-mono text-[13px] leading-7 overflow-x-auto">
              <div style={{ color: 'var(--code-cmt)' }}>// npm install @getradius/sdk</div>
              <div>&nbsp;</div>
              <div>
                <span style={{ color: 'var(--code-kw)' }}>import </span>
                <span style={{ color: 'var(--code-punc)' }}>{'{ '}</span>
                <span style={{ color: 'var(--text-1)' }}>Radius</span>
                <span style={{ color: 'var(--code-punc)' }}>{' }'}</span>
                <span style={{ color: 'var(--code-kw)' }}> from </span>
                <span style={{ color: 'var(--code-str)' }}>"@getradius/sdk"</span>
              </div>
              <div>&nbsp;</div>
              <div>
                <span style={{ color: 'var(--code-kw)' }}>const </span>
                <span style={{ color: 'var(--text-1)' }}>radius</span>
                <span style={{ color: 'var(--code-punc)' }}> = </span>
                <span style={{ color: 'var(--code-kw)' }}>new </span>
                <span style={{ color: 'var(--text-1)' }}>Radius</span>
                <span style={{ color: 'var(--code-punc)' }}>(</span>
                <span style={{ color: 'var(--code-str)' }}>"sk_sandbox_..."</span>
                <span style={{ color: 'var(--code-punc)' }}>)</span>
              </div>
              <div>
                <span style={{ color: 'var(--code-kw)' }}>const </span>
                <span style={{ color: 'var(--text-1)' }}>result</span>
                <span style={{ color: 'var(--code-punc)' }}> = </span>
                <span style={{ color: 'var(--code-kw)' }}>await </span>
                <span style={{ color: 'var(--text-1)' }}>radius</span>
                <span style={{ color: 'var(--code-punc)' }}>.</span>
                <span style={{ color: 'var(--text-1)' }}>transactions</span>
                <span style={{ color: 'var(--code-punc)' }}>.</span>
                <span style={{ color: 'var(--text-1)' }}>check</span>
                <span style={{ color: 'var(--code-punc)' }}>(</span>
                <span style={{ color: 'var(--code-punc)' }}>{'{'}</span>
              </div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>sender</span>
                <span style={{ color: 'var(--code-punc)' }}>: </span>
                <span style={{ color: 'var(--code-str)' }}>"0x742d..."</span>
                <span style={{ color: 'var(--code-punc)' }}>,</span>
              </div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>receiver</span>
                <span style={{ color: 'var(--code-punc)' }}>: </span>
                <span style={{ color: 'var(--code-str)' }}>"0x3fC9..."</span>
                <span style={{ color: 'var(--code-punc)' }}>,</span>
              </div>
              <div className="pl-5">
                <span style={{ color: 'var(--code-prop)' }}>amount</span>
                <span style={{ color: 'var(--code-punc)' }}>: </span>
                <span style={{ color: 'var(--code-str)' }}>"2500.00"</span>
              </div>
              <div>
                <span style={{ color: 'var(--code-punc)' }}>{'}'}</span>
                <span style={{ color: 'var(--code-punc)' }}>)</span>
              </div>
            </div>
          </div>
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
    <section id="pricing" className="py-24 px-6" style={{ borderTop: '1px solid var(--border)' }}>
      <div className="max-w-5xl mx-auto">
        <div className="max-w-2xl mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4 leading-tight" style={{ color: 'var(--text-1)' }}>
            Pricing
          </h2>
          <p className="text-base leading-relaxed" style={{ color: 'var(--text-2)' }}>
            Usage-based. No seat licenses. No annual commitments on Starter or Growth.
          </p>
        </div>

        <div className="grid sm:grid-cols-3 gap-3">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className="flex flex-col rounded-2xl"
              style={{
                backgroundColor: plan.highlighted ? 'var(--bg-accent)' : 'var(--bg-card)',
                border: `1px solid ${plan.highlighted ? 'var(--border-accent)' : 'var(--border)'}`,
              }}
            >
              <div className="p-6 flex-1">
                <div className="text-sm font-medium mb-4" style={{ color: 'var(--text-3)' }}>{plan.name}</div>
                <div className="mb-1">
                  <span className="text-3xl font-bold" style={{ color: 'var(--text-1)' }}>{plan.price}</span>
                  {plan.period && (
                    <span className="text-sm" style={{ color: 'var(--text-4)' }}>{plan.period}</span>
                  )}
                </div>
                {plan.usage ? (
                  <div className="text-xs mb-5" style={{ color: 'var(--text-4)' }}>{plan.usage}</div>
                ) : (
                  <div className="mb-5" />
                )}
                <p className="text-sm mb-6 leading-relaxed" style={{ color: 'var(--text-3)' }}>{plan.description}</p>
                <ul className="space-y-2.5">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-sm" style={{ color: 'var(--text-3)' }}>
                      <span className="mt-px flex-shrink-0" style={{ color: 'var(--text-4)' }}>-</span>
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="px-6 pb-6">
                <a
                  href="#waitlist"
                  className="block text-center py-2.5 rounded-xl text-sm font-medium transition-colors"
                  style={
                    plan.highlighted
                      ? { backgroundColor: 'var(--btn-bg)', color: 'var(--btn-text)' }
                      : { border: '1px solid var(--outline-border)', color: 'var(--outline-text)' }
                  }
                >
                  Get started
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
    <section className="py-24 px-6" style={{ borderTop: '1px solid var(--border)' }}>
      <div className="max-w-5xl mx-auto">
        <div
          className="rounded-3xl p-12 md:p-20 text-center"
          style={{ backgroundColor: 'var(--bg-accent)', border: '1px solid var(--border-accent)' }}
        >
          <h2
            className="text-3xl sm:text-4xl md:text-5xl font-bold mb-5 leading-tight"
            style={{ color: 'var(--text-1)' }}
          >
            Start building
          </h2>
          <p className="text-base mb-8 max-w-md mx-auto leading-relaxed" style={{ color: 'var(--text-2)' }}>
            Get your API key and start screening transactions in minutes. Free sandbox included.
          </p>
          <SignupForm center />
        </div>
      </div>
    </section>
  )
}

// ─── Footer ──────────────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer className="py-12 px-6" style={{ borderTop: '1px solid var(--border)' }}>
      <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: 'var(--accent)' }} />
            <span className="font-semibold text-sm" style={{ color: 'var(--text-1)' }}>Radius</span>
          </div>
          <p className="text-xs leading-relaxed" style={{ color: 'var(--text-4)' }}>
            Payment attestation infrastructure<br />for stablecoin transfers.
          </p>
        </div>
        <div className="flex items-center gap-6 text-sm" style={{ color: 'var(--text-3)' }}>
          <a href="#how-it-works" className="hover:opacity-70 transition-opacity">How it works</a>
          <a href="#pricing" className="hover:opacity-70 transition-opacity">Pricing</a>
          <a href="/docs" className="hover:opacity-70 transition-opacity">Docs</a>
          <a href="mailto:hello@getradius.com" className="hover:opacity-70 transition-opacity">Contact</a>
        </div>
      </div>
      <div className="max-w-5xl mx-auto mt-8 pt-6" style={{ borderTop: '1px solid var(--border)' }}>
        <p className="text-xs" style={{ color: 'var(--text-5)' }}>&copy; 2026 Radius.</p>
      </div>
    </footer>
  )
}

// ─── App ─────────────────────────────────────────────────────────────────────

export default function App() {
  const [dark, toggleTheme] = useTheme()

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg)', color: 'var(--text-1)' }}>
      <Nav dark={dark} toggleTheme={toggleTheme} />
      <main>
        <Hero />
        <Stats />
        <BeforeAfter />
        <HowItWorks />
        <Features />
        <SDKs />
        <Pricing />
        <CTA />
      </main>
      <Footer />
    </div>
  )
}
