import {
  sqliteTable,
  integer,
  text,
  real
} from 'drizzle-orm/sqlite-core';

export const folders = sqliteTable('folders', {
  id: integer('id').primaryKey(),
  name: text('name').notNull(),
  createdAt: real('created_at').notNull()
});

export const notes = sqliteTable('notes', {
  id: integer('id').primaryKey(),
  title: text('title').notNull(),
  bodyEnc: text('body_enc').notNull(), // encrypted markdown / html
  folderId: integer('folder_id')
    .references(() => folders.id)
    .notNull(),
  pinned: integer('pinned', { mode: 'boolean' }).notNull().default(false),
  x: integer('x').notNull().default(100),
  y: integer('y').notNull().default(100),
  width: integer('width').notNull().default(280),
  height: integer('height').notNull().default(220),
  createdAt: real('created_at').notNull(),
  updatedAt: real('updated_at').notNull()
});

export const reminders = sqliteTable('reminders', {
  id: integer('id').primaryKey(),
  noteId: integer('note_id')
    .references(() => notes.id)
    .notNull(),
  remindAt: real('remind_at').notNull(),
  done: integer('done', { mode: 'boolean' }).notNull().default(false)
});

export const settings = sqliteTable('settings', {
  id: integer('id').primaryKey(), // always 1
  theme: text('theme').notNull().default('parchment'),
  fontSize: integer('font_size').notNull().default(16),
  hotkey: text('hotkey').notNull().default('Ctrl+Shift+Space'),
  salt: text('salt').notNull() // base64 for key derivation
});
