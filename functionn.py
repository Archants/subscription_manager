import pandas as pd

import csv
from datetime import datetime, date, timedelta
from pathlib import Path


pathfile = Path(r"data\budi.csv")
template = ['Nama', 'Biaya', 'Metode Pembayaran','Tanggal Pembayaran', 'Tanggal Jatuh Tempo', 'Status']    




# Fungsi template file
def filetemplate(pathfile) -> None:
    with pathfile.open(mode='w+', newline='') as file:
        tulis = csv.writer(file)
        tulis.writerow(template)


# Fungsi untuk mengubah Status menjadi "Nonaktif" jika hari ini sudah melewati Tanggal Jatuh Tempo
def ubah_status(pathfile):
    df = pd.read_csv(pathfile, index_col='Nama')
    df['Tanggal Jatuh Tempo'] = pd.to_datetime(df['Tanggal Jatuh Tempo']).dt.date
    df.loc[df['Tanggal Jatuh Tempo'] < date.today(), 'Status'] = 'Nonaktif'
    df.to_csv(pathfile, index=True)


# Fungsi untuk menambah subscription baru
def add_subscription(pathfile, data: dict) -> None:

    data['Status'] = "Aktif" if data['Tanggal Jatuh Tempo'] > date.today() else "Nonaktif"

    with open(pathfile, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=template)
        writer.writerow(data)

"""
nama = input('Nama: ')
biaya = float(input('Biaya: '))
metpem = input('Metode Pembayaran: ')
tanggal_pembayaran = date.fromisoformat(input('Tanggal Pembayaran (YYYY-MM-DD): '))
tanggal_jatuh_tempo = date.fromisoformat(input('Tanggal Jatuh Tempo(YYYY-MM-DD): '))
data = {key: value for key, value in zip(template, [nama, biaya, metpem, tanggal_pembayaran, tanggal_jatuh_tempo])}
add_subscription(pathfile, data)
"""


# Fungsi untuk menghapus baris berdasarkan kolom "Nama"
def delete_data(pathfile, nama_subscription: str) -> None:
    # Baca file
    df = pd.read_csv(pathfile, index_col="Nama")
    # Hapus baris  
    df.drop(index=nama_subscription, inplace=True)
    # Simpan perubahan ke file .csv  
    df.to_csv(pathfile, index=True) 


# Fungsi untuk memodifikasi kolom tertentu pada baris berdasarkan kolom "Nama"
def update_data(pathfile, nama_subscription: str, nama_kolom: str, nilai_baru) -> None:

    df = pd.read_csv(pathfile, index_col="Nama")
    # Update data yang dimakusd
    if nama_kolom != "Nama":
        df.loc[nama_subscription, nama_kolom] = nilai_baru
    else:
        df.rename(index={nama_subscription: nilai_baru}, inplace=True)

    # Simpan perubahan ke file .csv
    df.to_csv(pathfile, index=True)




# Fungsi untuk mencari baris data berdasarkan kolom "Nama" dengan sequential search
def sequential_search_data(pathfile, kata_kunci) -> list[dict]:

    with open(pathfile, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    hasil = []
    # sequential search: periksa setiap baris satu per satu
    for row in rows:          
        if row['Nama'] == kata_kunci:
            hasil.append(row)

    return hasil



# Fungsi untuk mencari baris data dengan binary search berdasarkan kolom "Nama"
def binary_search_data(pathfile, kata_kunci) -> list[dict | None]:

    # Baca dan salin isi file .csv
    with open(pathfile, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        rows = list(reader) # list of dictionary

    # Urutkan isi file berdasarkan kolom "Nama" (syarat binary search)
    rows.sort(key=lambda row: row['Nama'])

    ## Operasi pencarian dengan algoritma binary search
    kiri, kanan = 0, len(rows) - 1
    indeks_ditemukan = -1

    while kiri <= kanan:
        tengah = (kiri + kanan) // 2
        nama_tengah = rows[tengah]['Nama']

        if nama_tengah == kata_kunci:
            indeks_ditemukan = tengah
            break
        elif nama_tengah < kata_kunci:
            kiri = tengah + 1
        else:
            kanan = tengah - 1

    if indeks_ditemukan == -1:
        return [None]

    return [rows[indeks_ditemukan]]



# Fungsi untuk mengurutkan data dengan algoritma insertion sort (berdasarkan kolom "Nama", "Biaya" atau "Tanggal Jatuh Tempo")
def insertion_sort_data(pathfile, tipe='ascending', kolom='Nama') -> None:

    # konversi nilai kolom ke tipe yang sesuai agar perbandingan benar
    def konversi(row): # -> mengembalikan nilai kolom yang dimaksud dengan tipe data yang sesuai
        nilai = row[kolom]
        if kolom == 'Biaya':
            return float(nilai)
        elif kolom == "Tanggal Jatuh Tempo" or kolom == "Tanggal Pembayaran":
            return date.fromisoformat(nilai)
        else:
            return str(nilai)

    # Baca dan salin isi file .csv untuk disorting
    with open(pathfile, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        rows = list(reader) # list of dictionary

    # Opersi sorting dengan algoritma insertion sort
    for i in range(1, len(rows)):
        kunci = rows[i]
        j = i - 1
        if tipe == 'ascending':
            # geser elemen yang lebih besar ke kanan, sisipkan kunci di posisi yang tepat
            while j >= 0 and konversi(rows[j]) > konversi(kunci):  # type: ignore
                rows[j + 1] = rows[j]
                j -= 1
        elif tipe == 'descending':
            # geser elemen yang lebih kecil ke kanan, sisipkan kunci di posisi yang tepat
            while j >= 0 and konversi(rows[j]) < konversi(kunci):  # type: ignore
                rows[j + 1] = rows[j]
                j -= 1
        rows[j + 1] = kunci


    # Tulis kembali data ke file .csv
    with open(pathfile, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=template)
        writer.writeheader()
        writer.writerows(rows)



# Fungsi untuk mengurutkan data dengan algoritma selection sort (berdasarkan kolom "Nama", "Biaya" atau "Tanggal Jatuh Tempo")
def selection_sort_data(pathfile, tipe='ascending', kolom='Nama') -> None:

    def konversi(row):
        nilai = row[kolom]
        if kolom == 'Biaya':
            return float(nilai)
        elif kolom == 'Tanggal Jatuh Tempo' or kolom == 'Tanggal Pembayaran':
            return date.fromisoformat(nilai)
        else:
            return str(nilai)

    with open(pathfile, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    n = len(rows)
    for i in range(n):
        idx_ekstrem = i
        for j in range(i + 1, n):
            if tipe == 'ascending':
                # cari nilai minimum dari sisa elemen, taruh di posisi i
                if konversi(rows[j]) < konversi(rows[idx_ekstrem]):  # type: ignore
                    idx_ekstrem = j
            elif tipe == 'descending':
                # cari nilai maksimum dari sisa elemen, taruh di posisi i
                if konversi(rows[j]) > konversi(rows[idx_ekstrem]):  # type: ignore
                    idx_ekstrem = j
        rows[i], rows[idx_ekstrem] = rows[idx_ekstrem], rows[i]

    with open(pathfile, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=template)
        writer.writeheader()
        writer.writerows(rows)



## Untuk menampilkan data subscription aktif dan apakah di bayar bulan ini atau tidak
def subscription_aktif(pathfile):
    df = pd.read_csv(pathfile)
    df['Biaya'] = pd.to_numeric(df['Biaya'])
    df['Tanggal Pembayaran'] = pd.to_datetime(df['Tanggal Pembayaran'])
    df_aktif = df[df['Status'] == 'Aktif'].copy()

    bulan_ini = date.today().month
    tahun_ini = date.today().year

    df_aktif['Dibayar Bulan Ini'] = (
        (df_aktif['Tanggal Pembayaran'].dt.month == bulan_ini) &
        (df_aktif['Tanggal Pembayaran'].dt.year  == tahun_ini)
    )

    return df_aktif[['Nama', 'Biaya', 'Dibayar Bulan Ini']]


## Fungsi untuk menghitung total pengeluaran bulan ini (subscription yang di bayar bulan ini saja)
def total_pengeluaran_bulan_ini(pathfile):
    df = pd.read_csv(pathfile)
    df['Biaya'] = pd.to_numeric(df['Biaya'])
    df['Tanggal Pembayaran'] = pd.to_datetime(df['Tanggal Pembayaran'])

    bulan_ini = date.today().month
    tahun_ini = date.today().year

    df_bulan_ini = df[
        (df['Tanggal Pembayaran'].dt.month == bulan_ini) &
        (df['Tanggal Pembayaran'].dt.year  == tahun_ini)
    ]
    return float(df_bulan_ini['Biaya'].sum())


## Fungsi untuk menampilkan subscription yang mendekati jatuh tempo (misal: dalam 7 hari ke depan)
def mendekati_jatuh_tempo(pathfile, hari_sebelum: int=7 ) -> list[dict]:
    df = pd.read_csv(pathfile)
    df['Tanggal Jatuh Tempo'] = pd.to_datetime(df['Tanggal Jatuh Tempo']).dt.date

    today = date.today()
    batas = today + timedelta(days=hari_sebelum)

    df_pengingat = df[
        (df['Status'] == 'Aktif') &
        (df['Tanggal Jatuh Tempo'] >= today) &
        (df['Tanggal Jatuh Tempo'] <= batas)
    ]

    return df_pengingat[['Nama', 'Biaya', 'Tanggal Jatuh Tempo']].to_dict('records') # list of dictionary


## Fungsi untuk memberi rekomendasi subscription yang sebaiknya dihentikan (biaya di atas rata-rata) dan total potensi penghematan jika dihentikan semua subscription tersebut
def rekomendasi_berhenti(pathfile):
    df = pd.read_csv(pathfile)
    df['Biaya'] = pd.to_numeric(df['Biaya'])
    df_aktif = df[df['Status'] == 'Aktif'].copy()

    if df_aktif.empty:
        return []

    rata_rata = df_aktif['Biaya'].mean()
    df_rekomendasi = (df_aktif[df_aktif['Biaya'] > rata_rata]
                      .sort_values('Biaya', ascending=False))

    total_bisa_hemat = float(df_rekomendasi['Biaya'].sum())

    return {
        'rekomendasi': df_rekomendasi[['Nama', 'Biaya']].to_dict('records'),
        'potensi_hemat': total_bisa_hemat
    }