import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from '../schema';

const dbRaw = new Database('stickies.db');
export const db = drizzle(dbRaw, { schema });
