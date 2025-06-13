import React, { useState } from 'react';
import { useStickies } from '../store';

export const FolderSidebar: React.FC = () => {
  const {
    folders,
    currentFolderId,
    setCurrentFolder,
    addFolder
  } = useStickies();
  const [newName, setNewName] = useState('');

  return (
    <aside
      style={{
        width: 180,
        borderRight: '1px solid #ddd',
        padding: 8,
        boxSizing: 'border-box'
      }}
    >
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {folders.map((f) => (
          <li key={f.id}>
            <button
              style={{
                background:
                  f.id === currentFolderId ? '#ffe8c4' : 'transparent',
                border: 'none',
                width: '100%',
                textAlign: 'left',
                padding: '4px 6px'
              }}
              onClick={() => setCurrentFolder(f.id)}
            >
              {f.name}
            </button>
          </li>
        ))}
      </ul>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (newName.trim()) {
            addFolder(newName.trim());
            setNewName('');
          }
        }}
      >
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="New folder…"
          style={{ width: '100%' }}
        />
      </form>
    </aside>
  );
};
