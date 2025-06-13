/* eslint-disable camelcase */
import sodium from 'libsodium-wrappers-sumo';

await sodium.ready;

const ALG = {
  saltBytes: sodium.crypto_pwhash_SALTBYTES,
  keyBytes: sodium.crypto_aead_aes256gcm_KEYBYTES,
  nonceBytes: sodium.crypto_aead_aes256gcm_NPUBBYTES
};

export const generateSalt = (): Uint8Array =>
  sodium.randombytes_buf(ALG.saltBytes);

export const deriveKey = async (
  passphrase: string,
  salt: Uint8Array
): Promise<Uint8Array> =>
  sodium.crypto_pwhash(
    ALG.keyBytes,
    passphrase,
    salt,
    sodium.crypto_pwhash_OPSLIMIT_MODERATE,
    sodium.crypto_pwhash_MEMLIMIT_MODERATE,
    sodium.crypto_pwhash_ALG_ARGON2ID13
  );

export const encrypt = (
  plaintext: Uint8Array,
  key: Uint8Array
): { cipher: Uint8Array; nonce: Uint8Array } => {
  const nonce = sodium.randombytes_buf(ALG.nonceBytes);
  let cipher: Uint8Array;

  if (sodium.crypto_aead_aes256gcm_is_available()) {
    cipher = sodium.crypto_aead_aes256gcm_encrypt(
      plaintext,
      null,
      null,
      nonce,
      key
    );
  } else {
    // Fallback → XChaCha20-Poly1305 (still 256-bit)
    cipher = sodium.crypto_aead_xchacha20poly1305_ietf_encrypt(
      plaintext,
      null,
      null,
      nonce,
      key
    );
  }
  return { cipher, nonce };
};

export const decrypt = (
  cipher: Uint8Array,
  nonce: Uint8Array,
  key: Uint8Array
): Uint8Array => {
  if (sodium.crypto_aead_aes256gcm_is_available()) {
    return sodium.crypto_aead_aes256gcm_decrypt(
      null,
      cipher,
      null,
      nonce,
      key
    );
  }
  return sodium.crypto_aead_xchacha20poly1305_ietf_decrypt(
    null,
    cipher,
    null,
    nonce,
    key
  );
};
