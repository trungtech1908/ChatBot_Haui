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
  { key: 'income', label: 'Khoản thu' },
  { key: 'expense', label: 'Khoản chi' },
] as const

type Filter = (typeof FILTERS)[number]['key']

function FinanceView({ finance }: { finance: Finance }) {
  const [filter, setFilter] = useState<Filter>('all')
  const rows = finance.transactions.filter((t) => filter === 'all' || t.isIncome === (filter === 'income'))

  return (
    <>
      <PageHeader section="Tài chính" title="Học phí & giao dịch" />
      <Figures
        className="mb-5"
        items={[
          { label: 'Số dư tài khoản', value: formatMoney(finance.balance) },
          { label: 'Công nợ phải nộp', value: formatMoney(finance.debt), alert: finance.debt > 0, note: finance.debt > 0 ? 'Nộp trước hạn để không bị khóa đăng ký học phần' : 'Không có công nợ' },
          { label: 'Học bổng đã nhận', value: formatMoney(finance.scholarship) },
        ]}
      />

      <Section
        title="Lịch sử giao dịch"
        flush
        aside={
          <div className="flex gap-3 text-sm">
            {FILTERS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={cn(filter === key ? 'font-medium text-brand underline underline-offset-4' : 'text-muted hover:text-fg')}
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
                <TH className="w-24">Mã GD</TH>
                <TH>Nội dung</TH>
                <TH>Ghi chú</TH>
                <TH className="text-right">Số tiền</TH>
              </tr>
            </THead>
            <TBody>
              {rows.map((t) => (
                <TR key={t.code}>
                  <TD className="font-mono text-xs">{t.code}</TD>
                  <TD>{t.name}</TD>
                  <TD className="text-muted">{t.note}</TD>
                  <TD className={cn('text-right whitespace-nowrap tabular-nums', t.isIncome ? 'text-emerald-700 dark:text-emerald-400' : '')}>
                    {t.isIncome ? '+' : '−'}
                    {formatMoney(t.amount)}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        ) : (
          <p className="px-4 py-3 text-sm text-muted">Không có giao dịch.</p>
        )}
      </Section>
    </>
  )
}

export function FinancePage() {
  return <QueryState query={useFinance()}>{(finance) => <FinanceView finance={finance} />}</QueryState>
}
