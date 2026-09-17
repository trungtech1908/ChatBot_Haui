import type { LucideIcon } from 'lucide-react'
import { Award, FileText, Wallet } from 'lucide-react'

import { useFinance } from '@/api/students'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { formatMoney } from '@/lib/format'

const styles = {
  green: 'bg-green-50 border-green-500 text-green-800',
  red: 'bg-red-50 border-red-500 text-red-800',
  blue: 'bg-blue-50 border-blue-500 text-blue-800',
}

function StatCard({ label, value, icon: Icon, color }: { label: string; value: number; icon: LucideIcon; color: keyof typeof styles }) {
  return (
    <div className={`flex items-center justify-between rounded-lg border-l-4 p-6 shadow ${styles[color]}`}>
      <div>
        <p className="text-xs font-bold tracking-wider uppercase opacity-80">{label}</p>
        <p className="mt-1 text-2xl font-bold">{formatMoney(value)}</p>
      </div>
      <Icon size={32} className="opacity-30" />
    </div>
  )
}

export function FinancePage() {
  return (
    <>
      <PageHeader title="Tình hình Tài chính" />
      <QueryState query={useFinance()}>
        {(finance) => (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <StatCard label="Số dư tài khoản" value={finance.balance} icon={Wallet} color="green" />
            <StatCard label="Công nợ phải đóng" value={finance.debt} icon={FileText} color="red" />
            <StatCard label="Học bổng tích lũy" value={finance.scholarship} icon={Award} color="blue" />
          </div>
        )}
      </QueryState>
    </>
  )
}
