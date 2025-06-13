export const debounce = <A extends unknown[]>(fn: (...args: A) => void, ms = 400) => {
  let t: ReturnType<typeof setTimeout>
  return (...args: A) => {
    clearTimeout(t)
    t = setTimeout(() => fn(...args), ms)
  }
}
