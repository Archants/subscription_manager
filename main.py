import tkinter as tk
from tkinter import ttk
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter
from pathlib import Path
from datetime import date
from functionn import *

# ── Konstanta ──────────────────────────────────────────────────────────────────
pathfile = Path(r"data\budi.csv")

BG, SURFACE, PANEL = '#F5F1E8', '#FFFFFF', '#FBF8F1'
BORDER, BORDER_D   = '#E3DBC9', '#C9BFA8'
TEXT, MUTED, DIM   = '#2C2620', '#8A7E6A', '#B3A88F'
ACCENT, ACCENT_S   = '#A8421C', '#C5572A'
OK, DANGER         = '#4F7A3D', '#A83333'

F_TITLE      = ('Georgia',  22)
F_H2         = ('Georgia',  15)
F_BODY       = ('Segoe UI', 11)
F_LABEL      = ('Segoe UI', 10)
F_LABEL_BOLD = ('Segoe UI', 10, 'bold')
F_CAPS       = ('Segoe UI',  9, 'bold')
F_ITAL       = ('Segoe UI', 11, 'italic')
F_BUTTON     = ('Segoe UI', 11, 'bold')
F_MONO       = ('Consolas', 10)
F_MONO_LG    = ('Consolas', 22)

PLACEHOLDER = "Cari nama subscription…"
COLS     = ('Nama', 'Biaya', 'Metode Pembayaran',
            'Tanggal Pembayaran', 'Tanggal Jatuh Tempo', 'Status')
COL_DISP = ('Nama', 'Biaya', 'Metode Pembayaran',
            'Tgl Pembayaran', 'Jatuh Tempo', 'Status')
COL_W    = [180, 120, 150, 112, 112, 90]


# ── Utilitas ───────────────────────────────────────────────────────────────────
def validasi_tanggal(s):
    try:    date.fromisoformat(s); return True
    except: return False

def _format_biaya(raw):
    try:    return f"Rp {float(str(raw)):,.0f}".replace(",", ".")
    except: return str(raw)

def _parse_biaya(s):
    try:    return str(int(s.replace('Rp ', '').replace('.', '').strip()))
    except: return s


# ── Tabel kustom (Canvas, warna per-sel + garis grid) ─────────────────────────
class TableCanvas(tk.Frame):
    _PX, _RH, _HH = 12, 38, 36

    def __init__(self, parent, columns, col_display, col_widths, **kw):
        super().__init__(parent, **kw)
        self.columns, self.col_display, self.col_widths = columns, col_display, col_widths
        self._items, self._order = {}, []
        self._sel, self._n, self._pending = None, 0, False

        self._cv = tk.Canvas(self, bg=SURFACE, highlightthickness=0)
        self._sb = ttk.Scrollbar(self, orient='vertical', command=self._cv.yview)
        self._cv.configure(yscrollcommand=self._sb.set)
        self._sb.pack(side='right', fill='y')
        self._cv.pack(side='left', fill='both', expand=True)
        self._cv.bind('<Configure>', lambda e: self._schedule())
        self._cv.bind('<Button-1>',  self._click)
        self._cv.bind('<MouseWheel>',
                      lambda e: self._cv.yview_scroll(-1*(e.delta//120), 'units'))

    # API kompatibel dengan ttk.Treeview
    def tag_configure(self, *a, **kw): pass
    def get_children(self):  return list(self._order)
    def selection(self):     return (self._sel,) if self._sel else ()
    def item(self, iid):     return {'values': list(self._items.get(iid, []))}

    def delete(self, iid):
        self._items.pop(iid, None)
        if iid in self._order: self._order.remove(iid)
        if self._sel == iid:   self._sel = None
        self._schedule()

    def insert(self, parent, index, values=(), tags=()):
        iid = f'I{self._n:05d}'; self._n += 1
        self._items[iid] = list(values)
        self._order.append(iid)
        self._schedule()
        return iid

    def _schedule(self):
        if not self._pending:
            self._pending = True
            self._cv.after_idle(self._flush)

    def _flush(self):
        self._pending = False
        self._draw()

    def _widths(self):
        total = self._cv.winfo_width() or sum(self.col_widths)
        ws = [max(60, int(cw * total / sum(self.col_widths))) for cw in self.col_widths]
        ws[-1] = total - sum(ws[:-1])
        return ws

    def _draw(self):
        cv, today = self._cv, date.today()
        cv.delete('all')
        ws = self._widths()
        xs = [sum(ws[:i]) for i in range(len(ws) + 1)]
        W  = xs[-1]

        # Header
        cv.create_rectangle(0, 0, W, self._HH, fill=PANEL, outline='')
        for i, disp in enumerate(self.col_display):
            mid = self.columns[i] in ('Biaya', 'Status')
            cv.create_text(xs[i] + (ws[i]//2 if mid else self._PX), self._HH // 2,
                           text=disp, anchor='center' if mid else 'w',
                           font=F_CAPS, fill=MUTED)

        # Baris data
        for r, iid in enumerate(self._order):
            vals   = self._items[iid]
            y0, y1 = self._HH + r*self._RH, self._HH + (r+1)*self._RH
            cv.create_rectangle(0, y0, W, y1,
                                fill=BORDER if iid == self._sel else SURFACE,
                                outline='', tags=iid)
            for i, (col, val) in enumerate(zip(self.columns, vals)):
                if col == 'Status':
                    s = str(val).lower()
                    fg = OK if ('aktif' in s and 'non' not in s) else DANGER
                elif col == 'Tanggal Jatuh Tempo':
                    try:    fg = DANGER if date.fromisoformat(str(val)) < today else TEXT
                    except: fg = TEXT
                else:
                    fg = TEXT
                mid = col in ('Biaya', 'Status')
                cv.create_text(xs[i] + (ws[i]//2 if mid else self._PX), (y0+y1)//2,
                               text=str(val), anchor='center' if mid else 'w',
                               font=('Georgia', 11), fill=fg, tags=iid)

        # Garis horizontal (digambar terakhir agar tidak tertimpa background)
        total_h = self._HH + len(self._order) * self._RH
        cv.create_line(0, self._HH, W, self._HH, fill=BORDER_D, width=2)
        for r in range(len(self._order)):
            y = self._HH + (r+1) * self._RH
            cv.create_line(0, y, W, y, fill=BORDER_D, width=1)
        cv.configure(scrollregion=(0, 0, W, total_h))

    def _click(self, event):
        y = self._cv.canvasy(event.y)
        if y < self._HH: return
        r = int((y - self._HH) / self._RH)
        if 0 <= r < len(self._order):
            iid = self._order[r]
            self._sel = None if self._sel == iid else iid
            self._draw()


# ── Dialog dasar ───────────────────────────────────────────────────────────────
def _show_dialog(title, message, parent=None, yesno=False, is_error=False):
    result = [False]
    par = parent or root
    dlg = tk.Toplevel(par)
    dlg.title(title); dlg.configure(bg=BG)
    dlg.resizable(False, False); dlg.grab_set(); dlg.transient(par)

    pad = tk.Frame(dlg, bg=BG, padx=24, pady=20)
    pad.pack(fill='both', expand=True)
    tk.Label(pad, text=title, font=F_H2, bg=BG, fg=TEXT).pack(anchor='w')
    tk.Frame(pad, height=1, bg=BORDER).pack(fill='x', pady=(8, 14))
    tk.Label(pad, text=message, font=F_BODY, bg=BG, fg=TEXT,
             wraplength=320, justify='left').pack(anchor='w')
    tk.Frame(pad, height=1, bg=BORDER).pack(fill='x', pady=(14, 10))

    btn = tk.Frame(pad, bg=BG); btn.pack(anchor='e')
    if yesno:
        def _yes(): result[0] = True; dlg.destroy()
        ttk.Button(btn, text="Ya",    command=_yes,        style='Primary.TButton').pack(side='left', padx=(0, 8))
        ttk.Button(btn, text="Tidak", command=dlg.destroy, style='Secondary.TButton').pack(side='left')
    else:
        ttk.Button(btn, text="OK", command=dlg.destroy,
                   style='Danger.TButton' if is_error else 'Primary.TButton').pack()

    dlg.update_idletasks()
    w = max(dlg.winfo_reqwidth(), 360); h = dlg.winfo_reqheight()
    dlg.geometry(f"{w}x{h}+{par.winfo_x()+(par.winfo_width()-w)//2}"
                 f"+{par.winfo_y()+(par.winfo_height()-h)//2}")
    par.wait_window(dlg)
    return result[0]

def _info(t, m, parent=None):  _show_dialog(t, m, parent)
def _error(t, m, parent=None): _show_dialog(t, m, parent, is_error=True)
def _yesno(t, m, parent=None): return _show_dialog(t, m, parent, yesno=True)


# ── Data & dashboard ───────────────────────────────────────────────────────────
def load_treeview(data=None):
    for iid in tree.get_children():
        tree.delete(iid)

    if data is None:
        try:    rows = [list(r) for _, r in pd.read_csv(pathfile).iterrows()]
        except: rows = []
    else:
        rows = [[row.get(c, '') for c in COLS] for row in data if row]

    for vals in rows:
        d = list(vals)
        d[1] = _format_biaya(vals[1])
        d[5] = str(vals[5]).strip().lower() if len(vals) > 5 else ''
        tree.insert('', 'end', values=d)

    try:    grand = len(pd.read_csv(pathfile))
    except: grand = len(rows)
    shown = len(rows)
    label_count.config(text=(f"Menampilkan {shown} subscription" if data is None
                              else f"Menampilkan {shown} dari {grand} subscription"))


def update_dashboard():
    ax.clear()
    try:    df = subscription_aktif(pathfile)
    except: df = pd.DataFrame()
    fig.patch.set_facecolor(BG); ax.set_facecolor(SURFACE)

    if df.empty:
        ax.text(0.5, 0.5, "Belum ada subscription aktif.", ha='center', va='center',
                transform=ax.transAxes, fontsize=12, color=MUTED,
                fontstyle='italic', fontfamily='Segoe UI')
        for s in ax.spines.values(): s.set_visible(False)
        ax.set_xticks([]); ax.set_yticks([])
        canvas.draw()
        label_total.config(text="Rp 0")
        label_aktif_count.config(text="dari 0 langganan aktif")
        for w in frame_rekom.winfo_children(): w.destroy()
        tk.Label(frame_rekom, text="Tidak ada rekomendasi",
                 font=F_ITAL, bg=PANEL, fg=MUTED).pack(anchor='center')
        return

    warna = [ACCENT if x else BORDER_D for x in df['Dibayar Bulan Ini']]
    bars  = ax.bar(df['Nama'], df['Biaya'], color=warna, width=0.55)
    ax.bar_label(bars, labels=[_format_biaya(v) for v in df['Biaya']],
                 padding=4, fontsize=9, color=TEXT, fontfamily='Segoe UI')
    ax.set_title("Biaya Subscription Aktif", fontfamily='Georgia',
                 fontsize=14, color=TEXT, fontweight='normal', pad=12)
    ax.set_ylabel("Biaya (Rp)", fontsize=9, color=MUTED, fontfamily='Segoe UI')
    ax.tick_params(axis='x', rotation=15, labelcolor=MUTED, labelsize=10)
    ax.tick_params(axis='y', labelcolor=MUTED, labelsize=9)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _format_biaya(v)))
    ax.grid(axis='y', color=BORDER_D, linewidth=0.6, alpha=0.5)
    ax.grid(axis='x', visible=False); ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False);  ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(BORDER);  ax.spines['bottom'].set_color(BORDER)
    ax.legend(handles=[Patch(color=ACCENT,   label='Dibayar bulan ini'),
                       Patch(color=BORDER_D, label='Bulan sebelumnya')],
              frameon=False, loc='upper right', fontsize=9, labelcolor=MUTED)
    fig.tight_layout(); canvas.draw()

    label_total.config(text=_format_biaya(total_pengeluaran_bulan_ini(pathfile)))
    label_aktif_count.config(text=f"dari {len(df)} langganan aktif")

    hasil = rekomendasi_berhenti(pathfile)
    for w in frame_rekom.winfo_children(): w.destroy()
    if isinstance(hasil, dict) and hasil.get('rekomendasi'):
        for item in hasil['rekomendasi']:
            fr = tk.Frame(frame_rekom, bg=PANEL); fr.pack(fill='x', pady=2)
            tk.Label(fr, text=item['Nama'],
                     font=F_BODY, bg=PANEL, fg=TEXT, anchor='w').pack(side='left')
            tk.Label(fr, text=_format_biaya(item['Biaya']),
                     font=F_MONO, bg=PANEL, fg=DANGER).pack(side='right')
        tk.Label(frame_rekom,
                 text=f"Hemat {_format_biaya(hasil['potensi_hemat'])}/bln",
                 font=F_BUTTON, bg=PANEL, fg=OK).pack(anchor='w', pady=(8, 0))
    else:
        tk.Label(frame_rekom, text="Tidak ada rekomendasi",
                 font=F_ITAL, bg=PANEL, fg=MUTED).pack(anchor='center')


# ── Aksi toolbar ──────────────────────────────────────────────────────────────
def klik_cari():
    raw = entry_search.get().strip()
    kw  = '' if raw == PLACEHOLDER else raw
    if not kw: load_treeview(); return
    fn    = sequential_search_data if combo_metode_search.get() == "Sequential" else binary_search_data
    hasil = fn(pathfile, kw)
    if not hasil or hasil == [None]:
        _info("Tidak Ditemukan", f"'{kw}' tidak ditemukan."); load_treeview()
    else:
        load_treeview(data=hasil)

def klik_sort():
    fn = insertion_sort_data if combo_algo_sort.get() == "Insertion Sort" else selection_sort_data
    fn(pathfile, tipe=combo_tipe_sort.get().lower(), kolom=combo_kolom_sort.get())
    load_treeview()

def klik_hapus():
    sel = tree.selection()
    if not sel: _info("Peringatan", "Pilih subscription yang ingin dihapus."); return
    nama = tree.item(sel[0])['values'][0]
    if _yesno("Konfirmasi Hapus", f"Hapus subscription '{nama}'?"):
        delete_data(pathfile, nama); load_treeview(); update_dashboard()

def klik_ubah():
    sel = tree.selection()
    if not sel: _info("Peringatan", "Pilih subscription yang ingin diubah."); return
    buka_dialog_ubah(tree.item(sel[0])['values'])


# ── Pembangun dialog form ──────────────────────────────────────────────────────
def _buat_dialog(title_window, title_dalam):
    dlg = tk.Toplevel(root)
    dlg.title(title_window); dlg.geometry("420x368")
    dlg.resizable(False, False); dlg.grab_set(); dlg.transient(root)
    dlg.configure(bg=BG)
    pad = tk.Frame(dlg, bg=BG, padx=24, pady=20)
    pad.pack(fill='both', expand=True); pad.columnconfigure(1, weight=1)
    tk.Label(pad, text=title_dalam, font=F_H2, bg=BG, fg=TEXT).grid(
        row=0, column=0, columnspan=3, sticky='w', pady=(0, 4))
    tk.Frame(pad, height=1, bg=BORDER).grid(
        row=1, column=0, columnspan=3, sticky='ew', pady=(0, 14))
    dlg._inner = pad  # type: ignore[attr-defined]
    return dlg

def _buat_fields(dlg, fields, prefill=None):
    pad, entries = dlg._inner, []
    for i, field in enumerate(fields):
        tk.Label(pad, text=field, font=F_LABEL, bg=BG, fg=MUTED, anchor='e').grid(
            row=i+2, column=0, sticky='e', padx=(0, 10), pady=5)
        ent = tk.Entry(pad, width=22, font=F_BODY, fg=TEXT, bg=SURFACE,
                       relief='flat', bd=0, insertbackground=TEXT,
                       highlightbackground=BORDER, highlightthickness=1, highlightcolor=ACCENT)
        if prefill: ent.insert(0, prefill[i])
        ent.grid(row=i+2, column=1, pady=5, sticky='ew', ipady=6)
        entries.append(ent)
        if i in (3, 4):
            tk.Label(pad, text="YYYY-MM-DD", font=F_MONO, bg=BG, fg=DIM).grid(
                row=i+2, column=2, sticky='w', padx=(8, 0))
    return entries

def _buat_tombol_dialog(dlg, n, fn_simpan, fn_batal):
    pad = dlg._inner
    tk.Frame(pad, height=1, bg=BORDER).grid(
        row=n+2, column=0, columnspan=3, sticky='ew', pady=(12, 8))
    bf = tk.Frame(pad, bg=BG); bf.grid(row=n+3, column=0, columnspan=3, sticky='w')
    ttk.Button(bf, text="Simpan", command=fn_simpan, style='Primary.TButton').pack(side='left', padx=(0, 8))
    ttk.Button(bf, text="Batal",  command=fn_batal,  style='Secondary.TButton').pack(side='left')

def _get_form_data(entries, dlg):
    """Validasi & parsing isian form. Mengembalikan tuple atau None jika gagal."""
    vals = [e.get().strip() for e in entries]
    if not all(vals):
        _error("Error", "Semua field harus diisi.", parent=dlg); return None
    try:    biaya = float(vals[1])
    except: _error("Error", "Biaya harus berupa angka.", parent=dlg); return None
    for t, label in [(vals[3], "Pembayaran"), (vals[4], "Jatuh Tempo")]:
        if not validasi_tanggal(t):
            _error("Error", f"Format Tanggal {label} salah. Gunakan YYYY-MM-DD.", parent=dlg)
            return None
    return vals[0], biaya, vals[2], vals[3], vals[4]


# ── Dialog CRUD ───────────────────────────────────────────────────────────────
def klik_tambah():
    fields  = ["Nama", "Biaya (Rp)", "Metode Pembayaran", "Tanggal Pembayaran", "Tanggal Jatuh Tempo"]
    dlg     = _buat_dialog("Tambah Subscription", "Tambah Subscription Baru")
    entries = _buat_fields(dlg, fields)

    def simpan():
        data = _get_form_data(entries, dlg)
        if not data: return
        nama, biaya, metode, t1, t2 = data
        add_subscription(pathfile, {
            'Nama': nama, 'Biaya': biaya, 'Metode Pembayaran': metode,
            'Tanggal Pembayaran':  date.fromisoformat(t1),
            'Tanggal Jatuh Tempo': date.fromisoformat(t2),
        })
        dlg.destroy(); load_treeview(); update_dashboard()

    _buat_tombol_dialog(dlg, len(fields), simpan, dlg.destroy)


def buka_dialog_ubah(values):
    fields   = ["Nama", "Biaya (Rp)", "Metode Pembayaran", "Tanggal Pembayaran", "Tanggal Jatuh Tempo"]
    prefill  = [str(values[0]), _parse_biaya(str(values[1])),
                str(values[2]), str(values[3]), str(values[4])]
    dlg      = _buat_dialog("Edit Subscription", "Edit Subscription")
    entries  = _buat_fields(dlg, fields, prefill)
    nama_lama = [prefill[0]]

    def simpan():
        data = _get_form_data(entries, dlg)
        if not data: return
        nama, biaya, metode, t1, t2 = data
        if nama != prefill[0]:
            update_data(pathfile, nama_lama[0], 'Nama', nama)
            nama_lama[0] = nama
        for col, val in [('Biaya', biaya), ('Metode Pembayaran', metode),
                         ('Tanggal Pembayaran', t1), ('Tanggal Jatuh Tempo', t2),
                         ('Status', 'Aktif' if date.fromisoformat(t2) > date.today() else 'Nonaktif')]:
            update_data(pathfile, nama_lama[0], col, val)
        dlg.destroy(); load_treeview(); update_dashboard()

    _buat_tombol_dialog(dlg, len(fields), simpan, dlg.destroy)


# ══════════════════════════════════════════════════════════════════════════════
# JENDELA UTAMA
# ══════════════════════════════════════════════════════════════════════════════
root = tk.Tk()
root.title("Manajemen Subskripsi Digital")
root.geometry("960x620"); root.minsize(960, 560)
root.resizable(True, True); root.configure(bg=BG)

for opt, val in [('*TCombobox*Listbox.font',            F_BODY),
                 ('*TCombobox*Listbox.background',       SURFACE),
                 ('*TCombobox*Listbox.foreground',       TEXT),
                 ('*TCombobox*Listbox.selectBackground', BORDER),
                 ('*TCombobox*Listbox.selectForeground', TEXT)]:
    root.option_add(opt, val)

# ── Style ──────────────────────────────────────────────────────────────────────
style = ttk.Style(root)
style.theme_use('clam')
style.configure('TFrame', background=BG)
style.configure('TLabel', background=BG, foreground=TEXT, font=F_BODY)

style.configure('Primary.TButton', font=F_BUTTON, background=ACCENT, foreground=SURFACE,
                borderwidth=0, focusthickness=0, padding=(18, 10), relief='flat')
style.map('Primary.TButton',
          background=[('active', ACCENT_S), ('pressed', ACCENT_S)],
          relief=[('active', 'flat'), ('pressed', 'flat')])

style.configure('Secondary.TButton', font=F_BUTTON, background=SURFACE, foreground=TEXT,
                borderwidth=1, focusthickness=0, padding=(18, 10),
                bordercolor=BORDER, relief='solid')
style.map('Secondary.TButton',
          background=[('active', PANEL), ('pressed', PANEL)],
          bordercolor=[('active', BORDER_D)])

style.configure('Danger.TButton', font=F_BUTTON, background=SURFACE, foreground=DANGER,
                borderwidth=1, focusthickness=0, padding=(18, 10),
                bordercolor=BORDER, relief='solid')
style.map('Danger.TButton',
          background=[('active', '#F8E8E8'), ('pressed', '#F8E8E8')],
          bordercolor=[('active', DANGER)])

style.configure('TScrollbar', background=PANEL, troughcolor=BG, bordercolor=BORDER,
                arrowcolor=MUTED, relief='flat', borderwidth=0, width=8)
style.map('TScrollbar', background=[('active', BORDER_D)])

style.configure('TCombobox', fieldbackground=SURFACE, background=SURFACE, foreground=TEXT,
                arrowcolor=MUTED, bordercolor=BORDER, selectbackground=SURFACE,
                selectforeground=TEXT, padding=6, relief='flat')
style.map('TCombobox',
          fieldbackground=[('readonly', SURFACE)], foreground=[('readonly', TEXT)],
          background=[('readonly', SURFACE)],
          bordercolor=[('focus', ACCENT), ('readonly', BORDER)])


# ── Header ─────────────────────────────────────────────────────────────────────
frame_header = tk.Frame(root, bg=BG)
frame_header.pack(fill='x', side='top', padx=24, pady=(20, 14))
frame_header.columnconfigure(0, weight=1)

_bulan = ["Januari","Februari","Maret","April","Mei","Juni",
          "Juli","Agustus","September","Oktober","November","Desember"]
_today = date.today()

tk.Label(frame_header, text="Subscription Manager",
         font=F_TITLE, bg=BG, fg=TEXT).grid(row=0, column=0, sticky='w')
tk.Label(frame_header, text="Pantau & kelola langganan digital Anda",
         font=F_ITAL, bg=BG, fg=MUTED).grid(row=1, column=0, sticky='w', pady=(3, 0))
tk.Label(frame_header, text=f"{_bulan[_today.month-1]}  ·  {_today.year}",
         font=F_MONO, bg=BG, fg=MUTED).grid(row=0, column=1, sticky='ne', pady=(6, 0))

tk.Frame(root, height=1, bg=BORDER).pack(fill='x', side='top')


# ── Tab bar ────────────────────────────────────────────────────────────────────
frame_tabbar = tk.Frame(root, bg=BG)
frame_tabbar.pack(fill='x', side='top', padx=24)
frame_tab1 = tk.Frame(root, bg=BG)
frame_tab2 = tk.Frame(root, bg=BG)
_tab_labels, _tab_underline = [], []

def _switch_tab(idx):
    frame_tab1.pack_forget(); frame_tab2.pack_forget()
    (frame_tab1 if idx == 0 else frame_tab2).pack(
        fill='both', expand=True, padx=24, pady=(6, 20))
    for i, (lbl, und) in enumerate(zip(_tab_labels, _tab_underline)):
        active = i == idx
        lbl.config(font=F_LABEL_BOLD if active else F_LABEL, fg=TEXT if active else MUTED)
        und.config(bg=ACCENT if active else BG)

for _i, _name in enumerate(["Daftar Langganan", "Dashboard"]):
    _wrap = tk.Frame(frame_tabbar, bg=BG, cursor='hand2')
    _wrap.pack(side='left', padx=(0, 22))
    _lbl = tk.Label(_wrap, text=_name, font=F_LABEL, bg=BG, fg=MUTED, pady=10, cursor='hand2')
    _lbl.pack()
    _und = tk.Frame(_wrap, height=2, bg=BG); _und.pack(fill='x')
    _tab_labels.append(_lbl); _tab_underline.append(_und)
    _cb = lambda _, i=_i: _switch_tab(i)
    _wrap.bind('<Button-1>', _cb); _lbl.bind('<Button-1>', _cb)

tk.Frame(root, height=1, bg=BORDER).pack(fill='x', side='top')


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DAFTAR LANGGANAN
# ══════════════════════════════════════════════════════════════════════════════

# Toolbar
frame_toolbar = tk.Frame(frame_tab1, bg=BG)
frame_toolbar.pack(side='top', fill='x', pady=(8, 10))

# Sort (kanan terlebih dahulu agar search bisa mengisi sisa ruang)
_fr_sort = tk.Frame(frame_toolbar, bg=BG); _fr_sort.pack(side='right')

combo_kolom_sort = ttk.Combobox(_fr_sort, values=["Nama", "Biaya", "Tanggal Jatuh Tempo"],
                                 state="readonly", width=15, font=F_BODY)
combo_kolom_sort.set("Biaya"); combo_kolom_sort.pack(side='left', padx=(0, 6))

combo_tipe_sort = ttk.Combobox(_fr_sort, values=["Ascending", "Descending"],
                                state="readonly", width=11, font=F_BODY)
combo_tipe_sort.set("Descending"); combo_tipe_sort.pack(side='left', padx=(0, 6))

combo_algo_sort = ttk.Combobox(_fr_sort, values=["Insertion Sort", "Selection Sort"],
                                state="readonly", width=13, font=F_BODY)
combo_algo_sort.set("Insertion Sort"); combo_algo_sort.pack(side='left', padx=(0, 8))
ttk.Button(_fr_sort, text="Terapkan", command=klik_sort,
           style='Primary.TButton').pack(side='left')

# Search (mengisi sisa lebar)
_fr_search = tk.Frame(frame_toolbar, bg=BG)
_fr_search.pack(side='left', fill='x', expand=True, padx=(0, 14))

_search_box = tk.Frame(_fr_search, bg=SURFACE,
                       highlightbackground=BORDER, highlightthickness=1)
_search_box.pack(side='left', fill='x', expand=True)

entry_search = tk.Entry(_search_box, font=F_BODY, fg=MUTED, bg=SURFACE,
                        relief='flat', bd=0, insertbackground=TEXT, highlightthickness=0)
entry_search.pack(fill='x', expand=True, padx=14, ipady=8)
entry_search.insert(0, PLACEHOLDER)

def _focus_in(_):
    if entry_search.get() == PLACEHOLDER:
        entry_search.delete(0, 'end'); entry_search.config(fg=TEXT)

def _focus_out(_):
    if not entry_search.get().strip():
        entry_search.insert(0, PLACEHOLDER); entry_search.config(fg=MUTED)

entry_search.bind('<FocusIn>',  _focus_in)
entry_search.bind('<FocusOut>', _focus_out)

combo_metode_search = ttk.Combobox(_fr_search, values=["Sequential", "Binary"],
                                    state="readonly", width=11, font=F_BODY)
combo_metode_search.set("Sequential"); combo_metode_search.pack(side='left', padx=(8, 0))
ttk.Button(_fr_search, text="Cari", command=klik_cari,
           style='Primary.TButton').pack(side='left', padx=(8, 0))

# Tombol CRUD (bawah)
frame_buttons = tk.Frame(frame_tab1, bg=BG)
frame_buttons.pack(side='bottom', fill='x', pady=(10, 0))
ttk.Button(frame_buttons, text="+ Tambah", command=klik_tambah,
           style='Primary.TButton').pack(side='left', padx=(0, 8))
ttk.Button(frame_buttons, text="Edit",  command=klik_ubah,
           style='Secondary.TButton').pack(side='left', padx=(0, 8))
ttk.Button(frame_buttons, text="Hapus", command=klik_hapus,
           style='Danger.TButton').pack(side='left')
label_count = tk.Label(frame_buttons, text="", font=F_ITAL, bg=BG, fg=MUTED)
label_count.pack(side='right')
tk.Frame(frame_tab1, height=1, bg=BORDER).pack(side='bottom', fill='x', pady=(0, 6))

# Tabel
frame_tree = tk.Frame(frame_tab1, bg=BG,
                      highlightbackground=BORDER, highlightthickness=1)
frame_tree.pack(side='top', fill='both', expand=True)
tree = TableCanvas(frame_tree, columns=COLS, col_display=COL_DISP,
                   col_widths=COL_W, bg=SURFACE)
tree.pack(fill='both', expand=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
frame_chart = tk.Frame(frame_tab2, bg=BG)
frame_chart.pack(side='left', fill='both', expand=True, padx=(0, 14))

frame_info = tk.Frame(frame_tab2, width=290, bg=BG)
frame_info.pack(side='right', fill='y'); frame_info.pack_propagate(False)

fig = Figure(figsize=(5, 3.5), dpi=90)
fig.patch.set_facecolor(BG)
ax  = fig.add_subplot(111); ax.set_facecolor(SURFACE)
canvas = FigureCanvasTkAgg(fig, master=frame_chart)
canvas.get_tk_widget().configure(bg=BG, highlightthickness=0)
canvas.get_tk_widget().pack(fill='both', expand=True)

# Kartu: Total
_ct_frame = tk.Frame(frame_info, bg=PANEL,
                     highlightbackground=BORDER, highlightthickness=1)
_ct_frame.pack(fill='x', pady=(0, 12))
_ct = tk.Frame(_ct_frame, bg=PANEL, padx=18, pady=18); _ct.pack(fill='x')
tk.Label(_ct, text="TOTAL BULAN INI", font=F_CAPS, bg=PANEL, fg=MUTED).pack(anchor='w')
label_total = tk.Label(_ct, text="Rp 0", font=F_MONO_LG, bg=PANEL, fg=ACCENT)
label_total.pack(anchor='w', pady=(4, 2))
label_aktif_count = tk.Label(_ct, text="dari 0 langganan aktif",
                              font=F_BODY, bg=PANEL, fg=MUTED)
label_aktif_count.pack(anchor='w')

# Kartu: Rekomendasi
_cr_frame = tk.Frame(frame_info, bg=PANEL,
                     highlightbackground=BORDER, highlightthickness=1)
_cr_frame.pack(fill='x')
_cr = tk.Frame(_cr_frame, bg=PANEL, padx=18, pady=18); _cr.pack(fill='both', expand=True)
tk.Label(_cr, text="Rekomendasi berhenti",
         font=F_H2, bg=PANEL, fg=TEXT).pack(anchor='w', pady=(0, 8))
frame_rekom = tk.Frame(_cr, bg=PANEL); frame_rekom.pack(fill='x', anchor='w')


# ══════════════════════════════════════════════════════════════════════════════
# STARTUP
# ══════════════════════════════════════════════════════════════════════════════
if not pathfile.exists():
    pathfile.parent.mkdir(parents=True, exist_ok=True)
    filetemplate(pathfile)

ubah_status(pathfile)

pengingat = mendekati_jatuh_tempo(pathfile, hari_sebelum=7)
if pengingat:
    def _show_jatuh_tempo():
        dlg = tk.Toplevel(root)
        dlg.title("Pengingat Jatuh Tempo"); dlg.configure(bg=BG)
        dlg.resizable(False, False); dlg.grab_set(); dlg.transient(root)
        pad = tk.Frame(dlg, bg=BG, padx=24, pady=20); pad.pack(fill='both', expand=True)
        tk.Label(pad, text="Pengingat Jatuh Tempo",
                 font=F_H2, bg=BG, fg=TEXT).pack(anchor='w')
        tk.Frame(pad, height=1, bg=BORDER).pack(fill='x', pady=(8, 12))
        tk.Label(pad, text="Subscription berikut akan segera jatuh tempo dalam 7 hari:",
                 font=F_BODY, bg=BG, fg=TEXT).pack(anchor='w', pady=(0, 10))
        for item in pengingat:
            fr = tk.Frame(pad, bg=BG); fr.pack(fill='x', pady=3)
            tk.Label(fr, text=item['Nama'],
                     font=F_BODY, bg=BG, fg=TEXT, anchor='w').pack(side='left')
            tk.Label(fr, text=str(item['Tanggal Jatuh Tempo']),
                     font=F_MONO, bg=BG, fg=DANGER).pack(side='right')
        tk.Frame(pad, height=1, bg=BORDER).pack(fill='x', pady=(12, 10))
        ttk.Button(pad, text="OK", command=dlg.destroy,
                   style='Primary.TButton').pack(anchor='e')
        dlg.update_idletasks()
        w = max(dlg.winfo_reqwidth(), 360); h = dlg.winfo_reqheight()
        dlg.geometry(f"{w}x{h}+{root.winfo_x()+(root.winfo_width()-w)//2}"
                     f"+{root.winfo_y()+(root.winfo_height()-h)//2}")
    root.after(150, _show_jatuh_tempo)

_switch_tab(0)
load_treeview()
update_dashboard()
root.mainloop()
