import React, { useState } from 'react';
import { Rnd } from 'react-rnd';
import { useStickies } from '../store';
import { RichEditor } from './RichEditor';
import { Note } from '../types';

interface Props {
  note: Note;
}

export const Sticky: React.FC<Props> = ({ note }) => {
  const { updateNote, removeNote } = useStickies();
  const [title, setTitle] = useState(note.title);

  return (
    <Rnd
      default={{
        x: note.x,
        y: note.y,
        width: note.width,
        height: note.height
      }}
      onDragStop={(_, d) =>
        updateNote({ id: note.id, x: d.x, y: d.y })
      }
      onResizeStop={(_, __, ref, ___, pos) =>
        updateNote({
          id: note.id,
          width: ref.offsetWidth,
          height: ref.offsetHeight,
          x: pos.x,
          y: pos.y
        })
      }
      bounds="window"
      style={{
        background: 'papayawhip',
        border: '1px solid #e2c8a4',
        boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <input
        value={title}
        onChange={(e) => {
          setTitle(e.target.value);
          updateNote({ id: note.id, title: e.target.value });
        }}
        placeholder="Title"
        style={{
          border: 'none',
          background: 'transparent',
          padding: '4px 8px',
          fontWeight: 'bold'
        }}
      />
      <div style={{ flex: 1, overflow: 'auto', padding: 8 }}>
        <RichEditor
          value={note.bodyEnc} // plaintext for now
          onChange={(html) =>
            updateNote({ id: note.id, bodyEnc: html })
          }
        />
      </div>
      <button
        onClick={() => removeNote(note.id)}
        style={{ alignSelf: 'flex-end', margin: 4 }}
      >
        🗑
      </button>
    </Rnd>
  );
};
