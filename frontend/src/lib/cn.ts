/** Ghép className, bỏ giá trị rỗng/false. */
export const cn = (...classes: (string | false | null | undefined)[]) => classes.filter(Boolean).join(' ')
