import { useState, useEffect } from 'react';
import { api } from '../lib/api';

export default function KeyManagement({ onClose }) {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newKeyResult, setNewKeyResult] = useState(null);
  const [creating, setCreating] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: '',
    scopes: 'transactions:write,transactions:read,reports:read',
  });

  const fetchKeys = async () => {
    setLoading(true);
    try {
      const data = await api.listApiKeys();
      setKeys(data.keys || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const result = await api.createApiKey({
        name: createForm.name || 'Unnamed Key',
        scopes: createForm.scopes,
        is_test_key: true,
      });
      setNewKeyResult(result);
      setShowCreate(false);
      setCreateForm({ name: '', scopes: 'transactions:write,transactions:read,reports:read' });
      fetchKeys();
    } catch (err) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (keyId, keyName) => {
    if (!window.confirm(`Revoke "${keyName || keyId}"? This cannot be undone.`)) return;
    try {
      await api.revokeApiKey(keyId);
      fetchKeys();
    } catch (err) {
      setError(err.message);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">API Keys</h2>
            <p className="text-sm text-gray-500">Manage programmatic access to your Radius account</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            &times;
          </button>
        </div>

        <div className="px-6 py-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {/* New key result banner */}
          {newKeyResult && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-green-800">Key created successfully</p>
                  <p className="text-xs text-green-600 mt-1">Copy this key now. It will not be shown again.</p>
                </div>
                <button
                  onClick={() => setNewKeyResult(null)}
                  className="text-green-400 hover:text-green-600"
                >
                  &times;
                </button>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <code className="flex-1 bg-white px-3 py-2 rounded border border-green-300 text-sm font-mono text-gray-900 select-all">
                  {newKeyResult.api_key}
                </code>
                <button
                  onClick={() => copyToClipboard(newKeyResult.api_key)}
                  className="px-3 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                >
                  Copy
                </button>
              </div>
            </div>
          )}

          {/* Create key form */}
          {showCreate ? (
            <form onSubmit={handleCreate} className="bg-gray-50 rounded-lg p-4 mb-4 border border-gray-200">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Create new API key</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Key name</label>
                  <input
                    type="text"
                    value={createForm.name}
                    onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                    placeholder="e.g. Production, Staging"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Scopes</label>
                  <select
                    value={createForm.scopes}
                    onChange={(e) => setCreateForm({ ...createForm, scopes: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="transactions:write,transactions:read,reports:read">Full access (read + write)</option>
                    <option value="transactions:read,reports:read">Read only</option>
                    <option value="transactions:write">Write only</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-2 mt-4">
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create key'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md text-sm hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <button
              onClick={() => setShowCreate(true)}
              className="mb-4 px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Create API key
            </button>
          )}

          {/* Keys table */}
          {loading ? (
            <div className="text-center py-8 text-gray-500">Loading keys...</div>
          ) : keys.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No API keys yet</p>
              <p className="text-sm text-gray-400 mt-1">Create one to start using the Radius API</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Key</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Scopes</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last used</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {keys.map((k) => (
                    <tr key={k.key_id}>
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                        {k.name || 'Unnamed'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <code className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                          {k.key_prefix}{'*'.repeat(12)}
                        </code>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex flex-wrap gap-1">
                          {k.scopes.split(',').map((scope) => (
                            <span
                              key={scope}
                              className="px-1.5 py-0.5 text-xs bg-blue-50 text-blue-700 rounded"
                            >
                              {scope.trim()}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                        {k.last_used_at
                          ? new Date(k.last_used_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                          : 'Never'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                        {new Date(k.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                          k.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-500'
                        }`}>
                          {k.is_active ? 'Active' : 'Revoked'}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        {k.is_active && (
                          <button
                            onClick={() => handleRevoke(k.key_id, k.name)}
                            className="text-xs text-red-600 hover:text-red-800 font-medium"
                          >
                            Revoke
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
