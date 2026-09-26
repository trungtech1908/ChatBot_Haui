/** Tải xuống bảng dữ liệu dạng CSV (UTF-8 có BOM để Excel đọc đúng tiếng Việt). */
export function downloadCsv(filename: string, headers: string[], rows: (string | number | null | undefined)[][]) {
  const escape = (value: string | number | null | undefined) => {
    const text = value == null ? '' : String(value)
    return /[",\n;]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
  }
  const csv = [headers, ...rows].map((row) => row.map(escape).join(',')).join('\n')
  const url = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' }))
  const link = Object.assign(document.createElement('a'), { href: url, download: filename })
  link.click()
  URL.revokeObjectURL(url)
}
