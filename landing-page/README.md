# Radius Landing Page

**Live site:** [getradius.vercel.app](https://getradius.vercel.app)

Marketing site for [Radius](https://github.com/shriatluri/Radius) — payment attestation infrastructure for stablecoin transfers.

Built with React, Vite, and Tailwind CSS.

## Prerequisites

- [Node.js](https://nodejs.org/) v18 or higher
- npm (comes with Node)

## Getting started

**1. Clone the repo**

```bash
git clone https://github.com/shriatluri/Radius.git
cd Radius/landing-page
```

**2. Install dependencies**

```bash
npm install
```

**3. Start the dev server**

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

## Other commands

| Command | Description |
|---|---|
| `npm run dev` | Start local dev server with hot reload |
| `npm run build` | Build for production (outputs to `dist/`) |
| `npm run preview` | Preview the production build locally |

## Project structure

```
landing-page/
├── index.html          # HTML entry point
├── vite.config.js      # Vite config
├── tailwind.config.js  # Tailwind config
├── postcss.config.js   # PostCSS config
├── package.json
└── src/
    ├── main.jsx        # React entry point
    ├── App.jsx         # Full page — all sections live here
    └── index.css       # Tailwind directives + base styles
```

## Tech stack

- [React 18](https://react.dev/)
- [Vite](https://vitejs.dev/)
- [Tailwind CSS v3](https://tailwindcss.com/)
