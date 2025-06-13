import React from 'react'
import { useStickies } from '../store'

export const ThemeSwitcher: React.FC = () => {
  const { theme, setTheme } = useStickies()
  return (
    <select
      value={theme}
      onChange={e => setTheme(e.target.value)}
      style={{ marginLeft: 8 }}
    >
      <option value="parchment">Parchment</option>
      <option value="dark">Dark</option>
      <option value="cyber">Cyberpunk</option>
    </select>
  )
}
