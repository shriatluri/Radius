export default function StatsBar({ transactions }) {
  const stats = {
    total: transactions.length,
    totalVolume: transactions.reduce((sum, t) => sum + parseFloat(t.amount || 0), 0),
    approved: transactions.filter(t => t.status === 'approved').length,
    pending: transactions.filter(t => t.status === 'pending').length,
    blocked: transactions.filter(t => t.status === 'blocked').length,
    sanctionsCleared: transactions.filter(t => t.sanctions_result === 'clear' || t.sanctions_result === 'passed').length,
    highRisk: transactions.filter(t => t.risk_level === 'high' || t.risk_level === 'critical').length,
  };

  const complianceRate = stats.total > 0 ? ((stats.approved / stats.total) * 100).toFixed(1) : 0;
  const sanctionsRate = stats.total > 0 ? ((stats.sanctionsCleared / stats.total) * 100).toFixed(1) : 0;

  const statCards = [
    {
      label: 'Total Transactions',
      value: stats.total,
      color: 'bg-blue-50 text-blue-700',
      subtitle: `$${stats.totalVolume.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} volume`
    },
    {
      label: 'Compliance Rate',
      value: `${complianceRate}%`,
      color: 'bg-green-50 text-green-700',
      subtitle: `${stats.approved} approved`
    },
    {
      label: 'Sanctions Screening',
      value: `${sanctionsRate}%`,
      color: 'bg-purple-50 text-purple-700',
      subtitle: `${stats.sanctionsCleared}/${stats.total} cleared`
    },
    {
      label: 'Flagged for Review',
      value: stats.pending + stats.blocked + stats.highRisk,
      color: stats.pending + stats.blocked + stats.highRisk > 0 ? 'bg-yellow-50 text-yellow-700' : 'bg-gray-50 text-gray-700',
      subtitle: `${stats.pending} pending, ${stats.blocked} blocked`
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {statCards.map((stat) => (
        <div key={stat.label} className={`${stat.color} rounded-lg p-4`}>
          <div className="text-xs font-medium opacity-75 uppercase tracking-wide">{stat.label}</div>
          <div className="text-3xl font-bold mt-2">{stat.value}</div>
          {stat.subtitle && (
            <div className="text-xs opacity-75 mt-1">{stat.subtitle}</div>
          )}
        </div>
      ))}
    </div>
  );
}
