-- Tabel pendaftaran yang menunggu verifikasi OTP. Jalankan sebagai root MySQL:
--   sudo mysql kamistore < deploy/otp_table.sql
CREATE TABLE IF NOT EXISTS registration_otps (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email         VARCHAR(150) NOT NULL UNIQUE,
  name          VARCHAR(100) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  nonce         CHAR(32) NOT NULL,
  expires_at    DATETIME NOT NULL,
  attempts      TINYINT UNSIGNED NOT NULL DEFAULT 0,
  send_count    TINYINT UNSIGNED NOT NULL DEFAULT 1,
  last_sent_at  DATETIME NOT NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
