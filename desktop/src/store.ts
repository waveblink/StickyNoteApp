import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Folder, Note } from './types';
import { db } from './libs/dbBridge';

interface StickiesState {
  folders: Folder[];
  notes: Note[];
  currentFolderId: number | null;
  theme: string;
  // actions
  refresh: () => Promise<void>;
  addFolder: (name: string) => Promise<void>;
  removeFolder: (id: number) => Promise<void>;
  addNote: () => Promise<void>;
  updateNote: (patch: Partial<Note> & { id: number }) => Promise<void>;
  removeNote: (id: number) => Promise<void>;
  setCurrentFolder: (id: number) => void;
  setTheme: (t: string) => void;
}

export const useStickies = create<StickiesState>()(
  devtools((set, get) => ({
    folders: [],
    notes: [],
    currentFolderId: null,
    theme: 'parchment',

    refresh: async () => {
      const folders = await db.listFolders();
      const cf = get().currentFolderId ?? folders[0]?.id ?? null;
      const notes = cf ? await db.listNotes(cf) : [];
      set({ folders, notes, currentFolderId: cf });
    },

    addFolder: async (name) => {
      const folder = await db.createFolder(name);
      set((s) => ({ folders: [...s.folders, folder] }));
    },

    removeFolder: async (id) => {
      await db.deleteFolder(id);
      set((s) => ({
        folders: s.folders.filter((f) => f.id !== id),
        notes: s.notes.filter((n) => n.folderId !== id),
        currentFolderId:
          s.currentFolderId === id ? null : s.currentFolderId
      }));
    },

    addNote: async () => {
      const fid = get().currentFolderId;
      if (!fid) return;
      const note = await db.createNote(fid);
      set((s) => ({ notes: [...s.notes, note] }));
    },

    updateNote: async (patch) => {
      await db.updateNote(patch);
      set((s) => ({
        notes: s.notes.map((n) =>
          n.id === patch.id ? { ...n, ...patch } : n
        )
      }));
    },

    removeNote: async (id) => {
      await db.deleteNote(id);
      set((s) => ({
        notes: s.notes.filter((n) => n.id !== id)
      }));
    },

    setCurrentFolder: (id) => set({ currentFolderId: id }),

    setTheme: (t) => {
      document.documentElement.setAttribute('data-theme', t);
      set({ theme: t });
    }
  }))
);
