import { useEffect, useRef, useState } from 'react'

/** Chiều rộng thật của phần tử (px), cập nhật khi đổi kích thước — để vẽ SVG đúng pixel, chữ không bị kéo giãn. */
export function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [width, setWidth] = useState(0)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const observer = new ResizeObserver(([entry]) => setWidth(Math.floor(entry.contentRect.width)))
    observer.observe(el)
    return () => observer.disconnect()
  }, [])
  return [ref, width] as const
}
