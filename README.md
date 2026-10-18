# KAMISTORE

KAMISTORE adalah aplikasi web e-commerce yang dikembangkan menggunakan Flask untuk menyediakan katalog produk Pokémon TCG dan Action Figure.

Project ini dibuat sebagai bagian dari PBL 315 dengan fokus pada pengembangan aplikasi toko online yang memiliki katalog produk, pencarian, filter, autentikasi pengguna, dan informasi pengiriman.

## Fitur

### Beranda

* Hero section dan banner promosi
* Produk populer
* Kategori produk
* Informasi toko
* Navigasi utama

### Katalog Produk

* Menampilkan daftar produk
* Kategori Pokémon TCG dan Action Figure
* Pencarian produk
* Filter produk
* Pengurutan produk
* Informasi harga, rating, dan ketersediaan
* Tampilan grid dan list

### Autentikasi

* Registrasi pengguna
* Login pengguna
* Password hashing
* Validasi data pengguna

### Tracking Pesanan

* Informasi pesanan
* Nomor resi
* Status pengiriman
* Riwayat perjalanan paket

### Interface

* Responsive design
* Navigasi yang sederhana
* Komponen produk yang konsisten
* Tampilan yang dapat digunakan pada desktop maupun perangkat mobile

## Teknologi

Project ini menggunakan beberapa teknologi berikut:

| Teknologi       | Penggunaan                   |
| --------------- | ---------------------------- |
| Python          | Bahasa pemrograman utama     |
| Flask           | Web framework                |
| HTML            | Struktur halaman             |
| CSS             | Styling dan layout           |
| JavaScript      | Interaksi pada halaman       |
| Jinja2          | Template engine Flask        |
| JSON            | Penyimpanan data produk      |
| MySQL Connector | Persiapan integrasi database |

## Struktur Project

```text
PBL315/
│
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
│
├── data/
│   └── products.json
│
├── docs/
│   └── DESIGN.md
│
├── static/
│   ├── css/
│   │   ├── auth.css
│   │   └── style.css
│   │
│   ├── js/
│   │   ├── app.js
│   │   ├── categories.js
│   │   ├── filter.js
│   │   ├── hero.js
│   │   ├── login.js
│   │   ├── popular.js
│   │   └── register.js
│   │
│   └── images/
│       ├── logo2.png
│       ├── logo3.png
│       ├── welcome.png
│       ├── b1.png
│       ├── b2.png
│       └── ...
│
└── templates/
    ├── base.html
    ├── index.html
    ├── catalog.html
    ├── login.html
    ├── register.html
    ├── tracking.html
    │
    └── partials/
        ├── header.html
        ├── footer.html
        ├── hero.html
        ├── product-card.html
        ├── catalog-content.html
        ├── catalog-filters.html
        ├── catalog-toolbar.html
        ├── categories.html
        ├── popular-items.html
        ├── trust-features.html
        └── welcome.html
```

## Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/FatihAthala-png/PBL_315-OUTPUT1.git
```

Masuk ke direktori project:

```bash
cd PBL_315-OUTPUT1
```

### 2. Membuat Virtual Environment

Windows:

```bash
python -m venv venv
```

Aktifkan virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependency

```bash
pip install -r requirements.txt
```

### 4. Menjalankan Aplikasi

```bash
python app.py
```

Kemudian buka browser dan akses:

```text
http://127.0.0.1:5000
```

## Data Produk

Data produk saat ini disimpan dalam file:

```text
data/products.json
```

File tersebut digunakan oleh aplikasi sebagai sumber data katalog produk.

Project juga memiliki dependency `mysql-connector-python` sebagai persiapan untuk pengembangan integrasi database MySQL.

## Dokumentasi Design

Dokumentasi desain tersedia pada:

```text
docs/DESIGN.md
```

Dokumentasi tersebut mencakup:

* Color system
* Typography
* Layout
* Spacing
* Komponen UI
* Product card
* Header dan navigation
* Catalog filter
* Responsive design

## Keamanan

Beberapa aspek keamanan yang diterapkan dalam project:

* Password diproses menggunakan password hashing.
* Password tidak disimpan dalam bentuk teks biasa.
* File konfigurasi sensitif dapat dikecualikan melalui `.gitignore`.
* Data pengguna pada contoh pesanan tidak menggunakan informasi sensitif secara langsung.

## Pengembangan Selanjutnya

Pengembangan yang dapat dilakukan pada versi berikutnya:

1. Integrasi database MySQL secara penuh.
2. Sistem keranjang dan checkout.
3. Integrasi payment gateway.
4. Penyimpanan wishlist ke database.
5. Integrasi API tracking jasa pengiriman.
6. Dashboard admin.
7. Manajemen produk dan stok.
8. Sistem manajemen pesanan.
9. Peningkatan sistem autentikasi dan authorization.

## Repository

Repository project:

```text
https://github.com/FatihAthala-png/PBL_315-OUTPUT1
```

## Project

**KAMISTORE**

PBL 315
E-Commerce Web Application
