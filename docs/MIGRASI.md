# Migrasi Database (Flask-Migrate / Alembic)

Perubahan skema dikelola lewat berkas versi di `migrations/versions/`, bukan lagi dengan mengedit SQL manual.

| Revisi | Isi |
|---|---|
| `0001` | Baseline: mengadopsi tabel dari `schema.sql` (tidak membuat tabel) |
| `0002` | Menambah kolom `description` pada `products` (contoh migrasi) |

## Instalasi
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Database baru
```bash
mysql -u root -p < schema.sql
flask --app app db upgrade
```

## Database lama (sudah berjalan, tabel sudah ada)
```bash
flask --app app db upgrade      # 0001 lolos, 0002 menambah kolom description
flask --app app db current      # harus menampilkan 0002 (head)
```

## Perintah yang sering dipakai
```bash
flask --app app db current                 # revisi aktif
flask --app app db history                 # daftar revisi
flask --app app db upgrade                 # naik ke revisi terbaru
flask --app app db downgrade               # turun satu revisi (hapus kolom description)
flask --app app db migrate -m "pesan"      # buat revisi baru otomatis dari perubahan models.py
```

## Demo untuk dosen
```bash
flask --app app db downgrade               # kolom description hilang
mysql -u root -p kamistore -e "DESCRIBE products;"
flask --app app db upgrade                 # kolom description muncul lagi
mysql -u root -p kamistore -e "DESCRIBE products;"
```

## Catatan
- `include_object` di `migrations/env.py` mengabaikan tabel yang belum punya model, jadi autogenerate tidak mencoba menghapus `orders`, `cart_items`, dan lainnya.
- Aplikasi lain (keranjang, pesanan, Midtrans, OTP) tetap memakai `db.py` dan berjalan di database yang sama.
