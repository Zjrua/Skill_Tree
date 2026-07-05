import { useState, useRef, useEffect } from 'react'
import { api } from './api'

interface Props {
  value: string
  onChange: (v: string) => void
  onSend: () => void
  onStop?: () => void                // 停止生成(streaming 时显示停止按钮)
  streaming?: boolean                // 正在生成中
  onCommand?: (cmd: string) => void   // 处理 /new 等命令
  placeholder?: string
}

const SYM_MAP: Record<string, string> = { '#': 'node', '@': 'resource', '$': 'dir' }
const SYM_LABEL: Record<string, string> = { '#': '节点', '@': '资源', '$': '方向' }

export function MentionInput({ value, onChange, onSend, onStop, streaming, onCommand, placeholder }: Props) {
  const [suggestions, setSuggestions] = useState<{ id: string; name: string }[]>([])
  const [activeSym, setActiveSym] = useState<string | null>(null)
  const [selIdx, setSelIdx] = useState(0)
  const debounceRef = useRef<number>(0)
  const taRef = useRef<HTMLTextAreaElement>(null)

  // 检测光标前的 #/@/$ + 前缀
  useEffect(() => {
    const m = value.match(/([#@$])([^\s#@$]*)$/)
    if (m) {
      const sym = m[1], pre = m[2]
      setActiveSym(sym)
      window.clearTimeout(debounceRef.current)
      debounceRef.current = window.setTimeout(async () => {
        try {
          const r = await api.chatSuggest(SYM_MAP[sym], pre)
          setSuggestions(r.items)
          setSelIdx(0)
        } catch { setSuggestions([]) }
      }, 150)
    } else {
      setActiveSym(null)
      setSuggestions([])
    }
  }, [value])

  const insertSuggestion = (item: { id: string; name: string }) => {
    // 在光标处替换 #/@/$ 前缀为符号+id,并恢复光标到插入点之后
    const ta = taRef.current
    const caret = ta ? ta.selectionStart : value.length
    const before = value.slice(0, caret)
    const after = value.slice(caret)
    const replaced = before.replace(/([#@$])[^\s#@$]*$/, `$1${item.id} `)
    if (replaced === before) return   // 光标前无匹配前缀,不插
    const newValue = replaced + after
    const newCaret = replaced.length
    onChange(newValue)
    setActiveSym(null)
    setSuggestions([])
    // 异步恢复光标(等 React 更新 textarea value 后)
    requestAnimationFrame(() => { ta?.focus(); ta?.setSelectionRange(newCaret, newCaret) })
  }

  const handleKey = (e: React.KeyboardEvent) => {
    // 补全弹层导航
    if (activeSym && suggestions.length > 0) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setSelIdx(i => (i + 1) % suggestions.length); return }
      if (e.key === 'ArrowUp') { e.preventDefault(); setSelIdx(i => (i - 1 + suggestions.length) % suggestions.length); return }
      if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault(); insertSuggestion(suggestions[selIdx]); return
      }
      if (e.key === 'Escape') { setActiveSym(null); setSuggestions([]); return }
    }
    // 发送 / 命令
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      const trimmed = value.trim()
      if (trimmed.startsWith('/') && onCommand) {
        onCommand(trimmed)
        onChange('')
      } else {
        onSend()
      }
    }
  }

  return (
    <div className="mention-wrap">
      {activeSym && suggestions.length > 0 && (
        <div className="mention-pop">
          <div className="mention-pop-title">{SYM_LABEL[activeSym]}</div>
          {suggestions.map((s, i) => (
            <div key={s.id} className={`mention-item ${i === selIdx ? 'active' : ''}`}
                 onClick={() => insertSuggestion(s)}>{s.name} <span className="mention-id">{s.id}</span></div>
          ))}
        </div>
      )}
      <textarea
        ref={taRef}
        className="ai-textarea"
        value={value}
        onChange={e => onChange(e.target.value)}
        onKeyDown={handleKey}
        rows={2}
        placeholder={placeholder || '问我… 用 #节点 @资源 $方向 引用，/new 开新会话'}
      />
      {streaming && onStop ? (
        <button className="aibtn ghost" onClick={onStop} title="停止生成">■ 停止</button>
      ) : (
        <button className="aibtn solid" onClick={onSend} disabled={!value.trim()}>发送 ▸</button>
      )}
    </div>
  )
}
