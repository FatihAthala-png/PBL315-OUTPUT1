CREATE DATABASE IF NOT EXISTS kamistore
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE kamistore;

-- ---------------------------------------------------------------- users
CREATE TABLE IF NOT EXISTS users (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(100) NOT NULL,
  email         VARCHAR(150) NOT NULL UNIQUE,
  phone         VARCHAR(20)  NULL,
  avatar_path   VARCHAR(255) NULL,
  password_hash VARCHAR(255) NOT NULL,
  role          ENUM('customer','admin') NOT NULL DEFAULT 'customer',
  is_active     TINYINT(1) NOT NULL DEFAULT 1,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------- products
-- price = harga jual saat ini (sudah termasuk diskon).
-- Harga coret dihitung di aplikasi dari discount_percent.
-- rarity = daftar dipisah koma, mis. 'sar,psa10'.
CREATE TABLE IF NOT EXISTS products (
  id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name             VARCHAR(200) NOT NULL,
  image_url        VARCHAR(500) NOT NULL,
  category         VARCHAR(100) NOT NULL,          -- label kecil di kartu
  type             ENUM('tcg','figure') NOT NULL,
  sub              VARCHAR(50)  NOT NULL DEFAULT '',
  brand            VARCHAR(50)  NOT NULL DEFAULT '',
  rarity           VARCHAR(100) NOT NULL DEFAULT '',
  price            INT UNSIGNED NOT NULL,
  discount_percent TINYINT UNSIGNED NULL,
  stock            INT UNSIGNED NOT NULL DEFAULT 0,
  stock_unit       VARCHAR(20)  NOT NULL DEFAULT '',
  rating           DECIMAL(2,1) NOT NULL DEFAULT 0.0,
  review_count     INT UNSIGNED NOT NULL DEFAULT 0,
  badge            VARCHAR(30)  NULL,
  is_preorder      TINYINT(1) NOT NULL DEFAULT 0,
  is_active        TINYINT(1) NOT NULL DEFAULT 1,
  created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                   ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_products_type_sub (type, sub),
  INDEX idx_products_active (is_active)
) ENGINE=InnoDB;

-- ------------------------------------------------------------ cart_items
CREATE TABLE IF NOT EXISTS cart_items (
  id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id    INT UNSIGNED NOT NULL,
  product_id INT UNSIGNED NOT NULL,
  qty        INT UNSIGNED NOT NULL DEFAULT 1,
  added_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_cart_user_product (user_id, product_id),
  FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- --------------------------------------------------------------- orders
-- Alamat disimpan sebagai salinan (snapshot) supaya riwayat pesanan
-- tidak berubah kalau user mengganti data nanti.
CREATE TABLE IF NOT EXISTS orders (
  id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  order_no       VARCHAR(30) NOT NULL UNIQUE,      -- mis. KMS-261008-0001
  user_id        INT UNSIGNED NOT NULL,
  status         ENUM('menunggu_pembayaran','menunggu_approval','diproses',
                      'dikirim','selesai','dibatalkan')
                 NOT NULL DEFAULT 'menunggu_pembayaran',
  recipient_name VARCHAR(100) NOT NULL,
  phone          VARCHAR(20)  NOT NULL,
  address        VARCHAR(300) NOT NULL,
  city           VARCHAR(100) NOT NULL,
  province       VARCHAR(100) NOT NULL,
  postal_code    VARCHAR(10)  NOT NULL,
  courier        VARCHAR(50)  NULL,
  service        VARCHAR(30)  NULL,
  resi           VARCHAR(50)  NULL,
  subtotal       INT UNSIGNED NOT NULL,
  shipping_cost  INT UNSIGNED NOT NULL DEFAULT 0,
  total          INT UNSIGNED NOT NULL,
  created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                 ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_orders_user (user_id),
  INDEX idx_orders_status (status),
  INDEX idx_orders_resi (resi),
  FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS order_items (
  id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  order_id     INT UNSIGNED NOT NULL,
  product_id   INT UNSIGNED NOT NULL,
  product_name VARCHAR(200) NOT NULL,              -- snapshot nama
  unit_price   INT UNSIGNED NOT NULL,              -- snapshot harga
  qty          INT UNSIGNED NOT NULL,
  FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB;

-- Riwayat perjalanan pesanan (dipakai halaman Cek Resi & Pesanan).
CREATE TABLE IF NOT EXISTS order_status_history (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  order_id    INT UNSIGNED NOT NULL,
  title       VARCHAR(150) NOT NULL,
  description VARCHAR(300) NOT NULL DEFAULT '',
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_history_order (order_id),
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------- payments
-- Satu pesanan bisa punya beberapa upload kalau sebelumnya ditolak.
CREATE TABLE IF NOT EXISTS payments (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  order_id      INT UNSIGNED NOT NULL,
  method        VARCHAR(30)  NOT NULL,             -- BCA / Mandiri / QRIS
  amount        INT UNSIGNED NOT NULL,
  proof_path    VARCHAR(255) NOT NULL,
  status        ENUM('menunggu','disetujui','ditolak') NOT NULL DEFAULT 'menunggu',
  reject_reason VARCHAR(255) NULL,
  reviewed_by   INT UNSIGNED NULL,
  reviewed_at   TIMESTAMP NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_payments_status (status),
  FOREIGN KEY (order_id)    REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (reviewed_by) REFERENCES users(id)  ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reviews (
  id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  product_id INT UNSIGNED NOT NULL,
  user_id    INT UNSIGNED NOT NULL,
  rating     TINYINT UNSIGNED NOT NULL,          -- 1 sampai 5
  comment    VARCHAR(1000) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_review_user_product (product_id, user_id),
  INDEX idx_reviews_product (product_id),
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE
) ENGINE=InnoDB;