-- Isi deskripsi produk (aman diulang: tidak menimpa deskripsi yang sudah diisi admin).
-- Jalankan:  mysql -u kamistore_app -p --default-character-set=utf8mb4 kamistore < deploy/product_descriptions.sql
SET NAMES utf8mb4;

UPDATE products SET description = 'Booster bundle Pokémon TCG Scarlet & Violet—151 edisi bahasa Inggris, segel pabrik. Set ini mengangkat 151 Pokémon generasi pertama (Kanto) dengan ilustrasi kartu bernuansa nostalgia, jadi cocok untuk kolektor maupun pemain.\n\n• Edisi Inggris, segel rapat\n• Berisi beberapa booster pack dalam satu bundle\n• Peluang menarik kartu langka bertema Kanto'
  WHERE id = 1 AND (description IS NULL OR description = '');
UPDATE products SET description = 'Kartu Charizard ex Special Art Rare (SAR) nomor 199/165 dari set Scarlet & Violet—151. Termasuk kartu paling dicari di set ini berkat ilustrasi penuh yang detail. Kondisi mint dan belum di-grade (raw), disimpan dengan sleeve dan toploader.\n\n• Nomor kartu: 199/165\n• Rarity: Special Art Rare (SAR)\n• Kondisi: Mint, belum di-grade (raw)\n• Stok sangat terbatas'
  WHERE id = 2 AND (description IS NULL OR description = '');
UPDATE products SET description = 'Elite Trainer Box (ETB) edisi Crown Zenith, set penutup era Sword & Shield. Satu paket lengkap untuk memulai atau menambah koleksi: berisi booster pack, perlengkapan bermain, dan kotak penyimpanan kartu.\n\n• Isi umum ETB: booster pack, sleeve kartu, kartu energi, dadu, dan penanda kondisi\n• Kotak bisa dipakai menyimpan kartu\n• Segel pabrik'
  WHERE id = 3 AND (description IS NULL OR description = '');
UPDATE products SET description = 'Figure skala 1/8 ARTFX J dari Kotobukiya bertema Red dan Pikachu, produk resmi. Dibuat dari PVC pre-painted dengan detail pose dan warna yang rapi, cocok untuk dipajang di rak koleksi.\n\n• Skala 1/8, produk resmi Kotobukiya\n• Material PVC pre-painted, siap pajang\n• Disarankan disimpan jauh dari sinar matahari langsung'
  WHERE id = 4 AND (description IS NULL OR description = '');
UPDATE products SET description = 'Nendoroid Pokémon Trainer Cynthia (Shirona) lengkap dengan Garchomp dari Good Smile Company. Bentuk chibi khas Nendoroid dengan bagian yang bisa dilepas dan diganti, sehingga ekspresi dan pose bisa diubah-ubah. Produk pre-order, stok datang sesuai jadwal batch.\n\n• Status: Pre-Order\n• Wajah dan aksesori bisa diganti\n• Produk resmi Good Smile Company'
  WHERE id = 5 AND (description IS NULL OR description = '');
UPDATE products SET description = 'Booster box Pokémon TCG Terastal Festival (SV8a) edisi Jepang, segel pabrik. Set ini menghadirkan Pokémon ex bertema Terastal dan banyak kartu ilustrasi spesial yang diburu kolektor. Produk pre-order.\n\n• Edisi Jepang (bahasa Jepang), segel pabrik\n• Berisi banyak booster pack dalam satu box\n• Status: Pre-Order'
  WHERE id = 6 AND (description IS NULL OR description = '');
UPDATE products SET description = 'Kartu Mewtwo VSTAR Secret Rare (SAR) nomor 221 dari set VSTAR Universe edisi Jepang. Ilustrasi penuh yang dramatis membuatnya menjadi salah satu kartu favorit kolektor. Kondisi mint, belum di-grade (raw).\n\n• Nomor kartu: 221\n• Edisi Jepang\n• Kondisi: Mint, belum di-grade (raw)'
  WHERE id = 7 AND (description IS NULL OR description = '');
UPDATE products SET description = 'S.H.Figuarts Ash Ketchum (Satoshi) bersama Pikachu dari Bandai Tamashii Nations. Action figure artikulasi tinggi, jadi bisa dipasang dalam banyak pose dinamis seperti di serial animasinya.\n\n• Artikulasi (sendi) bisa digerakkan untuk berbagai pose\n• Disertai Pikachu\n• Produk resmi Bandai'
  WHERE id = 8 AND (description IS NULL OR description = '');
UPDATE products SET description = 'Kartu promo Pikachu with Grey Felt Hat dari kolaborasi Pokémon dengan Van Gogh Museum, kondisi sealed. Kartu promo yang sangat diminati kolektor karena distribusinya terbatas. Hanya tersisa satu.\n\n• Kartu promo kolaborasi Van Gogh Museum\n• Kondisi sealed\n• Stok tinggal 1'
  WHERE id = 9 AND (description IS NULL OR description = '');
UPDATE products SET description = 'Satu booster pack Scarlet & Violet—Paldean Fates, segel pabrik. Set ini terkenal dengan banyaknya Pokémon Shiny, cocok untuk dibuka satuan atau menambah koleksi dengan harga terjangkau.\n\n• Dijual satuan (single pack), segel pabrik\n• Set bertema Pokémon Shiny\n• Harga terjangkau untuk mencoba peruntungan'
  WHERE id = 10 AND (description IS NULL OR description = '');
UPDATE products SET description = 'Figure Pop Up Parade Red (Pokémon Masters EX) dari Good Smile Company. Seri Pop Up Parade dikenal dengan harga lebih terjangkau namun tetap rapi dan detail, pas untuk melengkapi koleksi figure.\n\n• Produk resmi Good Smile Company\n• Material PVC\n• Cocok untuk koleksi pemula maupun lanjutan'
  WHERE id = 11 AND (description IS NULL OR description = '');
UPDATE products SET description = 'Binder Ultra PRO bergambar Pikachu dengan halaman 9 kantong (9-pocket) untuk kartu ukuran standar. Melindungi kartu dari debu dan lecet sekaligus memudahkan pameran koleksi.\n\n• 9 kantong per halaman, untuk kartu ukuran standar\n• Cocok untuk kartu Pokémon TCG\n• Produk resmi Ultra PRO'
  WHERE id = 12 AND (description IS NULL OR description = '');
