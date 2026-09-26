import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, MessageSquarePlus, Pencil, Trash2, X } from 'lucide-react'
import { useMemo, useState, type KeyboardEvent } from 'react'
import { Link } from 'react-router'

import { deleteAllConversations, deleteConversation, fetchConversations, renameConversation } from '@/api/chat'
import { SearchInput } from '@/components/ui/SearchInput'
import { cn } from '@/lib/cn'
import type { Conversation } from '@/types/chat'

import { CONVERSATIONS_KEY, messagesKey } from './useChat'

const DAY = 86_400_000

function groupLabel(updatedAt: string) {
  const days = Math.floor((new Date().setHours(0, 0, 0, 0) - new Date(updatedAt).setHours(0, 0, 0, 0)) / DAY)
  if (days <= 0) return 'Hôm nay'
  if (days === 1) return 'Hôm qua'
  if (days < 7) return '7 ngày qua'
  if (days < 30) return '30 ngày qua'
  return 'Cũ hơn'
}

function Item({ conversation, active, locked, onDeleted }: {
  conversation: Conversation
  active: boolean
  /** Đang trả lời trong cuộc này: không cho xóa */
  locked: boolean
  onDeleted: () => void
}) {
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(conversation.title)

  const rename = useMutation({
    mutationFn: (value: string) => renameConversation(conversation.id, value),
    onSuccess: (saved) =>
      queryClient.setQueryData<Conversation[]>(CONVERSATIONS_KEY, (list = []) => list.map((c) => (c.id === saved.id ? saved : c))),
  })
  const remove = useMutation({
    mutationFn: () => deleteConversation(conversation.id),
    onSuccess: () => {
      queryClient.setQueryData<Conversation[]>(CONVERSATIONS_KEY, (list = []) => list.filter((c) => c.id !== conversation.id))
      queryClient.removeQueries({ queryKey: messagesKey(conversation.id) })
      onDeleted()
    },
  })

  const save = () => {
    const value = title.trim()
    setEditing(false)
    if (value && value !== conversation.title) rename.mutate(value)
    else setTitle(conversation.title)
  }
  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.nativeEvent.isComposing) save()
    if (e.key === 'Escape') {
      setTitle(conversation.title)
      setEditing(false)
    }
  }

  if (editing) {
    return (
      <div className="flex items-center gap-1 rounded-lg bg-surface px-1.5 py-1 ring-1 ring-brand">
        <input
          autoFocus
          value={title}
          maxLength={120}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={onKeyDown}
          onBlur={save}
          aria-label="Tên cuộc trò chuyện"
          className="min-w-0 flex-1 bg-transparent px-1 py-0.5 text-[13px] outline-none"
        />
        <button onMouseDown={(e) => e.preventDefault()} onClick={save} className="rounded p-1 text-success hover:bg-hover" title="Lưu"><Check size={14} /></button>
        <button onMouseDown={(e) => e.preventDefault()} onClick={() => { setTitle(conversation.title); setEditing(false) }} className="rounded p-1 text-muted hover:bg-hover" title="Hủy"><X size={14} /></button>
      </div>
    )
  }

  return (
    <div className={cn('group relative flex items-center rounded-lg transition-colors', active ? 'bg-brand-soft' : 'hover:bg-hover')}>
      <Link
        to={`/chat/${conversation.id}`}
        aria-current={active ? 'page' : undefined}
        title={conversation.title}
        className={cn('min-w-0 flex-1 truncate py-2 pr-2 pl-3 text-[13px]', active ? 'font-medium text-brand-ink' : 'text-fg-2')}
      >
        {rename.isPending ? title : conversation.title}
      </Link>
      <div className={cn('flex shrink-0 items-center pr-1', active ? 'flex' : 'hidden group-focus-within:flex group-hover:flex')}>
        <button onClick={() => setEditing(true)} className="rounded p-1.5 text-muted hover:bg-surface hover:text-fg" title="Đổi tên">
          <Pencil size={13} />
        </button>
        <button
          onClick={() => confirm(`Xóa cuộc trò chuyện "${conversation.title}"?`) && remove.mutate()}
          disabled={remove.isPending || locked}
          className="rounded p-1.5 text-muted hover:bg-surface hover:text-danger disabled:opacity-40"
          title="Xóa"
        >
          <Trash2 size={13} />
        </button>
      </div>
    </div>
  )
}

/** Danh sách cuộc trò chuyện, nhóm theo thời gian hoạt động gần nhất. */
export function ConversationList({ activeId, onNavigate, onActiveDeleted, disabled }: {
  activeId: string | null
  /** Gọi sau khi chọn một mục (đóng ngăn kéo trên di động) */
  onNavigate?: () => void
  onActiveDeleted: () => void
  /** Đang trả lời: không cho xóa cuộc đang mở / xóa tất cả */
  disabled?: boolean
}) {
  const queryClient = useQueryClient()
  const conversations = useQuery({ queryKey: CONVERSATIONS_KEY, queryFn: fetchConversations })
  const [search, setSearch] = useState('')

  const clearAll = useMutation({
    mutationFn: deleteAllConversations,
    onSuccess: () => {
      queryClient.setQueryData(CONVERSATIONS_KEY, [])
      queryClient.removeQueries({ queryKey: ['chat', 'messages'] })
      onActiveDeleted()
    },
  })

  const groups = useMemo(() => {
    const keyword = search.trim().toLowerCase()
    const out = new Map<string, Conversation[]>()
    for (const c of conversations.data ?? []) {
      if (keyword && !c.title.toLowerCase().includes(keyword)) continue
      const label = groupLabel(c.updatedAt)
      out.set(label, [...(out.get(label) ?? []), c])
    }
    return [...out]
  }, [conversations.data, search])

  const total = conversations.data?.length ?? 0

  return (
    <div className="flex h-full flex-col" onClick={(e) => (e.target as HTMLElement).closest('a') && onNavigate?.()}>
      <div className="space-y-2 p-3">
        <Link to="/chat" className="btn-primary w-full">
          <MessageSquarePlus size={16} />
          Cuộc trò chuyện mới
        </Link>
        {total > 5 && <SearchInput value={search} onChange={setSearch} placeholder="Tìm cuộc trò chuyện…" className="sm:w-full" />}
      </div>

      <nav aria-label="Lịch sử trò chuyện" className="flex-1 overflow-y-auto px-2 pb-3">
        {conversations.isPending ? (
          <div className="space-y-2 px-1">
            {[0, 1, 2, 3].map((i) => <div key={i} className="h-8 animate-pulse rounded-lg bg-hover" />)}
          </div>
        ) : conversations.isError ? (
          <p className="px-3 py-4 text-[13px] text-danger">Không tải được lịch sử.</p>
        ) : !total ? (
          <p className="px-3 py-4 text-[13px] text-muted">Chưa có cuộc trò chuyện nào. Câu hỏi đầu tiên sẽ tạo cuộc mới.</p>
        ) : !groups.length ? (
          <p className="px-3 py-4 text-[13px] text-muted">Không có cuộc trò chuyện phù hợp.</p>
        ) : (
          groups.map(([label, items]) => (
            <section key={label} className="mb-3">
              <h3 className="px-3 pt-2 pb-1 text-[11px] font-medium tracking-wide text-muted uppercase">{label}</h3>
              <div className="space-y-0.5">
                {items.map((c) => (
                  <Item key={c.id} conversation={c} active={c.id === activeId} locked={!!disabled && c.id === activeId} onDeleted={() => c.id === activeId && onActiveDeleted()} />
                ))}
              </div>
            </section>
          ))
        )}
      </nav>

      {total > 0 && (
        <div className="border-t border-line p-2">
          <button
            onClick={() => confirm('Xóa toàn bộ lịch sử trò chuyện?') && clearAll.mutate()}
            disabled={clearAll.isPending || disabled}
            className="btn-ghost h-8 w-full justify-start px-3 text-[13px] hover:text-danger"
          >
            <Trash2 size={14} />
            Xóa tất cả
          </button>
        </div>
      )}
    </div>
  )
}
