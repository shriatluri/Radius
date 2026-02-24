export default function TransactionDetail({ auditRecord, onClose }) {
  if (!auditRecord) return null;

  const renderField = (label, value, monospace = false) => {
    if (value === null || value === undefined || value === '') return null;

    return (
      <div className="py-3 border-b border-gray-200 last:border-b-0">
        <div className="text-sm font-medium text-gray-500 mb-1">{label}</div>
        <div className={`text-sm text-gray-900 ${monospace ? 'font-mono' : ''}`}>
          {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">Transaction Audit Record</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="overflow-y-auto flex-1 p-6">
          <div className="space-y-6">
            {/* Basic Info */}
            <section>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Basic Information</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                {renderField('Transaction ID', auditRecord.transaction_id, true)}
                {renderField('Payment ID', auditRecord.payment_id, true)}
                {renderField('Business ID', auditRecord.business_id)}
                {renderField('Amount', auditRecord.amount)}
                {renderField('Asset', auditRecord.asset)}
                {renderField('Purpose', auditRecord.purpose)}
                {renderField('Created At', auditRecord.created_at ? new Date(auditRecord.created_at).toLocaleString() : null)}
              </div>
            </section>

            {/* Entities */}
            <section>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Entities</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                {renderField('From Entity', auditRecord.from_entity)}
                {renderField('From Wallet', auditRecord.from_wallet, true)}
                {renderField('To Entity', auditRecord.to_entity)}
                {renderField('To Wallet', auditRecord.to_wallet, true)}
              </div>
            </section>

            {/* Compliance */}
            <section>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Compliance</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                {renderField('Status', auditRecord.status)}
                {renderField('Risk Score', auditRecord.risk_score)}
                {renderField('Risk Level', auditRecord.risk_level)}
                {renderField('Sanctions Result', auditRecord.sanctions_result)}
                {renderField('Travel Rule Status', auditRecord.travel_rule_status)}
              </div>
            </section>

            {/* Blockchain */}
            {auditRecord.tx_hash && (
              <section>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Blockchain</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  {renderField('Transaction Hash', auditRecord.tx_hash, true)}
                </div>
              </section>
            )}

            {/* Approvals */}
            {auditRecord.approvals && auditRecord.approvals.length > 0 && (
              <section>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Approvals</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  {renderField('Approvals', auditRecord.approvals)}
                </div>
              </section>
            )}

            {/* Reconciliation */}
            {auditRecord.reconciliation_status && (
              <section>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Reconciliation</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  {renderField('Reconciliation Status', auditRecord.reconciliation_status)}
                </div>
              </section>
            )}
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
