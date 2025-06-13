import React, { useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { useStickies } from '../store';
import { FolderSidebar } from '../components/FolderSidebar';
import { Sticky } from '../components/Sticky';

const App = () => {
  const { refresh, notes, addNote } = useStickies();

  useEffect(() => {
    refresh();
  }, []);

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <FolderSidebar />
      <main style={{ flex: 1, position: 'relative' }}>
        {notes.map((n) => (
          <Sticky key={n.id} note={n} />
        ))}
        <button
          onClick={() => addNote()}
          style={{ position: 'absolute', top: 10, right: 10 }}
        >
          ➕ New note
        </button>
      </main>
    </div>
  );
};

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
