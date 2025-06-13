import { zipSync, unzipSync } from 'fflate'
import { encrypt, decrypt, deriveKey, generateSalt } from './crypto'
import { invoke } from '@tauri-apps/api/core'

export const exportAll = async (pass: string, data: unknown) => {
  const salt = generateSalt()
  const key = await deriveKey(pass, salt)
  const json = new TextEncoder().encode(JSON.stringify(data))
  const { cipher, nonce } = encrypt(json, key)
  const zipped = zipSync({ data: new Uint8Array([...cipher, ...nonce]) })
  const blob = new Blob([salt, zipped], { type: 'application/zip' })
  return blob
}

export const importAll = async (
  pass: string,
  blob: Blob
): Promise<unknown> => {
  const buf = new Uint8Array(await blob.arrayBuffer())
  const salt = buf.slice(0, 16) // first 16 bytes
  const zipped = buf.slice(16)
  const key = await deriveKey(pass, salt)
  const { data } = unzipSync(zipped) as { data: Uint8Array }
  const cipher = data.slice(0, -24)
  const nonce = data.slice(-24)
  const plain = decrypt(cipher, nonce, key)
  return JSON.parse(new TextDecoder().decode(plain))
}

// Tauri wrappers
export const exportToFile = async (pass: string) => {
  const data = await invoke('dump_all')
  const blob = await exportAll(pass, data)
  // @ts-ignore
  const handle = await window.showSaveFilePicker({
    suggestedName: 'stickies.zip'
  })
  const ws = await handle.createWritable()
  await ws.write(blob)
  await ws.close()
}

export const importFromFile = async (pass: string) => {
  // @ts-ignore
  const [file] = await window.showOpenFilePicker()
  const blobBuf = await (await file.getFile()).arrayBuffer()
  const data = await importAll(pass, new Blob([blobBuf]))
  await invoke('restore_all', { payload: data })
}
