stOrm-py3 Bot - Python 3 Edition


https://img.shields.io/badge/Python-3.8%252B-blue.svg
https://img.shields.io/badge/License-GPL_v2-orange.svg
https://img.shields.io/badge/XMPP-slixmpp-green.svg

stOrm adalah bot XMPP multiguna yang awalnya dibuat dalam Python 2 menggunakan pustaka xmpppy. Proyek ini adalah porting penuh ke Python 3 dengan pustaka modern slixmpp.

Bot mampu:

Berada di banyak room MUC sekaligus.

Menjalankan perintah langsung tanpa prefix (cukup ketik help, ping, access, dll).

Manajemen akses bertingkat (global dan per-room, level -100 hingga 100).

Remote command (remote) untuk menjalankan perintah di room lain.

Redirect hasil perintah ke pengguna privat (redirect).

Superadmin massal (fullban, fullunban, fullmember, fullunmember) di semua room.

Dan banyak lagi.

🚀 Fitur Utama
Tanpa prefix: command diketik langsung (tanpa !).

Plugin system: tambah fitur hanya dengan meletakkan file .py di folder plugins/.

Multi-room: bergabung otomatis dari file chatrooms.list, bisa join/leave kapan saja.

Akses granular: level akses dari -100 (diabaikan) sampai 100 (bot admin).

Remote & redirect: jalankan command di room lain, kirim hasil ke user privat.

Global message: globmsg ke semua room yang mengizinkan.

Auto-restart: opsional, hidupkan lewat config.json.

Lebih aman: semua konfigurasi dan data disimpan dalam JSON, bukan eval().

📋 Persyaratan
Python 3.8 atau lebih baru

pip terbaru

Koneksi ke server XMPP (akun bot)

🔧 Instalasi Cepat
bash
# 1. Clone repositori atau salin folder proyek
git clone <url-repo> storm-py3
cd storm-py3

# 2. Install pustaka yang diperlukan
python3 -m pip install --upgrade pip
python3 -m pip install slixmpp

# 3. Salin config contoh dan sesuaikan
cp config.example.json config.json   # atau buat config.json sendiri
nano config.json                     # isi dengan kredensial bot Anda

# 4. (Opsional) Siapkan daftar room
mkdir dynamic
echo '{"room@conference.example.com": {"nick": "stOrm", "passw": ""}}' > dynamic/chatrooms.list

# 5. Jalankan bot
python3 bot.py
Bot akan login, bergabung dengan room yang terdaftar di dynamic/chatrooms.list, dan siap menerima perintah.

🛠️ Pengembangan
Kode bersih, terstruktur, dan banyak komentar (dalam bahasa Indonesia).

Gunakan logging.DEBUG jika ingin melihat log detail.

Seluruh data disimpan di folder dynamic/ dalam format JSON.

Plugin asli dari Python 2 sudah dikonversi dan tersedia di plugins/.

📄 Lisensi
Program ini dilisensikan di bawah GNU General Public License v2.
Lihat file LICENSE atau kunjungi https://www.gnu.org/licenses/old-licenses/gpl-2.0.html.

🙏 Kredit
Original Bot: Mike Mintz, Als, dimichxp, Boris Kotov.

Python 3 Port: Komunitas & kontributor modern.

Library XMPP: slixmpp.
