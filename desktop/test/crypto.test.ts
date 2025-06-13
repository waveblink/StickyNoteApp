import { describe, expect, it } from 'vitest';
import {
  deriveKey,
  encrypt,
  decrypt,
  generateSalt
} from '../src/libs/crypto';

describe('crypto util', () => {
  it('encrypts and decrypts symmetrically', async () => {
    const salt = generateSalt();
    const key = await deriveKey('hunter2', salt);
    const data = new TextEncoder().encode('secret parchment');
    const { cipher, nonce } = encrypt(data, key);
    const plain = decrypt(cipher, nonce, key);
    expect(new TextDecoder().decode(plain)).toBe('secret parchment');
  });
});
