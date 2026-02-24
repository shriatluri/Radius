# Radius Dashboard - Frontend

A modern, React-based compliance dashboard for the Radius platform.

## Tech Stack

- **React 18** - UI library
- **Vite 6** - Build tool and dev server
- **Tailwind CSS 3** - Utility-first styling
- **FastAPI** - Backend API (served from `/v1/*`)

## Development

### Prerequisites

- Node.js 18+ and npm
- Running Radius API backend on port 8000

### Installation

```bash
npm install
```

### Development Server

Start the Vite dev server with hot reload:

```bash
npm run dev
```

This will start the frontend on **http://localhost:5173**

The dev server automatically proxies API requests from `/v1/*` to `http://localhost:8000`, so you don't need to worry about CORS during development.

### Development Workflow

1. Start the Radius API backend:
   ```bash
   cd ..
   uvicorn app.main:app --reload --port 8000
   ```

2. In a separate terminal, start the frontend dev server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open http://localhost:5173 in your browser

4. Use the demo API key: `sk_test_acme_123456`

### Building for Production

Build the frontend and output to `../app/static`:

```bash
npm run build
```

This compiles and minifies the React app into static files that FastAPI can serve.

### Preview Production Build

Preview the production build locally:

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ApiKeyInput.jsx  # Authentication gate
│   │   ├── Filters.jsx      # Filter controls
│   │   ├── StatsBar.jsx     # Summary statistics
│   │   ├── TransactionList.jsx      # Transaction table
│   │   └── TransactionDetail.jsx    # Audit record modal
│   ├── lib/
│   │   └── api.js          # API client
│   ├── App.jsx             # Main application
│   ├── main.jsx            # React entry point
│   └── index.css           # Global styles (Tailwind)
├── index.html              # HTML template
├── vite.config.js          # Vite configuration
├── tailwind.config.js      # Tailwind configuration
└── package.json            # Dependencies
```

## Features

### Authentication
- API key stored in localStorage
- Simple login/logout flow
- Automatic re-authentication on 401/403

### Transaction List
- Paginated table view
- Color-coded status badges (pending/approved/blocked)
- Color-coded risk levels (low/medium/high/critical)
- Click any row to view full audit record

### Filtering
- Filter by status (pending, approved, blocked)
- Filter by risk level (low, medium, high, critical)
- Filter by business ID (text search)

### Export
- Export filtered transactions to CSV
- Automatic file download with timestamp

### Audit Records
- Full transaction details in modal
- Structured sections: Basic Info, Entities, Compliance, Blockchain
- Conditional rendering (only shows fields that exist)

## API Client

The API client (`src/lib/api.js`) provides:

- `setApiKey(key)` - Store API key
- `getApiKey()` - Retrieve stored key
- `clearApiKey()` - Remove stored key
- `listTransactions(filters)` - Fetch transactions
- `getAuditRecord(id)` - Fetch audit record
- `exportData(format, filters)` - Export data
- `downloadCsv(filters)` - Download CSV

## Configuration

### Vite Config (`vite.config.js`)

- **Build output**: `../app/static` (served by FastAPI)
- **Dev proxy**: `/v1` → `http://localhost:8000`
- **Hot reload**: Enabled by default

### Tailwind Config (`tailwind.config.js`)

- **Content sources**: `index.html`, `src/**/*.{js,jsx}`
- **Default theme**: Extended as needed
- **Plugins**: None (can add as needed)

## Troubleshooting

### CORS Errors in Development

If you see CORS errors, ensure:
1. FastAPI backend is running on port 8000
2. Vite dev server is running on port 5173
3. The proxy is configured in `vite.config.js`

### API Key Not Persisting

The API key is stored in `localStorage`. If it's not persisting:
- Check browser console for localStorage errors
- Ensure you're not in incognito/private mode
- Try clearing localStorage: `localStorage.removeItem('radius_api_key')`

### Build Errors

If `npm run build` fails:
1. Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
2. Clear Vite cache: `rm -rf .vite`
3. Check for TypeScript errors (we're using plain JS, so shouldn't happen)

### Static Files Not Served

If the production build doesn't load:
1. Verify files exist in `../app/static/`
2. Restart FastAPI server to pick up the static files mount
3. Check FastAPI logs for mounting errors

## Production Deployment

When deploying to production:

1. Build the frontend:
   ```bash
   npm run build
   ```

2. Verify `app/static/` contains the built files

3. Deploy the entire project (including `app/static/`) to your server

4. Start FastAPI:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

5. Access the dashboard at `http://your-server:8000`

The FastAPI server will automatically serve the static frontend at `/` and API routes at `/v1/*`.

## Future Enhancements

Out of scope for MVP but planned:
- Pagination controls (prev/next buttons)
- Date range picker (calendar widget)
- Free-text search
- Column sorting
- Charts and graphs
- Real-time updates (WebSocket)
- Dark mode
- Proper authentication (login flow, sessions)
- User preferences and saved filters
