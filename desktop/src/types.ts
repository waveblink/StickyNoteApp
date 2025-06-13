export interface Folder {
  id: number;
  name: string;
  createdAt: number;
}

export interface Note {
  id: number;
  title: string;
  bodyEnc: string; // encrypted string; plaintext lives only in editor state
  folderId: number;
  pinned: boolean;
  x: number;
  y: number;
  width: number;
  height: number;
  createdAt: number;
  updatedAt: number;
  remindAt?: number | null;
}
