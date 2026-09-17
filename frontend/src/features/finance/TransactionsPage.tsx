import { useFinance } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { formatMoney } from '@/lib/format'

export function TransactionsPage() {
  return (
    <>
      <PageHeader title="Lịch sử Giao dịch" />
      <QueryState query={useFinance()} empty="Chưa có phát sinh giao dịch nào." isEmpty={(f) => !f.transactions.length}>
        {({ transactions }) => (
          <div className="overflow-x-auto rounded bg-white shadow">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-100 text-xs font-bold text-gray-700 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Mã GD</th>
                  <th className="px-4 py-3 text-left">Nội dung</th>
                  <th className="px-4 py-3 text-right">Số tiền</th>
                  <th className="px-4 py-3 text-center">Loại</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {transactions.map((t) => (
                  <tr key={t.code} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-gray-500">{t.code}</td>
                    <td className="px-4 py-3">
                      <span className="block font-medium">{t.name}</span>
                      <span className="text-xs text-gray-500">{t.note}</span>
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-gray-800">{formatMoney(t.amount)}</td>
                    <td className="px-4 py-3 text-center">
                      {t.isIncome ? <Badge tone="green">+ Thu</Badge> : <Badge tone="red">- Chi</Badge>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </QueryState>
    </>
  )
}
