export function SearchInput({ value, onChange, placeholder }: { value: string; onChange: (value: string) => void; placeholder: string }) {
  return <input type="search" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="input w-full sm:w-64" />
}
