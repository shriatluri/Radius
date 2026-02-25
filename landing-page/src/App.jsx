import { useState } from 'react'

// ─── Icons ────────────────────────────────────────────────────────────────────

const Check = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
  </svg>
)

const X = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
  </svg>
)

// ─── Navbar ───────────────────────────────────────────────────────────────────

function Navbar() {
  const [open, setOpen] = useState(false)

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[#1a1a1a] bg-black/90 backdrop-blur-md">
      <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-full bg-[#6b21a8]" />
          <span className="font-semibold text-white text-sm tracking-tight">Radius</span>
        </div>

        <div className="hidden md:flex items-center gap-8 text-sm text-[#666]">
          <a href="#how-it-works" className="hover:text-white transition-colors">How it works</a>
          <a href="#features"     className="hover:text-white transition-colors">Features</a>
          <a href="#compare"      className="hover:text-white transition-colors">Compare</a>
          <a href="#pricing"      className="hover:text-white transition-colors">Pricing</a>
          <a href="#"             className="hover:text-white transition-colors">Docs</a>
        </div>

        <div className="hidden md:flex items-center gap-4">
          <a href="#" className="text-sm text-[#666] hover:text-white transition-colors">Sign in</a>
          <a href="#" className="text-sm bg-white text-black px-4 py-1.5 rounded-lg font-semibold hover:bg-[#e5e5e5] transition-colors">
            Get API Key
          </a>
        </div>

        <button onClick={() => setOpen(!open)} className="md:hidden text-[#666] hover:text-white p-1">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            {open
              ? <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              : <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />}
          </svg>
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-[#1a1a1a] bg-black px-6 py-5 flex flex-col gap-4 text-sm text-[#666]">
          <a href="#how-it-works" onClick={() => setOpen(false)} className="hover:text-white">How it works</a>
          <a href="#features"     onClick={() => setOpen(false)} className="hover:text-white">Features</a>
          <a href="#compare"      onClick={() => setOpen(false)} className="hover:text-white">Compare</a>
          <a href="#pricing"      onClick={() => setOpen(false)} className="hover:text-white">Pricing</a>
          <a href="#"             className="hover:text-white">Docs</a>
          <div className="pt-3 border-t border-[#1a1a1a] flex flex-col gap-3">
            <a href="#" className="hover:text-white">Sign in</a>
            <a href="#" className="bg-white text-black px-4 py-2 rounded-lg font-semibold text-center">Get API Key</a>
          </div>
        </div>
      )}
    </nav>
  )
}

// ─── Hero ─────────────────────────────────────────────────────────────────────

function RadarBackground() {
  const rings = [100, 200, 300, 400, 500]
  const size = 560

  return (
    <div
      className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden"
      style={{ opacity: 0.09 }}
    >
      <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
        {/* Concentric rings */}
        {rings.map((d) => (
          <div
            key={d}
            className="absolute rounded-full border border-white"
            style={{
              width: d,
              height: d,
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
            }}
          />
        ))}

        {/* Crosshairs */}
        <div className="absolute bg-white" style={{ width: '100%', height: 1, top: '50%', left: 0 }} />
        <div className="absolute bg-white" style={{ width: 1, height: '100%', left: '50%', top: 0 }} />

        {/* Center dot */}
        <div
          className="absolute rounded-full bg-white"
          style={{ width: 5, height: 5, top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}
        />

        {/* Rotating sweep */}
        <div
          className="radar-sweep absolute inset-0 rounded-full"
          style={{
            background: `conic-gradient(
              from 0deg,
              transparent 0deg,
              rgba(255,255,255,0.03) 20deg,
              rgba(255,255,255,0.08) 45deg,
              rgba(255,255,255,0.25) 59deg,
              rgba(255,255,255,0.6) 60deg,
              transparent 61deg,
              transparent 360deg
            )`,
          }}
        />
      </div>
    </div>
  )
}

function Hero() {
  return (
    <section className="relative pt-32 pb-24 px-6 overflow-hidden">
      <RadarBackground />
      <div className="relative z-10 max-w-5xl mx-auto flex flex-col items-center text-center">
        <div className="inline-flex items-center gap-2 border border-[#2a1045] bg-[#0f0020] text-[#a78bfa] text-xs font-medium px-3 py-1.5 rounded-full mb-10">
          <span className="w-1.5 h-1.5 rounded-full bg-[#7c3aed]" />
          GENIUS Act · FATF Travel Rule · OFAC
        </div>

        <h1 className="text-5xl sm:text-6xl md:text-[72px] font-bold text-white leading-[1.05] tracking-tight mb-7 max-w-4xl">
          The paper trail your
          <br className="hidden sm:block" />
          blockchain never had.
        </h1>

        <p className="text-lg text-[#777] max-w-xl leading-relaxed mb-10">
          Radius turns every stablecoin transaction into a structured financial record.
          Real OFAC screening, Travel Rule automation, and immutable audit trails — one API call.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 mb-16">
          <a href="#" className="bg-white text-black px-7 py-3 rounded-xl font-semibold text-sm hover:bg-[#e5e5e5] transition-colors">
            Get API Key — Free
          </a>
          <a href="#how-it-works" className="border border-[#222] text-[#999] px-7 py-3 rounded-xl font-semibold text-sm hover:border-[#444] hover:text-white transition-colors">
            See how it works →
          </a>
        </div>

        {/* Code blocks — side by side */}
        <div className="w-full max-w-4xl grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Request */}
          <div className="border border-[#1c1c1c] rounded-2xl overflow-hidden bg-[#080808] text-left">
            <div className="flex items-center gap-1.5 px-4 py-3 border-b border-[#1a1a1a]">
              <div className="w-2.5 h-2.5 rounded-full bg-[#222]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#222]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#222]" />
              <span className="ml-3 text-xs text-[#444] font-mono">request</span>
            </div>
            <div className="p-5 font-mono text-[13px] leading-7 overflow-x-auto">
              <div className="text-[#444]">// Attest before sending</div>
              <div>
                <span className="text-[#7c9cbf]">const </span>
                <span className="text-white">record </span>
                <span className="text-[#555]">= </span>
                <span className="text-[#7c9cbf]">await </span>
                <span className="text-white">radius</span>
                <span className="text-[#555]">.</span>
                <span className="text-[#c084fc]">attest</span>
                <span className="text-[#555]">({'{'}</span>
              </div>
              <div className="pl-5">
                <span className="text-[#e5c07b]">from</span>
                <span className="text-[#555]">: </span>
                <span className="text-[#98c379]">"0x742d35Cc..."</span>
                <span className="text-[#555]">,</span>
              </div>
              <div className="pl-5">
                <span className="text-[#e5c07b]">to</span>
                <span className="text-[#555]">: </span>
                <span className="text-[#98c379]">"0x3fC91A3a..."</span>
                <span className="text-[#555]">,</span>
              </div>
              <div className="pl-5">
                <span className="text-[#e5c07b]">amount</span>
                <span className="text-[#555]">: </span>
                <span className="text-[#98c379]">"2500.00"</span>
                <span className="text-[#555]">,</span>
              </div>
              <div className="pl-5">
                <span className="text-[#e5c07b]">asset</span>
                <span className="text-[#555]">: </span>
                <span className="text-[#98c379]">"USDC"</span>
                <span className="text-[#555]">,</span>
              </div>
              <div className="pl-5">
                <span className="text-[#e5c07b]">purpose</span>
                <span className="text-[#555]">: </span>
                <span className="text-[#98c379]">"contractor_payout"</span>
              </div>
              <div><span className="text-[#555]">{'}'});</span></div>
            </div>
          </div>

          {/* Response */}
          <div className="border border-[#1c1c1c] rounded-2xl overflow-hidden bg-[#080808] text-left">
            <div className="flex items-center gap-1.5 px-4 py-3 border-b border-[#1a1a1a]">
              <div className="w-2.5 h-2.5 rounded-full bg-[#222]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#222]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[#222]" />
              <span className="ml-3 text-xs text-[#444] font-mono">response</span>
            </div>
            <div className="p-5 font-mono text-[13px] leading-7 overflow-x-auto">
              <div className="text-[#444]">// Returns in ~200ms</div>
              <div className="text-[#555]">{'{'}</div>
              <div className="pl-5"><span className="text-[#e5c07b]">risk_level</span><span className="text-[#555]">: </span><span className="text-[#98c379]">"low"</span><span className="text-[#555]">,</span></div>
              <div className="pl-5"><span className="text-[#e5c07b]">sanctions_result</span><span className="text-[#555]">: </span><span className="text-[#98c379]">"passed"</span><span className="text-[#555]">,</span></div>
              <div className="pl-5"><span className="text-[#e5c07b]">travel_rule</span><span className="text-[#555]">: </span><span className="text-[#7c9cbf]">false</span><span className="text-[#555]">,</span></div>
              <div className="pl-5"><span className="text-[#e5c07b]">audit_id</span><span className="text-[#555]">: </span><span className="text-[#98c379]">"txn_01HX8KmR9..."</span></div>
              <div className="text-[#555]">{'}'}</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

// ─── Stats ────────────────────────────────────────────────────────────────────

function Stats() {
  const items = [
    { value: '$33T',  label: 'stablecoin volume in 2025' },
    { value: '30+',   label: 'jurisdictions covered' },
    { value: '~200ms', label: 'median check latency' },
    { value: '10×',   label: 'cheaper than Chainalysis' },
  ]
  return (
    <div className="border-y border-[#111]">
      <div className="max-w-5xl mx-auto px-6 py-10 grid grid-cols-2 md:grid-cols-4 gap-8">
        {items.map(s => (
          <div key={s.value}>
            <div className="text-3xl font-bold text-white mb-1">{s.value}</div>
            <div className="text-sm text-[#555]">{s.label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Problem ──────────────────────────────────────────────────────────────────

function Problem() {
  const triggers = [
    { icon: '📊', event: 'Accounting close',      pain: 'CFO can\'t reconcile stablecoin payments to business purpose. Books don\'t close.',    cost: 'Audit delayed' },
    { icon: '🏦', event: 'Bank review',            pain: 'Bank requests source-of-funds documentation you can\'t produce.',                       cost: 'Account frozen' },
    { icon: '💼', event: 'Fundraising diligence',  pain: 'Investors ask for proof of payment controls. Your answer is blockchain hashes.',        cost: 'Deal slows or dies' },
    { icon: '🌍', event: 'International expansion', pain: 'New jurisdiction requires Travel Rule proof to operate legally.',                      cost: 'Can\'t launch' },
  ]

  return (
    <section className="py-28 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="mb-14">
          <div className="text-xs font-semibold uppercase tracking-widest text-[#7c3aed] mb-4">The problem</div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-5 leading-tight">
            Your payments are hashes.<br />Not records.
          </h2>
          <p className="text-[#666] text-lg max-w-xl leading-relaxed">
            Companies can send stablecoin payments. They can't explain them later.
            Every operational trigger turns that gap into a crisis.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-12">
          {triggers.map(t => (
            <div key={t.event} className="card p-5">
              <div className="text-2xl mb-4">{t.icon}</div>
              <div className="text-xs font-semibold text-[#555] uppercase tracking-wider mb-2">{t.event}</div>
              <p className="text-sm text-[#888] leading-relaxed mb-4">{t.pain}</p>
              <div className="text-xs font-medium text-[#ef4444] border border-[#2a1010] bg-[#120808] rounded-lg px-3 py-1.5">
                {t.cost}
              </div>
            </div>
          ))}
        </div>

        {/* Before / After */}
        <div className="grid md:grid-cols-2 gap-3">
          <div className="card p-6">
            <div className="text-xs font-semibold uppercase tracking-widest text-[#555] mb-4">Without Radius</div>
            <div className="font-mono text-sm text-[#444] bg-[#060606] border border-[#161616] rounded-xl p-4 leading-8 break-all">
              0x5d3a1Bf4A11E5c8e9f...
              <br />0x8f9e2Cc7B23A6d1f0...
              <br />0x1a2b3c4d5e6f7a8b...
            </div>
            <p className="text-xs text-[#444] mt-3">Raw blockchain hashes. Useless to an auditor.</p>
          </div>
          <div className="border border-[#2a1045] bg-[#0a0015] rounded-2xl p-6">
            <div className="text-xs font-semibold uppercase tracking-widest text-[#7c3aed] mb-4">With Radius</div>
            <div className="font-mono text-xs text-[#666] bg-[#060606] border border-[#1a1a1a] rounded-xl p-4 leading-7">
              <span className="text-[#444]">{'{'}</span><br />
              <span className="pl-4 text-[#e5c07b]">entity</span><span className="text-[#444]">: </span><span className="text-[#aaa]">"Acme Inc → Alice Smith"</span><br />
              <span className="pl-4 text-[#e5c07b]">amount</span><span className="text-[#444]">: </span><span className="text-[#aaa]">"$2,500 USDC"</span><br />
              <span className="pl-4 text-[#e5c07b]">purpose</span><span className="text-[#444]">: </span><span className="text-[#aaa]">"contractor_payout"</span><br />
              <span className="pl-4 text-[#e5c07b]">sanctions</span><span className="text-[#444]">: </span><span className="text-[#4ade80]">"passed ✓"</span><br />
              <span className="text-[#444]">{'}'}</span>
            </div>
            <p className="text-xs text-[#555] mt-3">Structured financial record. Regulator-ready.</p>
          </div>
        </div>
      </div>
    </section>
  )
}

// ─── How It Works ─────────────────────────────────────────────────────────────

function HowItWorks() {
  const steps = [
    {
      n: '01',
      title: 'Attest before sending',
      body: 'One API call screens the counterparty against OFAC/EU/UN lists, scores risk 0–100, detects Travel Rule obligations, and creates a compliance record.',
      endpoint: 'POST /v1/transactions/ingest',
    },
    {
      n: '02',
      title: 'Annotate the on-chain hash',
      body: 'After the transaction broadcasts, attach the tx hash to close the loop between your compliance record and the on-chain event.',
      endpoint: 'POST /v1/payments/annotate',
    },
    {
      n: '03',
      title: 'Export audit records',
      body: 'Pull complete structured records any time — for your accountant, your bank, an investor, or a regulator. Every field named, signed, and exportable.',
      endpoint: 'GET /v1/transactions/:id/audit',
    },
  ]

  return (
    <section id="how-it-works" className="py-28 px-6 border-t border-[#111]">
      <div className="max-w-5xl mx-auto">
        <div className="mb-14">
          <div className="text-xs font-semibold uppercase tracking-widest text-[#7c3aed] mb-4">How it works</div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-5 leading-tight">
            Three calls.<br />Complete audit trail.
          </h2>
          <p className="text-[#666] text-lg max-w-xl leading-relaxed">
            Radius sits between your payment logic and the blockchain. One integration covers everything.
          </p>
        </div>

        <div className="space-y-3">
          {steps.map((s, i) => (
            <div key={s.n} className="card p-7 flex flex-col sm:flex-row sm:items-start gap-6">
              <div className="font-mono text-4xl font-bold text-[#1c1c1c] select-none flex-shrink-0 leading-none">
                {s.n}
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-3 mb-3">
                  <h3 className="text-lg font-semibold text-white">{s.title}</h3>
                  <span className="font-mono text-xs text-[#555] border border-[#1c1c1c] bg-[#0a0a0a] px-3 py-1 rounded-full">
                    {s.endpoint}
                  </span>
                </div>
                <p className="text-[#666] text-sm leading-relaxed">{s.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── Features ─────────────────────────────────────────────────────────────────

function Features() {
  const features = [
    {
      title: 'OFAC & Sanctions Screening',
      body: 'Real-time screening against OFAC SDN, EU, and UN lists. Risk scores 0–100. Block or flag transactions automatically.',
      items: ['OFAC SDN list (10,000+ entries)', 'EU & UN sanctions lists', 'Custom blocklist support', 'Pass/fail in ~200ms'],
    },
    {
      title: 'Travel Rule Automation',
      body: 'Automatically detect Travel Rule obligations by jurisdiction and collect the required counterparty data. FATF R.16 compliant.',
      items: ['Threshold detection per jurisdiction', 'Self-hosted wallet detection', '30+ jurisdictions', 'VASP network ready'],
    },
    {
      title: 'Wallet Identity Verification',
      body: 'Cryptographic proof of wallet control via signed message. Bind wallets to KYC\'d entities with risk-tier assignment.',
      items: ['Signed message verification', 'Entity binding', 'Risk tier assignment', '90-day expiry, auto-renewal'],
    },
    {
      title: 'Audit-Ready Export',
      body: 'Every transaction becomes a complete structured object — entity names, purpose, approvals, and on-chain hash in one record.',
      items: ['CSV & JSON export', 'Immutable audit trail', 'NetSuite / QuickBooks (roadmap)', 'Regulator-ready format'],
    },
  ]

  return (
    <section id="features" className="py-28 px-6 border-t border-[#111]">
      <div className="max-w-5xl mx-auto">
        <div className="mb-14">
          <div className="text-xs font-semibold uppercase tracking-widest text-[#7c3aed] mb-4">Features</div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-5 leading-tight">
            One integration.<br />Everything covered.
          </h2>
          <p className="text-[#666] text-lg max-w-xl leading-relaxed">
            Replaces a $500K enterprise compliance stack. No contract. No 6-month setup.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 gap-3">
          {features.map(f => (
            <div key={f.title} className="card p-7">
              <h3 className="text-base font-semibold text-white mb-3">{f.title}</h3>
              <p className="text-sm text-[#666] leading-relaxed mb-5">{f.body}</p>
              <ul className="space-y-2">
                {f.items.map(item => (
                  <li key={item} className="flex items-center gap-2.5 text-sm text-[#555]">
                    <Check className="w-3.5 h-3.5 flex-shrink-0 text-[#7c3aed]" />
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

// ─── Comparison ───────────────────────────────────────────────────────────────

function Comparison() {
  const cols = ['Radius', 'Chainalysis', 'TRM Labs', 'Notabene', 'DIY Build']
  const rows = [
    { feature: 'Sanctions screening',     values: [true,       true,  true,  false,   false] },
    { feature: 'Travel Rule automation',  values: [true,       false, false, true,    false] },
    { feature: 'Audit-ready records',     values: [true,       false, false, false,   false] },
    { feature: 'Self-serve signup',       values: [true,       false, false, false,   false] },
    { feature: 'Stablecoin-native',       values: [true,       false, false, false,   false] },
    { feature: 'Starting price',          values: ['$99/mo',   '$50K/yr', '$25K/yr', '$24K/yr', '$500K+'] },
    { feature: 'Setup time',              values: ['Hours',    '3–6 mo',  '3–6 mo',  '3–6 mo',  '12–18 mo'] },
  ]

  return (
    <section id="compare" className="py-28 px-6 border-t border-[#111]">
      <div className="max-w-5xl mx-auto">
        <div className="mb-14">
          <div className="text-xs font-semibold uppercase tracking-widest text-[#7c3aed] mb-4">Why Radius</div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-5 leading-tight">
            Built for SMBs.<br />Priced for startups.
          </h2>
          <p className="text-[#666] text-lg max-w-xl leading-relaxed">
            Enterprise tools start at $25K/year and require a sales call. Radius starts at $99/month and works in hours.
          </p>
        </div>

        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#1c1c1c]">
                <th className="text-left px-6 py-4 text-[#444] font-medium text-xs uppercase tracking-wider">Feature</th>
                {cols.map((c, i) => (
                  <th
                    key={c}
                    className={`px-4 py-4 text-center font-semibold text-sm ${
                      i === 0 ? 'text-white bg-[#0f0020] border-x border-[#2a1045]' : 'text-[#444]'
                    }`}
                  >
                    {c}
                    {i === 0 && (
                      <div className="text-[10px] font-medium text-[#7c3aed] mt-1">Best value</div>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, ri) => (
                <tr key={row.feature} className="border-b border-[#111] last:border-0">
                  <td className="px-6 py-3.5 text-[#666] text-sm">{row.feature}</td>
                  {row.values.map((val, ci) => (
                    <td
                      key={ci}
                      className={`px-4 py-3.5 text-center ${ci === 0 ? 'bg-[#0a0015] border-x border-[#1e0035]' : ''}`}
                    >
                      {typeof val === 'boolean' ? (
                        val
                          ? <Check className={`w-4 h-4 mx-auto ${ci === 0 ? 'text-[#a78bfa]' : 'text-[#333]'}`} />
                          : <X className="w-4 h-4 mx-auto text-[#222]" />
                      ) : (
                        <span className={`text-xs font-medium ${ci === 0 ? 'text-[#a78bfa]' : 'text-[#444]'}`}>
                          {val}
                        </span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

// ─── Pricing ──────────────────────────────────────────────────────────────────

function Pricing() {
  const plans = [
    {
      name: 'Free',
      price: '$0',
      sub: 'forever',
      desc: 'Full API access with mock data. No credit card.',
      cta: 'Get started',
      ctaCls: 'border border-[#222] text-white hover:border-[#444] transition-colors',
      features: ['100 checks / month', 'Mock sanctions data', 'Travel Rule detection', 'REST API access'],
    },
    {
      name: 'Starter',
      price: '$99',
      sub: '/mo + $0.10/check',
      desc: 'Real OFAC screening and audit records for seed-stage teams.',
      cta: 'Get Starter',
      ctaCls: 'border border-[#222] text-white hover:border-[#444] transition-colors',
      features: ['Real OFAC SDN screening', 'Travel Rule automation', 'Immutable audit records', 'CSV & JSON export', 'Email support'],
    },
    {
      name: 'Growth',
      price: '$499',
      sub: '/mo + $0.05/check',
      desc: 'Full compliance stack for Series A companies scaling volume.',
      cta: 'Get Growth',
      ctaCls: 'bg-white text-black hover:bg-[#e5e5e5] transition-colors',
      popular: true,
      features: ['Everything in Starter', 'EU & UN sanctions lists', 'Priority support (4h SLA)', 'Dedicated Slack channel', 'Volume discounts'],
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      sub: 'pricing',
      desc: 'Dedicated instance, SLA, SOC 2 report, custom integrations.',
      cta: 'Contact sales',
      ctaCls: 'border border-[#222] text-white hover:border-[#444] transition-colors',
      features: ['Everything in Growth', 'Dedicated infrastructure', 'SOC 2 Type II report', '99.9% uptime SLA', 'NetSuite / QuickBooks sync'],
    },
  ]

  return (
    <section id="pricing" className="py-28 px-6 border-t border-[#111]">
      <div className="max-w-5xl mx-auto">
        <div className="mb-14">
          <div className="text-xs font-semibold uppercase tracking-widest text-[#7c3aed] mb-4">Pricing</div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-5 leading-tight">
            Pay per check.<br />Not per seat.
          </h2>
          <p className="text-[#666] text-lg max-w-xl leading-relaxed">
            Transparent usage-based pricing. Start free, upgrade when you need real compliance.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {plans.map(plan => (
            <div
              key={plan.name}
              className={`flex flex-col rounded-2xl ${
                plan.popular
                  ? 'border border-[#2a1045] bg-[#0a0015]'
                  : 'card'
              }`}
            >
              <div className="p-6 flex-1">
                <div className="flex items-center justify-between mb-5">
                  <span className="text-sm font-semibold text-[#aaa]">{plan.name}</span>
                  {plan.popular && (
                    <span className="text-[10px] font-semibold text-[#a78bfa] border border-[#2a1045] bg-[#0f0020] rounded-full px-2 py-0.5">
                      Popular
                    </span>
                  )}
                </div>
                <div className="mb-4">
                  <span className="text-4xl font-bold text-white">{plan.price}</span>
                  <span className="text-sm text-[#444] ml-1">{plan.sub}</span>
                </div>
                <p className="text-sm text-[#555] mb-6 leading-relaxed">{plan.desc}</p>
                <ul className="space-y-2.5">
                  {plan.features.map(f => (
                    <li key={f} className="flex items-start gap-2.5 text-sm text-[#555]">
                      <Check className={`w-3.5 h-3.5 flex-shrink-0 mt-0.5 ${plan.popular ? 'text-[#7c3aed]' : 'text-[#333]'}`} />
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="px-6 pb-6">
                <a href="#" className={`block text-center py-2.5 rounded-xl font-semibold text-sm ${plan.ctaCls}`}>
                  {plan.cta}
                </a>
              </div>
            </div>
          ))}
        </div>
        <p className="text-center text-xs text-[#333] mt-8">
          14-day free trial on paid plans. No credit card required for Free tier.
        </p>
      </div>
    </section>
  )
}

// ─── Final CTA ────────────────────────────────────────────────────────────────

function FinalCTA() {
  return (
    <section className="py-28 px-6 border-t border-[#111]">
      <div className="max-w-5xl mx-auto">
        <div className="border border-[#2a1045] bg-[#070010] rounded-3xl p-12 md:p-20 text-center">
          <h2 className="text-4xl md:text-6xl font-bold text-white mb-6 leading-tight">
            Ship compliance<br />in hours, not months.
          </h2>
          <p className="text-[#666] text-lg mb-10 max-w-md mx-auto leading-relaxed">
            Start free. 100 checks a month, no credit card, full API access.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <a href="#" className="bg-white text-black px-8 py-3.5 rounded-xl font-semibold text-sm hover:bg-[#e5e5e5] transition-colors w-full sm:w-auto">
              Get API Key — Free →
            </a>
            <a href="#" className="border border-[#2a1045] text-[#888] px-8 py-3.5 rounded-xl font-semibold text-sm hover:border-[#4a2065] hover:text-white transition-colors w-full sm:w-auto">
              Read the docs
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}

// ─── Footer ───────────────────────────────────────────────────────────────────

function Footer() {
  const links = {
    Product:    ['Features', 'Pricing', 'Changelog', 'Status'],
    Developers: ['API Reference', 'SDKs', 'Quickstart', 'Postman Collection'],
    Company:    ['About', 'Blog', 'Careers', 'Contact'],
    Legal:      ['Privacy', 'Terms', 'Security', 'SOC 2'],
  }

  return (
    <footer className="border-t border-[#111] py-16 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-10 mb-12">
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-5 h-5 rounded-full bg-[#6b21a8]" />
              <span className="font-semibold text-white text-sm">Radius</span>
            </div>
            <p className="text-xs text-[#444] leading-relaxed">
              Payment attestation infrastructure for stablecoin transfers.
            </p>
          </div>
          {Object.entries(links).map(([group, items]) => (
            <div key={group}>
              <div className="text-xs font-semibold uppercase tracking-widest text-[#333] mb-4">{group}</div>
              <ul className="space-y-2.5">
                {items.map(item => (
                  <li key={item}>
                    <a href="#" className="text-sm text-[#444] hover:text-white transition-colors">{item}</a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="pt-8 border-t border-[#111] flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-[#333]">© 2025 Radius. All rights reserved.</p>
          <p className="text-xs text-[#333]">OFAC · FATF · MiCA · GENIUS Act</p>
        </div>
      </div>
    </footer>
  )
}

// ─── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <div className="min-h-screen bg-black text-white">
      <Navbar />
      <main>
        <Hero />
        <Stats />
        <Problem />
        <HowItWorks />
        <Features />
        <Comparison />
        <Pricing />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  )
}
