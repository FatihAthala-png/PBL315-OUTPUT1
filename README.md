# PBL_315-OUTPUT1 — PokéVault Flask

Aplikasi web e-commerce monolitik berbasis Flask, Tailwind CSS, JavaScript, dan MySQL untuk penjualan Pokémon TCG dan action figure.

## Cara Menjalankan Aplikasi

Pastikan Python 3 sudah terpasang. Buka terminal pada folder proyek, lalu jalankan perintah berikut:

```bash
pip install -r requirements.txt
python app.py
```

Setelah aplikasi berjalan, buka alamat berikut di browser:

`http://127.0.0.1:5000`

## Struktur Utama

* `app.py`: file utama untuk menjalankan aplikasi Flask.
* `requirements.txt`: daftar pustaka Python yang dibutuhkan.
* `templates/`: halaman HTML menggunakan Jinja dan komponen partial.
* `templates/partials/product-card.html`: template kartu produk yang digunakan bersama.
* `data/products.json`: data produk contoh sementara.
* `static/`: tempat menyimpan file CSS, JavaScript, dan gambar.
* `docs/`: dokumentasi dan rancangan proyek.

## Pengembangan Database

Saat MySQL sudah siap digunakan, fungsi `get_products()` pada `app.py` dapat diubah agar mengambil data dari tabel produk di database.

Template kartu produk tidak perlu diubah selama nama kolom atau data yang dikirimkan tetap sesuai dengan kebutuhan template.
