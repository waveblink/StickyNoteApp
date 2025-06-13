import chrono from 'chrono-node'
import { Notification } from '@tauri-apps/api/notification'
import { Note } from '../types'

export const parseReminder = (text: string): number | null => {
  const res = chrono.parseDate(text)
  return res ? res.getTime() : null
}

export const scheduleReminder = (note: Note) => {
  if (!note.remindAt) return
  const delay = note.remindAt - Date.now()
  if (delay <= 0) return
  setTimeout(() => {
    new Notification('Cosy Stickies', {
      body: note.title || 'Reminder'
    }).show()
  }, delay)
}
