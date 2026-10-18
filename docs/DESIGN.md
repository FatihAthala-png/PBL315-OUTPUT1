---
name: KAMISTORE Design System
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#45464d'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#855300'
  on-secondary: '#ffffff'
  secondary-container: '#fea619'
  on-secondary-container: '#684000'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#410004'
  on-tertiary-container: '#ef4444'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#ffddb8'
  secondary-fixed-dim: '#ffb95f'
  on-secondary-fixed: '#2a1700'
  on-secondary-fixed-variant: '#653e00'
  tertiary-fixed: '#ffdad7'
  tertiary-fixed-dim: '#ffb3ad'
  on-tertiary-fixed: '#410004'
  on-tertiary-fixed-variant: '#930013'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '800'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  title-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0em
  price-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '800'
    lineHeight: 28px
    letterSpacing: -0.02em
  price-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '700'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.04em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.06em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

# KAMISTORE Design System

Dokumen ini menjelaskan tampilan yang **benar-benar dipakai** di kode (`templates/`, `static/`). Token di bagian frontmatter di atas sama dengan konfigurasi Tailwind di `static/js/app.js` (nama kelas seperti `bg-surface`, `text-on-surface`, `font-heading`). Selain token itu, halaman memakai kelas bawaan Tailwind (`slate`, `blue`, `red`) yang dijelaskan di bawah.

## Brand & Gaya

KAMISTORE adalah toko kurasi Pokémon TCG dan action figure asli Jepang untuk pasar Indonesia. Tampilannya bersih, terang, dan ramah: latar putih kebiruan, kartu putih dengan border tipis, dan aksen **biru** serta **merah** yang kuat. Logo memakai kombinasi merah "KAMI" dan biru "STORE", dan pola ini diulang di judul halaman.

- Nuansa: cerah, rapi, mudah dipindai. Tidak ada tema gelap pada halaman utama.
- Hiasan khas: bentuk geometris berwarna (lengkung merah, roda gigi kuning, tangga hijau dan pink) pada bagian Welcome, serta panel pink untuk "Most Popular Items".
- Interaksi: transisi 300 ms, kartu terangkat saat hover, gambar membesar pelan (`scale-105`).

## Warna

| Peran | Nilai | Dipakai untuk |
|---|---|---|
| Latar halaman (`surface`) | `#f8f9ff` | Background `body` |
| Kartu / panel | `#ffffff` | Kartu produk, filter, form |
| Border | `slate-200` | Border kartu dan panel |
| Teks utama | `on-surface` `#0b1c30`, `slate-900` | Judul, harga |
| Teks sekunder | `slate-600` / `slate-500` | Nama produk, keterangan |
| **Biru** `blue-600` / `blue-700` | `#2563eb` / `#1d4ed8` | Tombol aksi, link, kategori produk, filter terpilih |
| Biru muda `sky-100` | `#e0f2fe` | Tombol "Add to cart", chip filter aktif |
| **Merah** `red-600` / `red-500` | `#dc2626` / `#ef4444` | Aksen judul, badge diskon, wishlist aktif, Reset |
| Kuning | `#ffec99`, `amber-400` | Banner Welcome, bintang rating |
| Footer | `primary-container` `#131b2e` | Latar footer (satu-satunya area gelap) |

Aturan pakai:
- Satu halaman = satu aksen utama. Judul memakai teks gelap dengan **satu kata merah** (contoh: "Shop By **Category**", "All **Product**").
- Biru untuk hal yang bisa diklik dan dipilih; merah hanya untuk diskon, peringatan, dan status aktif seperti wishlist.
- Warna amber/oranye lama sudah tidak dipakai di katalog.

## Tipografi

- **Plus Jakarta Sans** (`font-heading`): judul, nama bagian, harga, tombol penting. Bobot 700–800.
- **Inter**: teks isi, deskripsi, label formulir.
- Ukuran judul halaman: `text-2xl` di HP, `text-3xl` di desktop, `font-extrabold`.
- Nama produk: `text-sm`, maksimal 2 baris (`line-clamp-2`). Harga: `font-heading text-base font-bold`.
- Label kecil (filter, badge): `text-xs` atau `text-[10px]–[11px]`, huruf kapital dengan `tracking-wider` untuk judul kelompok filter.
- Ikon memakai **Material Symbols Outlined**; ikon terisi (hati aktif, bintang) lewat `material-symbols-filled`.

## Tata Letak & Spasi

- Kontainer: `max-w-7xl mx-auto px-6 lg:px-12` pada setiap section, jadi tepi kiri-kanan selalu sejajar.
- Header `fixed` setinggi sekitar 128 px (desktop) atau 168 px (HP), sehingga `main` diberi `pt-32` / `pt-[10.5rem]`.
- Jarak antar section memakai token `space-md` (1 rem), `space-lg` (1.5 rem), `space-xl` (2.5 rem).
- **Katalog (All Product)**: grid 12 kolom. Sidebar filter 3 kolom (sticky, `top-36`), produk 9 kolom. Kartu 2 kolom di HP, 2 kolom di tablet, 3 kolom di `xl`. Di bawah `lg` sidebar disembunyikan dan dibuka lewat tombol **Filter**.
- **Beranda**: Hero (carousel + 2 banner) → Welcome → Most Popular Items (carousel horizontal) → Shop By Category (tab + grid 2–3 kolom).

## Bentuk & Elevasi

- Kartu produk, kartu kategori, panel filter, bar filter aktif: `rounded-2xl` + `border border-slate-200` + latar putih.
- Input, tombol, dropdown: `rounded-xl` atau `rounded-lg`.
- Chip filter aktif: `rounded-full`.
- Kartu login/register: `rounded-[2rem]` dengan `shadow-xl`.
- Hover kartu: naik 4 px (`-translate-y-1`), border menjadi `slate-300`, bayangan `0 16px 36px rgba(15,23,42,0.12)`.
- Header: putih 95% + `backdrop-blur-xl` dan bayangan tipis; footer gelap.

## Komponen

### Header & Navigasi
Logo di kiri, kolom pencarian di tengah, ikon wishlist / akun / keranjang di kanan. Menu (**Beranda / Promo**, **All Product**, **Cek Resi & Pesanan**) berada di baris kedua dan bisa digeser horizontal di HP. Menu aktif: latar `#d3e4fe`, teks `#0b1c30`, bobot 600 (kelas `.nav-button.active`).

### Kartu Produk
Dipakai di katalog dan konsisten dengan kartu di Beranda (`partials/product-card.html`).
- Area gambar `h-44 md:h-52`, gradasi `slate-50` ke putih, gambar `object-contain`.
- Badge (mis. BEST SELLER) di kiri atas: `bg-slate-900/85`, teks putih, 10 px kapital.
- Tombol wishlist (hati) di kanan atas: `text-slate-500`, saat aktif `text-red-500` dengan ikon terisi.
- Info: kategori (`text-xs font-bold text-blue-600`) dan stok, nama produk, rating (bintang `amber-400`), harga coret + badge `% OFF` merah bila ada diskon, lalu harga.
- Tombol **Add to cart**: `bg-sky-100 text-blue-700`, hover `sky-200`. Setelah diklik berubah menjadi biru solid "Ditambahkan!" selama 1,8 detik.
- Mode **List**: kartu menjadi horizontal (gambar 13 rem di kiri) di layar `sm` ke atas.

### Toolbar Katalog
Judul "All **Product**", tombol Filter (HP), pilihan tampilan Grid / List (aktif: `bg-blue-600 text-white`), lalu bar putih berisi chip **Filter Aktif**, jumlah hasil, dan dropdown urutan (Populer, Harga naik/turun, Terbaru, Rating).

### Sidebar Filter
Panel putih `rounded-2xl`, header "Filter Koleksi" dengan ikon `tune` biru dan tombol Reset merah. Kelompok: Jenis Produk, Kategori (mengikuti jenis yang dipilih), Rentang Harga, Ketersediaan, Card Rarity & Grade, Brand & Produsen. Setiap kelompok dipisah garis `slate-100`.
- Checkbox memakai `accent-blue-600` dengan jumlah produk di kanan.
- Chip rarity: tidak terpilih `slate-50`, terpilih `bg-blue-600 text-white`.
- Slider harga ganda: jalur `slate-200`, bagian terpilih `blue-600`, thumb putih berborder `#2563eb`. Ada input Min/Max berawalan "Rp" dan preset (<100rb, 100rb–500rb, 500rb–1,5jt, >1,5jt).
- Filter juga bisa dipilih lewat URL, mis. `/semua-produk?type=tcg`.

### Tombol
- **Aksi utama**: `bg-blue-600 text-white`, hover `blue-700` (contoh: "Jelajahi Sekarang").
- **Sekunder**: `border border-blue-600 text-blue-600`, hover terisi biru (contoh: "See All Products", "Reset Filter").
- **Aksi cepat dalam kartu**: `bg-sky-100 text-blue-700` (Add to cart).
- **Teks bahaya/reset**: `text-red-600`, hover garis bawah.

### Form Login & Register
Kartu putih besar dua kolom (logo di kiri, form di kanan). Judul "**Login**" dengan aksen merah dan biru. Input memakai label mengambang, `rounded-xl`, `border-slate-300`, fokus `border-red-600` dengan ring `red-100`. Pada register, kata sandi harus minimal 8 karakter dan memuat huruf besar, huruf kecil, angka, dan simbol.

### Carousel & Banner
Hero memakai carousel 3 slide (titik indikator putih, panah bulat putih) dan dua banner di kanan. Most Popular Items berupa carousel scroll horizontal dengan snap, kartu selebar 14–15 rem.

### Footer
Latar `#131b2e`, teks `slate-300/400`, judul kolom putih kapital, kolom: info toko, Navigasi Kolektor, serta logo mitra Pembayaran (BCA, BNI, BRI, Mandiri, QRIS) dan Pengiriman (JNE, J&T, SiCepat).

## Aksesibilitas & Responsif

- Titik henti: HP (default), `sm` 640, `md` 768, `lg` 1024, `xl` 1280.
- Tombol ikon wajib punya `aria-label`. Menu aktif memakai `aria-current="page"`, wishlist memakai `aria-pressed`.
- Fokus terlihat pada input (ring) dan chip rarity (`peer-focus-visible:ring-2`).
- Hindari menyampaikan status hanya dengan warna: diskon selalu disertai teks `% OFF`, wishlist aktif juga mengubah ikon menjadi terisi.