import { EditorContent, useEditor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import React from 'react';

interface Props {
  value: string;
  onChange: (html: string) => void;
}

export const RichEditor: React.FC<Props> = ({ value, onChange }) => {
  const editor = useEditor({
    extensions: [StarterKit],
    content: value,
    onUpdate({ editor }) {
      onChange(editor.getHTML());
    }
  });

  if (!editor) return null;
  return (
    <EditorContent
      editor={editor}
      style={{ height: '100%', outline: 'none' }}
    />
  );
};
