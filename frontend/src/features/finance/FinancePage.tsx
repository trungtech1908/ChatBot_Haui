import { ArrowDownLeft, ArrowUpRight, Award, Receipt, Wallet } from 'lucide-react'
import { useState } from 'react'

import { useFinance } from '@/api/students'
import { Card } from '@/components/ui/Card'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { StatCard } from '@/components/ui/StatCard'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/Table'
import { cn } from '@/lib/cn'
import { formatMoney } from '@/lib/format'
import type { Finance } from '@/types/student'

const FILTERS = [
  { key: 'all', label: 'Tất cả' },
  { key: 'income', label: 'Thu' },
  { key: 'expense', label: 'Chi' },
] as const

type Filter = (typeof FILTERS)[number]['key']

function FinanceView({ finance }: { finance: Finance }) {
  const [filter, setFilter] = useState<Filter>('all')
  const rows = finance.transactions.filter((t) => filter === 'all' || t.isIncome === (filter === 'income'))

  return (
    <>
      <PageHeader title="Tài chính" description="Số dư, công nợ và lịch sử giao dịch" />
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard label="Số dư tài khoản" value={formatMoney(finance.balance)} icon={Wallet} tone="green" />
        <StatCard
          label="Công nợ phải đóng"
          value={formatMoney(finance.debt)}
          icon={Receipt}
          tone={finance.debt ? 'red' : 'green'}
          hint={finance.debt ? 'Vui lòng thanh toán đúng hạn' : 'Không có công nợ'}
        />
        <StatCard label="Học bổng tích lũy" value={formatMoney(finance.scholarship)} icon={Award} tone="purple" />
      </div>

      <Card
        title="Lịch sử giao dịch"
        description={`${finance.transactions.length} giao dịch`}
        bodyClassName="p-0"
        action={
          <div className="flex rounded-xl bg-surface-2 p-1">
            {FILTERS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={cn('rounded-lg px-3 py-1 text-sm font-medium transition', filter === key ? 'bg-surface text-fg shadow-sm' : 'text-muted hover:text-fg')}
              >
                {label}
              </button>
            ))}
          </div>
        }
      >
        {rows.length ? (
          <Table>
            <THead>
              <tr>
                <TH>Giao dịch</TH>
                <TH className="hidden sm:table-cell">Mã GD</TH>
                <TH className="text-right">Số tiền</TH>
              </tr>
            </THead>
            <TBody>
              {rows.map((t) => (
                <TR key={t.code}>
                  <TD>
                    <div className="flex items-center gap-3">
                      <span className={cn('flex h-9 w-9 shrink-0 items-center justify-center rounded-xl', t.isIncome ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' : 'bg-rose-500/10 text-rose-600 dark:text-rose-400')}>
                        {t.isIncome ? <ArrowDownLeft size={16} /> : <ArrowUpRight size={16} />}
                      </span>
                      <div className="min-w-0">
                        <p className="font-medium">{t.name}</p>
                        <p className="text-xs text-muted">{t.note}</p>
                      </div>
                    </div>
                  </TD>
                  <TD className="hidden font-mono text-xs text-muted sm:table-cell">{t.code}</TD>
                  <TD className={cn('text-right font-semibold whitespace-nowrap tabular-nums', t.isIncome && 'text-emerald-600 dark:text-emerald-400')}>
                    {t.isIncome ? '+' : '−'}
                    {formatMoney(t.amount)}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        ) : (
          <p className="p-6 text-center text-sm text-muted">Không có giao dịch.</p>
        )}
      </Card>
    </>
  )
}

export function FinancePage() {
  return <QueryState query={useFinance()}>{(finance) => <FinanceView finance={finance} />}</QueryState>
}
