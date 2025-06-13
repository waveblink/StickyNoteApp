import { invoke } from '@tauri-apps/api/core';
import { Note, Folder } from '../types';

export const db = {
  // FOLDERS
  listFolders: async (): Promise<Folder[]> =>
    invoke('list_folders'),
  createFolder: async (name: string): Promise<Folder> =>
    invoke('create_folder', { name }),
  deleteFolder: async (id: number): Promise<void> =>
    invoke('delete_folder', { id }),

  // NOTES
  listNotes: async (folderId: number): Promise<Note[]> =>
    invoke('list_notes', { folderId }),
  createNote: async (folderId: number): Promise<Note> =>
    invoke('create_note', { folderId }),
  updateNote: async (note: Partial<Note> & { id: number }): Promise<void> =>
    invoke('update_note', { note }),
  deleteNote: async (id: number): Promise<void> =>
    invoke('delete_note', { id })
};
