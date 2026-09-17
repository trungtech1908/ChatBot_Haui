import { useState } from 'react'

import { useFinance } from '@/api/students'
import { Figures } from '@/components/ui/Figures'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { Section } from '@/components/ui/Section'
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
      <PageHeader title="Học phí" description="Số dư, công nợ và lịch sử giao dịch" />
      <Figures
        className="mb-4 lg:grid-cols-3"
        items={[
          { label: 'Số dư tài khoản', value: formatMoney(finance.balance) },
          { label: 'Công nợ', value: formatMoney(finance.debt), alert: finance.debt > 0, note: finance.debt > 0 ? 'Cần nộp trước hạn' : 'Không có công nợ' },
          { label: 'Học bổng', value: formatMoney(finance.scholarship) },
        ]}
      />

      <Section
        title="Lịch sử giao dịch"
        description={`${rows.length} giao dịch`}
        flush
        aside={
          <div className="flex rounded-lg bg-hover p-0.5">
            {FILTERS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={cn('h-7 rounded-md px-3 text-[13px] font-medium transition', filter === key ? 'bg-surface text-fg shadow-sm' : 'text-muted hover:text-fg')}
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
                <TH>Nội dung</TH>
                <TH>Mã giao dịch</TH>
                <TH className="text-right">Số tiền</TH>
              </tr>
            </THead>
            <TBody>
              {rows.map((t) => (
                <TR key={t.code}>
                  <TD className="py-2.5">
                    <p className="font-medium">{t.name}</p>
                    <p className="text-[13px] text-muted">{t.note}</p>
                  </TD>
                  <TD className="font-mono text-xs text-muted">{t.code}</TD>
                  <TD className={cn('text-right font-medium whitespace-nowrap tabular-nums', t.isIncome && 'text-success')}>
                    {t.isIncome ? '+' : '−'}
                    {formatMoney(t.amount)}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        ) : (
          <p className="px-5 py-8 text-center text-muted">Không có giao dịch.</p>
        )}
      </Section>
    </>
  )
}

export function FinancePage() {
  return <QueryState query={useFinance()}>{(finance) => <FinanceView finance={finance} />}</QueryState>
}
