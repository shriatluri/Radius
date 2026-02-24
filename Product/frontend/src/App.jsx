import { useState, useEffect } from 'react';
import { api } from './lib/api';
import ApiKeyInput from './components/ApiKeyInput';
import StatsBar from './components/StatsBar';
import Filters from './components/Filters';
import TransactionList from './components/TransactionList';
import TransactionDetail from './components/TransactionDetail';

export default function App() {
  const [apiKey, setApiKey] = useState(api.getApiKey());
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

  // Fetch transactions when filters change
  useEffect(() => {
    if (!apiKey) return;

    const fetchTransactions = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.listTransactions(filters);
        setTransactions(data.transactions || []);
      } catch (err) {
        setError(err.message);
        console.error('Failed to fetch transactions:', err);

        // If unauthorized, clear API key
        if (err.message.includes('401') || err.message.includes('403') || err.message.includes('Unauthorized')) {
          handleLogout();
        }
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [apiKey, filters]);

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

  const handleApiKeySubmit = (key) => {
    api.setApiKey(key);
    setApiKey(key);
  };

  const handleLogout = () => {
    api.clearApiKey();
    setApiKey(null);
    setTransactions([]);
    setFilters({
      status: null,
      risk_level: null,
      start_date: null,
      end_date: null,
      limit: 100,
    });
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

  // If not authenticated, show API key input
  if (!apiKey) {
    return <ApiKeyInput onSubmit={handleApiKeySubmit} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Acme Corp</h1>
              <p className="text-sm text-gray-600 mt-1">Compliance Audit Dashboard</p>
            </div>
            <div className="text-right">
              <div className="text-xs text-gray-500 uppercase tracking-wide">Powered by</div>
              <div className="text-lg font-semibold text-blue-600">Radius</div>
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
    </div>
  );
}
