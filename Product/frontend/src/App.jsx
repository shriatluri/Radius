import { useState, useEffect } from 'react';
import { useUser, useAuth, SignedIn, SignedOut } from '@clerk/clerk-react';
import { api } from './lib/api';
import LoginPage from './components/LoginPage';
import StatsBar from './components/StatsBar';
import Filters from './components/Filters';
import TransactionList from './components/TransactionList';
import TransactionDetail from './components/TransactionDetail';
import KeyManagement from './components/KeyManagement';

function Dashboard() {
  const { user } = useUser();
  const { getToken, signOut } = useAuth();

  const [businessName, setBusinessName] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [filters, setFilters] = useState({
    status: null,
    risk_level: null,
    start_date: null,
    end_date: null,
    limit: 100,
  });
  const [selectedTxId, setSelectedTxId] = useState(null);
  const [auditRecord, setAuditRecord] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showKeys, setShowKeys] = useState(false);

  // Wire up the Clerk token getter for API calls
  useEffect(() => {
    api.setTokenGetter(getToken);
    return () => api.clearTokenGetter();
  }, [getToken]);

  // Fetch business name on mount
  useEffect(() => {
    const fetchMe = async () => {
      try {
        const data = await api.getMe();
        setBusinessName(data.business_name);
      } catch (err) {
        console.error('Failed to fetch user info:', err);
      }
    };
    fetchMe();
  }, []);

  // Fetch transactions when filters change
  useEffect(() => {
    const fetchTransactions = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.listTransactions(filters);
        setTransactions(data.transactions || []);
      } catch (err) {
        setError(err.message);
        console.error('Failed to fetch transactions:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [filters]);

  // Fetch audit record when transaction is selected
  useEffect(() => {
    if (!selectedTxId) {
      setAuditRecord(null);
      return;
    }

    const fetchAuditRecord = async () => {
      try {
        const data = await api.getAuditRecord(selectedTxId);
        setAuditRecord(data);
      } catch (err) {
        console.error('Failed to fetch audit record:', err);
        setError(err.message);
      }
    };

    fetchAuditRecord();
  }, [selectedTxId]);

  const handleLogout = () => {
    signOut();
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  const handleExport = async () => {
    try {
      await api.downloadCsv(filters);
    } catch (err) {
      console.error('Failed to export:', err);
      setError(err.message);
    }
  };

  const handleRowClick = (transactionId) => {
    setSelectedTxId(transactionId);
  };

  const handleCloseModal = () => {
    setSelectedTxId(null);
    setAuditRecord(null);
  };

  const displayName = businessName || user?.primaryEmailAddress?.emailAddress || 'Dashboard';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{displayName}</h1>
              <p className="text-sm text-gray-600 mt-1">Compliance Audit Dashboard</p>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowKeys(true)}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 flex items-center gap-1.5"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                </svg>
                API Keys
              </button>
              <div className="text-right">
                <div className="text-xs text-gray-500 uppercase tracking-wide">Powered by</div>
                <div className="text-lg font-semibold text-blue-600">Radius</div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            <strong>Error:</strong> {error}
          </div>
        )}

        <StatsBar transactions={transactions} />

        <Filters
          filters={filters}
          onFilterChange={handleFilterChange}
          onExport={handleExport}
          onLogout={handleLogout}
        />

        <TransactionList
          transactions={transactions}
          onRowClick={handleRowClick}
          loading={loading}
        />
      </main>

      {/* Transaction Detail Modal */}
      {selectedTxId && (
        <TransactionDetail
          auditRecord={auditRecord}
          onClose={handleCloseModal}
        />
      )}

      {/* Key Management Modal */}
      {showKeys && (
        <KeyManagement onClose={() => setShowKeys(false)} />
      )}
    </div>
  );
}

export default function App() {
  return (
    <>
      <SignedOut>
        <LoginPage />
      </SignedOut>
      <SignedIn>
        <Dashboard />
      </SignedIn>
    </>
  );
}
