# KAMISTORE

Toko online Pokémon TCG dan action figure. Dibuat dengan Flask, MySQL, dan Jinja2 sebagai proyek PBL.

Repo: https://github.com/FatihAthala-png/PBL_315-OUTPUT1

## Fitur

- **Katalog**: beranda dan halaman `/semua-produk`, dengan pencarian, filter, dan urutan. Data produk dibaca dari database.
- **Register dengan verifikasi OTP**: kode 6 digit dikirim ke email. Akun baru dibuat setelah kode benar.
- **Login**: sandi di-hash, ada pembatasan percobaan gagal, dan semua kejadian login dicatat di log.
- **Manajemen produk (CRUD)**: tambah, ubah, nonaktifkan/aktifkan, dan hapus produk di panel admin. Produk yang pernah dipesan hanya bisa dinonaktifkan.
- **Dashboard admin**: hanya bisa dibuka akun dengan role `admin`. Pengguna biasa mendapat 403, pengunjung tanpa login diarahkan ke halaman login.
- **Profil dan reset sandi**: pengguna bisa mengubah profil dan memulihkan akun lewat halaman lupa sandi.
- **Wishlist, keranjang, checkout, pesanan, dan pelacakan**, dengan pembayaran lewat Midtrans.

## Teknologi

| Bagian | Yang dipakai |
|---|---|
| Framework | Flask (struktur blueprint) |
| Database | MySQL |
| ORM | Flask-SQLAlchemy (model `User` dan `Product`) |
| Migration | Flask-Migrate (Alembic) |
| Template | Jinja2 |
| Keamanan | Flask-WTF (CSRF), hash sandi scrypt (werkzeug), batas percobaan login, OTP email (pyotp) |
| Pembayaran | Midtrans |
| Server | gunicorn + systemd |

## Struktur proyek

```
app.py                  perakit aplikasi, mendaftarkan 15 blueprint
extensions.py           objek db (SQLAlchemy) dan migrate
models.py               kelas User dan Product
security.py             dekorator login_required dan admin_required
logging_config.py       pengaturan logging (konsol dan file, dengan rotasi)
ratelimit.py            pembatas percobaan login dan OTP
store_config.py         konfigurasi toko
otp_flow.py             alur verifikasi OTP saat register
mailer.py               pengiriman email
midtrans.py             integrasi pembayaran Midtrans
blueprints/             route per bagian (auth, shop, admin, admin_produk, cart, dst.)
services/               UserService dan ProductService (akses data)
templates/              base.html, partials/, admin/
static/                 css, js (register.js, login.js, filter.js), gambar
migrations/versions/    0001 baseline, 0002 tambah kolom description
schema.sql              skema awal database
seed.py                 mengisi 12 produk awal (dari data/products.json) dan akun admin
smoke_*.py              skrip uji manual per modul (jalan di database asli, hati-hati)
docs/                   dokumentasi tambahan
deploy/                 kamistore.service (systemd)
gunicorn.conf.py        konfigurasi gunicorn
```

## Arsitektur singkat

Alur permintaan: **route (blueprint)** menerima request, memanggil **service**, service memakai **model**, dan model terhubung ke **tabel database**.

Catatan: SQLAlchemy dan migration baru diterapkan untuk `User` dan `Product`. Keranjang, pesanan, dan pembayaran masih memakai query langsung lewat `db.py` pada database yang sama, dan akan dipindahkan bertahap.

## Cara menjalankan

### 1. Clone dan siapkan environment

```bash
git clone https://github.com/FatihAthala-png/PBL_315-OUTPUT1.git
cd PBL_315-OUTPUT1
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Isi file `.env`

Salin contoh lalu isi nilainya:

```bash
cp .env.example .env
```

| Variabel | Keterangan |
|---|---|
| `SECRET_KEY` | Wajib. Aplikasi gagal start kalau kosong. Isi dengan string acak yang panjang. |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Koneksi ke MySQL |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Akun admin yang dibuat oleh `seed.py` |
| `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD` | SMTP untuk mengirim kode OTP |
| `OTP_REGISTER` | Isi `0` untuk mematikan OTP. Kalau tidak diisi, OTP aktif selama SMTP terkonfigurasi. |
| `COOKIE_SECURE` | Isi `1` kalau diakses lewat HTTPS |
| `LOG_LEVEL`, `LOG_DIR`, `LOG_TO_FILE` | Pengaturan logging (opsional) |

File `.env` tidak boleh di-commit. File ini sudah masuk `.gitignore`.

### 3. Siapkan database

```bash
mysql -u root -p < schema.sql        # membuat tabel dasar
flask --app app db upgrade           # menjalankan migration sampai 0002
python seed.py                       # 12 produk awal dan akun admin
```

Urutannya penting. Migration `0001` hanya baseline untuk skema dari `schema.sql`, jadi tabel dasar harus dibuat dulu.

### 4. Jalankan aplikasi

Mode pengembangan:

```bash
python app.py
```

Mode server (gunicorn, port 8000 secara bawaan):

```bash
gunicorn -c gunicorn.conf.py app:app
```

Di server, aplikasi dijalankan lewat systemd dengan nama service `kamistore`:

```bash
sudo systemctl status kamistore
sudo systemctl restart kamistore      # setelah mengubah .env
```

## Migration

```bash
flask --app app db current       # revisi aktif, seharusnya 0002 (head)
flask --app app db history       # riwayat revisi
flask --app app db upgrade       # maju ke revisi terbaru
```

| Revisi | Isi |
|---|---|
| `0001` | Baseline, mengadopsi skema dari `schema.sql` |
| `0002` | Menambah kolom `description` pada tabel `products` |

Hati-hati dengan `flask db downgrade`: perintah ini menghapus kolom `description` beserta isinya.

## Logging

Log tampil di konsol dan tersimpan di `logs/kamistore.log` (rotasi 1 MB, 5 cadangan). Kejadian yang dicatat antara lain `LOGIN_OK`, `LOGIN_FAILED`, `RATE_LIMITED`, `OTP_VERIFY`, dan `ADMIN_ACTION`. Sandi tidak pernah dicatat.

```bash
tail -f logs/kamistore.log
```

## Keamanan

- Sandi disimpan sebagai hash scrypt, tidak pernah sebagai teks asli.
- Validasi dilakukan di browser dan diulang di server.
- Proteksi CSRF di seluruh aplikasi.
- Sesi dibuat ulang saat login (mencegah session fixation).
- Pesan gagal login sengaja umum agar daftar email terdaftar tidak bocor.
- Kode OTP tidak disimpan di database. Kode dihitung ulang dari `SECRET_KEY`, email, dan nonce.
- Akses admin dijaga dekorator `admin_required`, dan role dibaca dari database pada setiap request.

Batasan yang diketahui: penghitung rate limit dan OTP disimpan di memori proses, jadi hilang saat service di-restart dan hanya akurat dengan satu worker gunicorn.

## Akun awal

Akun admin dibuat oleh `seed.py` dari `ADMIN_EMAIL` dan `ADMIN_PASSWORD` di `.env`. Pengguna yang mendaftar lewat halaman register otomatis berperan `customer`.

## Tim

Kelompok PBL 315, Politeknik Negeri Batam.

| Nama | Bagian | Branch |
|---|---|---|
| Imam | Fondasi, database, keamanan, logging, migrasi, deployment, dokumentasi | `chore/fondasi-dan-docs` |
| Fatih | Login, register, profil, OTP, verifikasi email, reset sandi | `feat/auth-dan-profil` |
| Rai | Beranda, katalog, detail produk, wishlist, UI bersama | `feat/etalase-katalog` |
| Danar | Keranjang, checkout, pesanan, pelacakan, pembayaran Midtrans | `feat/keranjang-checkout-pesanan` |
| Alya | Panel admin, manajemen produk/pengguna/pesanan/laporan, media | `feat/panel-admin` |

## Alur kontribusi

- Jangan push langsung ke `main`. Satu tugas satu branch, lalu buka Pull Request.
- Minimal 1 review sebelum merge (Squash and merge).
- Stage file satu per satu, hindari `git add .`.
- Jangan commit `.env`, password, token, atau API key.
- Perubahan model/tabel, dependensi, atau konfigurasi lintas modul dibahas di grup dulu.

## Lisensi

Proyek ini dibuat untuk keperluan perkuliahan PBL, Politeknik Negeri Batam.
