import { Download, Gift, Receipt, Wallet } from 'lucide-react'
import { useMemo, useState } from 'react'

import { useFinance } from '@/api/students'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { type Column, DataTable } from '@/components/ui/DataTable'
import { PageHeader } from '@/components/ui/PageHeader'
import { Progress } from '@/components/ui/Progress'
import { QueryState } from '@/components/ui/QueryState'
import { SearchInput } from '@/components/ui/SearchInput'
import { Section } from '@/components/ui/Section'
import { Segmented } from '@/components/ui/Segmented'
import { Select } from '@/components/ui/Select'
import { StatGrid } from '@/components/ui/StatCard'
import { cn } from '@/lib/cn'
import { downloadCsv } from '@/lib/csv'
import { formatDate, formatDateTime, formatMoney, isOverdue, relativeDays, shortSemester } from '@/lib/format'
import type { Finance, Payable, SemesterDebt, Transaction } from '@/types/student'
import type { Tone } from '@/types/ui'

type Tab = 'debts' | 'transactions'
type PayState = 'all' | 'unpaid' | 'paid'
type Direction = 'all' | 'in' | 'out'

const PAYABLE_KIND: Record<Payable['kind'], string> = { hoc_phi: 'Học phí', khoan_thu: 'Khoản thu', phi_phat: 'Phí', khac: 'Khác' }
const TRANSACTION_KIND: Record<string, string> = {
  nap_tien: 'Nạp tiền', thanh_toan: 'Thanh toán', nhan_hb: 'Học bổng', nhan_mghp: 'Miễn giảm học phí',
  nhan_ho_tro: 'Hỗ trợ', rut_tien: 'Rút tiền', hoan_tien: 'Hoàn tiền',
}
const PAGE = 20

function payStatus(remaining: number, paid: number, dueDate: string | null): { label: string; tone: Tone; rank: number } {
  if (remaining <= 0) return { label: 'Đã nộp đủ', tone: 'green', rank: 3 }
  if (isOverdue(dueDate, remaining)) return { label: 'Quá hạn', tone: 'red', rank: 0 }
  return paid > 0 ? { label: 'Nộp một phần', tone: 'yellow', rank: 1 } : { label: 'Chưa nộp', tone: 'orange', rank: 2 }
}

const money = (value: number, className?: string) => <span className={cn('whitespace-nowrap', className)}>{formatMoney(value)}</span>

const debtColumns: Column<SemesterDebt>[] = [
  { key: 'semester', header: 'Học kỳ', render: (d) => <span className="font-medium whitespace-nowrap">{d.semester}</span>, sortValue: (d) => d.semesterCode },
  { key: 'total', header: 'Phải nộp', align: 'right', render: (d) => money(d.total), sortValue: (d) => d.total },
  { key: 'paid', header: 'Đã nộp', align: 'right', render: (d) => money(d.paid, 'text-fg-2'), sortValue: (d) => d.paid },
  { key: 'remaining', header: 'Còn nợ', align: 'right', render: (d) => money(d.remaining, d.remaining > 0 ? 'font-semibold text-danger' : 'text-muted'), sortValue: (d) => d.remaining },
  {
    key: 'progress', header: 'Tiến độ nộp',
    render: (d) => (
      <div className="flex min-w-36 items-center gap-2">
        <Progress value={d.paid} max={d.total} tone={d.remaining <= 0 ? 'success' : 'brand'} className="flex-1" />
        <span className="w-9 text-right text-xs text-muted tabular-nums">{d.total ? Math.round((d.paid / d.total) * 100) : 100}%</span>
      </div>
    ),
    sortValue: (d) => (d.total ? d.paid / d.total : 1),
  },
  { key: 'due', header: 'Hạn nộp', render: (d) => <span className="whitespace-nowrap">{d.remaining > 0 ? formatDate(d.dueDate) : '—'}</span>, sortValue: (d) => (d.remaining > 0 ? d.dueDate : null) },
  {
    key: 'status', header: 'Trạng thái',
    render: (d) => { const s = payStatus(d.remaining, d.paid, d.dueDate); return <Badge tone={s.tone}>{s.label}</Badge> },
    sortValue: (d) => payStatus(d.remaining, d.paid, d.dueDate).rank,
  },
]

const payableColumns: Column<Payable>[] = [
  {
    key: 'content', header: 'Khoản phải nộp',
    render: (p) => (
      <div className="min-w-52">
        <p className="font-medium">{p.content ?? PAYABLE_KIND[p.kind]}</p>
        <p className="text-xs text-muted">{PAYABLE_KIND[p.kind]} · {shortSemester(p.semester)}</p>
      </div>
    ),
    sortValue: (p) => p.content,
  },
  { key: 'amount', header: 'Số tiền', align: 'right', render: (p) => money(p.amount), sortValue: (p) => p.amount },
  { key: 'paid', header: 'Đã nộp', align: 'right', render: (p) => money(p.paid, 'text-fg-2'), sortValue: (p) => p.paid },
  { key: 'remaining', header: 'Còn nợ', align: 'right', render: (p) => money(p.remaining, p.remaining > 0 ? 'font-semibold text-danger' : 'text-muted'), sortValue: (p) => p.remaining },
  {
    key: 'due', header: 'Hạn nộp',
    render: (p) => (
      <div className="whitespace-nowrap">
        <p>{formatDate(p.dueDate)}</p>
        {p.remaining > 0 && p.dueDate && <p className={cn('text-xs', isOverdue(p.dueDate, p.remaining) ? 'text-danger' : 'text-muted')}>{relativeDays(p.dueDate)}</p>}
      </div>
    ),
    sortValue: (p) => p.dueDate,
  },
  {
    key: 'status', header: 'Trạng thái',
    render: (p) => { const s = payStatus(p.remaining, p.paid, p.dueDate); return <Badge tone={s.tone}>{s.label}</Badge> },
    sortValue: (p) => payStatus(p.remaining, p.paid, p.dueDate).rank,
  },
]

const transactionColumns: Column<Transaction>[] = [
  { key: 'time', header: 'Thời gian', render: (t) => <span className="whitespace-nowrap text-fg-2 tabular-nums">{formatDateTime(t.time)}</span>, sortValue: (t) => t.time },
  {
    key: 'name', header: 'Nội dung',
    render: (t) => (
      <div className="min-w-56">
        <p className="font-medium">{t.name}</p>
        {t.note && <p className="text-xs text-muted">{t.note}</p>}
      </div>
    ),
    sortValue: (t) => t.name,
  },
  { key: 'kind', header: 'Loại', render: (t) => <Badge variant="soft">{TRANSACTION_KIND[t.kind] ?? t.kind}</Badge>, sortValue: (t) => TRANSACTION_KIND[t.kind] ?? t.kind },
  { key: 'code', header: 'Mã GD', render: (t) => <span className="font-mono text-xs text-muted">{t.code}</span>, sortValue: (t) => t.code },
  {
    key: 'status', header: 'Trạng thái',
    render: (t) => <Badge tone={t.status === 'Thành công' ? 'green' : t.status === 'Thất bại' ? 'red' : 'yellow'}>{t.status}</Badge>,
    sortValue: (t) => t.status,
  },
  {
    key: 'amount', header: 'Số tiền', align: 'right',
    render: (t) => <span className={cn('font-semibold whitespace-nowrap', t.isIncome && 'text-success')}>{t.isIncome ? '+' : '−'}{formatMoney(t.amount)}</span>,
    sortValue: (t) => (t.amount == null ? null : t.isIncome ? t.amount : -t.amount),
  },
]

function DebtsTab({ finance }: { finance: Finance }) {
  const [semester, setSemester] = useState('all')
  const [state, setState] = useState<PayState>('unpaid')
  const [kind, setKind] = useState<Payable['kind'] | 'all'>('all')

  const semesters = finance.debts.map((d) => [d.semesterCode, d.semester] as const)
  const base = finance.payables.filter((p) => (semester === 'all' || p.semesterCode === semester) && (kind === 'all' || p.kind === kind))
  const rows = base.filter((p) => state === 'all' || (state === 'unpaid') === p.remaining > 0)
  const kinds = [...new Set(finance.payables.map((p) => p.kind))]

  return (
    <div className="space-y-6">
      <Section title="Công nợ theo học kỳ" description="Tổng phải nộp, đã nộp và còn nợ của từng học kỳ" flush>
        <DataTable rows={finance.debts} columns={debtColumns} rowKey={(d) => d.semesterCode} defaultSort={{ key: 'semester', dir: 'desc' }} />
      </Section>

      <Section
        title="Chi tiết khoản phải nộp"
        description={`${rows.length} khoản · còn nợ ${formatMoney(rows.reduce((s, p) => s + p.remaining, 0))}`}
        toolbar={
          <>
            <Segmented<PayState>
              value={state}
              onChange={setState}
              options={[
                { value: 'unpaid', label: 'Còn nợ', count: base.filter((p) => p.remaining > 0).length },
                { value: 'paid', label: 'Đã nộp đủ', count: base.filter((p) => p.remaining <= 0).length },
                { value: 'all', label: 'Tất cả', count: base.length },
              ]}
            />
            <Select
              label="Học kỳ"
              value={semester}
              onChange={setSemester}
              options={[{ value: 'all', label: 'Tất cả học kỳ' }, ...semesters.map(([code, name]) => ({ value: code, label: shortSemester(name) }))]}
              className="w-44"
            />
            <Select<Payable['kind'] | 'all'>
              label="Loại khoản"
              value={kind}
              onChange={setKind}
              options={[{ value: 'all', label: 'Mọi loại khoản' }, ...kinds.map((k) => ({ value: k, label: PAYABLE_KIND[k] }))]}
              className="w-40"
            />
          </>
        }
        flush
      >
        <DataTable
          rows={rows}
          columns={payableColumns}
          rowKey={(p) => String(p.id)}
          defaultSort={{ key: 'due', dir: 'desc' }}
          empty={state === 'unpaid' ? 'Không còn khoản nào phải nộp.' : 'Không có khoản phù hợp.'}
          rowClassName={(p) => (isOverdue(p.dueDate, p.remaining) ? 'bg-danger-soft/50' : undefined)}
        />
      </Section>
    </div>
  )
}

function TransactionsTab({ transactions }: { transactions: Transaction[] }) {
  const [direction, setDirection] = useState<Direction>('all')
  const [kind, setKind] = useState('all')
  const [search, setSearch] = useState('')
  const [limit, setLimit] = useState(PAGE)

  const kinds = [...new Set(transactions.map((t) => t.kind))]
  const keyword = search.trim().toLowerCase()
  const base = useMemo(
    () => transactions.filter((t) => (kind === 'all' || t.kind === kind) && (!keyword || `${t.name} ${t.note} ${t.code}`.toLowerCase().includes(keyword))),
    [transactions, kind, keyword],
  )
  const rows = base.filter((t) => direction === 'all' || t.isIncome === (direction === 'in'))
  const totalIn = rows.filter((t) => t.isIncome).reduce((s, t) => s + (t.amount ?? 0), 0)
  const totalOut = rows.filter((t) => !t.isIncome).reduce((s, t) => s + (t.amount ?? 0), 0)

  const exportCsv = () =>
    downloadCsv(
      'giao-dich.csv',
      ['Thời gian', 'Mã GD', 'Loại', 'Nội dung', 'Ghi chú', 'Thu/Chi', 'Số tiền', 'Trạng thái'],
      rows.map((t) => [formatDateTime(t.time), t.code, TRANSACTION_KIND[t.kind] ?? t.kind, t.name, t.note, t.isIncome ? 'Thu' : 'Chi', t.amount, t.status]),
    )

  return (
    <Section
      title="Lịch sử giao dịch"
      description={
        <>
          {rows.length} giao dịch · thu <span className="font-medium text-success">+{formatMoney(totalIn)}</span> · chi <span className="font-medium text-fg-2">−{formatMoney(totalOut)}</span>
        </>
      }
      aside={<button onClick={exportCsv} className="btn-secondary"><Download size={15} />Xuất CSV</button>}
      toolbar={
        <>
          <Segmented<Direction>
            value={direction}
            onChange={(v) => { setDirection(v); setLimit(PAGE) }}
            options={[
              { value: 'all', label: 'Tất cả', count: base.length },
              { value: 'in', label: 'Tiền vào', count: base.filter((t) => t.isIncome).length },
              { value: 'out', label: 'Tiền ra', count: base.filter((t) => !t.isIncome).length },
            ]}
          />
          <Select
            label="Loại giao dịch"
            value={kind}
            onChange={(v) => { setKind(v); setLimit(PAGE) }}
            options={[{ value: 'all', label: 'Mọi loại giao dịch' }, ...kinds.map((k) => ({ value: k, label: TRANSACTION_KIND[k] ?? k }))]}
            className="w-48"
          />
          <SearchInput value={search} onChange={(v) => { setSearch(v); setLimit(PAGE) }} placeholder="Tìm nội dung, mã giao dịch…" className="sm:ml-auto" />
        </>
      }
      flush
    >
      <DataTable rows={rows.slice(0, limit)} columns={transactionColumns} rowKey={(t) => t.code} defaultSort={{ key: 'time', dir: 'desc' }} empty="Không có giao dịch phù hợp." />
      {rows.length > limit && (
        <div className="border-t border-line p-3 text-center">
          <button onClick={() => setLimit((l) => l + PAGE)} className="btn-ghost">Xem thêm ({rows.length - limit} giao dịch)</button>
        </div>
      )}
    </Section>
  )
}

function FinanceView({ finance }: { finance: Finance }) {
  const [tab, setTab] = useState<Tab>('debts')
  const overdue = finance.payables.filter((p) => isOverdue(p.dueDate, p.remaining))
  const nextDue = finance.payables
    .filter((p) => p.remaining > 0 && p.dueDate && !isOverdue(p.dueDate, p.remaining))
    .sort((a, b) => a.dueDate!.localeCompare(b.dueDate!))[0]
  const totalDue = finance.debts.reduce((s, d) => s + d.total, 0)
  const totalPaid = finance.debts.reduce((s, d) => s + d.paid, 0)

  return (
    <>
      <PageHeader title="Học phí & tài chính" description="Công nợ, khoản phải nộp và lịch sử giao dịch" />
      <div className="space-y-6">
        {overdue.length > 0 && (
          <Alert
            tone="danger"
            title={`${overdue.length} khoản quá hạn · ${formatMoney(overdue.reduce((s, p) => s + p.remaining, 0))}`}
            action={<button onClick={() => setTab('debts')} className="btn-secondary h-8">Xem chi tiết</button>}
          >
            Hạn sớm nhất {formatDate(overdue.map((p) => p.dueDate!).sort()[0])}. Nộp muộn có thể bị khóa đăng ký học phần.
          </Alert>
        )}

        <StatGrid
          items={[
            { label: 'Công nợ hiện tại', value: formatMoney(finance.debt), note: nextDue ? `Hạn gần nhất ${formatDate(nextDue.dueDate)} (${relativeDays(nextDue.dueDate!)})` : finance.debt > 0 ? 'Đã quá hạn' : 'Không có công nợ', icon: Receipt, alert: finance.debt > 0 },
            { label: 'Số dư tài khoản', value: formatMoney(finance.balance), note: finance.debt > 0 && finance.balance >= finance.debt ? 'Đủ để thanh toán công nợ' : undefined, icon: Wallet },
            { label: 'Đã nộp', value: formatMoney(totalPaid), note: `trên ${formatMoney(totalDue)} phải nộp`, icon: Receipt },
            { label: 'Học bổng đã nhận', value: formatMoney(finance.scholarship), icon: Gift },
          ]}
        />

        <Segmented<Tab>
          value={tab}
          onChange={setTab}
          options={[
            { value: 'debts', label: 'Công nợ & khoản phải nộp', count: finance.payables.filter((p) => p.remaining > 0).length },
            { value: 'transactions', label: 'Lịch sử giao dịch', count: finance.transactions.length },
          ]}
        />
        {tab === 'debts' ? <DebtsTab finance={finance} /> : <TransactionsTab transactions={finance.transactions} />}
      </div>
    </>
  )
}

export function FinancePage() {
  return <QueryState query={useFinance()}>{(finance) => <FinanceView finance={finance} />}</QueryState>
}
