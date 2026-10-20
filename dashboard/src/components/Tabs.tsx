interface Props<T extends string> {
  label: string
  items: [T, string][]
  value: T
  onChange: (value: T) => void
  small?: boolean
}

/** Tab bar in a well (role=tablist); arrow keys move between tabs. */
export function Tabs<T extends string>({ label, items, value, onChange, small }: Props<T>) {
  const move = (index: number) => onChange(items[(index + items.length) % items.length][0])
  return (
    <div role="tablist" aria-label={label} className="tabs">
      {items.map(([id, text], i) => (
        <button
          key={id}
          type="button"
          role="tab"
          aria-selected={value === id}
          tabIndex={value === id ? 0 : -1}
          className={`tab ${small ? 'sm' : ''}`}
          onClick={() => onChange(id)}
          onKeyDown={(e) => {
            if (e.key === 'ArrowRight') move(i + 1)
            if (e.key === 'ArrowLeft') move(i - 1)
          }}
        >
          {text}
        </button>
      ))}
    </div>
  )
}
