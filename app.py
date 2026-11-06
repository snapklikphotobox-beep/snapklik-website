import streamlit as st
from supabase import create_client
from pathlib import Path
from datetime import date, datetime, timedelta
import re
import os
import hmac
import pandas as pd

# ============================================================
# SNAPKLIK PHOTOBOX - SISTEM BOOKING
# Jalankan: streamlit run app.py
# Database booking tersimpan di Supabase (cloud).
# ============================================================

APP_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="SnapKlik | Booking Photobox",
    page_icon="📸",
    layout="centered",
    initial_sidebar_state="expanded",
)

@st.cache_resource
def get_supabase():
    """Membuat koneksi Supabase menggunakan secret server-side."""
    try:
        url = (st.secrets.get("SUPABASE_URL", "")
               or st.secrets.get("supabase", {}).get("url", "")
               or os.environ.get("SUPABASE_URL", ""))
        key = (st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", "")
               or st.secrets.get("supabase", {}).get("service_role_key", "")
               or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""))
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

    if not url or not key:
        st.error("Koneksi Supabase belum dikonfigurasi. Isi SUPABASE_URL dan SUPABASE_SERVICE_ROLE_KEY di Streamlit Secrets.")
        st.stop()
    return create_client(url, key)

supabase = get_supabase()

# Palet warna terinspirasi dari referensi: cream, maroon, putih.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700;800&display=swap');
:root { --cream:#faf6f2; --maroon:#713746; --pink:#d9aeb4; --rose:#f3e4e3; --ink:#382d30; --muted:#887a7d; --line:#eadfdb; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:linear-gradient(180deg,#fbf7f3 0%,#f7efeb 100%); color:var(--ink); }
.block-container { max-width:900px; padding:1.5rem 1.2rem 3rem; }
header[data-testid="stHeader"] { background:transparent; }
#MainMenu, footer { visibility:hidden; }
h1,h2,h3,h4 { color:var(--maroon)!important; }
h2 { font-family:'Playfair Display',serif!important; font-size:1.8rem!important; }
h3 { font-size:1.08rem!important; }
p, label, .stMarkdown { color:var(--ink); }
.brandbar { display:flex; align-items:center; justify-content:space-between; padding:13px 18px; border:1px solid #eee3df; border-radius:18px; background:rgba(255,255,255,.78); box-shadow:0 8px 24px rgba(91,49,58,.045); margin-bottom:24px; }
.brandname { color:var(--maroon); font-weight:800; letter-spacing:3px; font-size:1.12rem; }
.brandtag { color:#9b8589; font-size:.76rem; letter-spacing:.5px; }
.hero { background:linear-gradient(125deg,#713746 0%,#955866 58%,#c18e96 100%); color:white; border-radius:26px; padding:35px 28px; text-align:center; margin-bottom:24px; box-shadow:0 15px 35px rgba(113,55,70,.16); position:relative; overflow:hidden; }
.hero:after { content:'♥'; position:absolute; right:28px; top:8px; color:rgba(255,255,255,.12); font-size:6rem; transform:rotate(15deg); }
.hero-kicker { font-size:.72rem; letter-spacing:3px; text-transform:uppercase; color:#f3dfe1; font-weight:700; }
.hero-title { font-family:'Playfair Display',serif; color:#fff; font-size:2.5rem; font-weight:700; line-height:1.15; margin:10px 0; }
.hero-sub { color:#f8e9e9; font-size:.94rem; margin:0; }
.stepper { display:flex; justify-content:space-between; gap:9px; margin:25px 0 30px; }
.step { flex:1; text-align:center; color:#a99a9c; font-size:.76rem; border-top:3px solid #e8dcd9; padding-top:10px; }
.step.active { color:var(--maroon); border-color:var(--maroon); font-weight:800; }
.studio-card { background:#fff; border:1px solid var(--line); border-radius:20px; padding:18px; margin:10px 0; }
.price { color:var(--maroon); font-size:1.18rem; font-weight:800; }
/* Streamlit cards and form surfaces */
div[data-testid="stVerticalBlockBorderWrapper"] { background:rgba(255,255,255,.88); border:1px solid var(--line); border-radius:20px; box-shadow:0 7px 20px rgba(85,54,59,.045); }
div[data-testid="stForm"] { background:#fff; padding:22px; border-radius:20px; border:1px solid var(--line); box-shadow:0 8px 22px rgba(85,54,59,.04); }
div.stButton > button { border-radius:14px; min-height:44px; font-weight:700; transition:all .2s ease; }
div.stButton > button[kind="primary"] { background:var(--maroon); border:1px solid var(--maroon); color:white; width:100%; box-shadow:0 5px 13px rgba(113,55,70,.16); }
div.stButton > button[kind="primary"]:hover { background:#572735; border-color:#572735; transform:translateY(-1px); }
div.stButton > button[kind="secondary"] { border:1px solid #d9c4c6; color:var(--maroon); background:#fff; }
div.stButton > button[kind="secondary"]:hover { border-color:var(--maroon); background:#fbf2f2; }
.stTextInput input, .stTextArea textarea, .stNumberInput input, div[data-baseweb="select"] > div { border-radius:12px!important; border-color:#e5d7d4!important; background:#fff!important; }
.stRadio [role="radiogroup"] { gap:8px; }
.stRadio [role="radiogroup"] label { background:#fff; border:1px solid #e8d9d8; border-radius:12px; padding:8px 13px; }
.stRadio [role="radiogroup"] label:has(input:checked) { border-color:var(--maroon); background:#f8eeee; }
div[data-testid="stAlert"] { border-radius:14px; }
.small-note { color:var(--muted); font-size:.82rem; text-align:center; padding-top:8px; }
.section-kicker { color:#b1848b; font-size:.72rem; font-weight:800; letter-spacing:2px; text-transform:uppercase; margin-bottom:2px; }
@media(max-width:640px) { .block-container{padding:1rem .8rem 2rem;} .hero{padding:28px 16px;border-radius:20px;} .hero-title{font-size:2rem;} .brandbar{padding:11px 13px;} .brandtag{font-size:.66rem;} .step{font-size:.68rem;} }
</style>
""", unsafe_allow_html=True)

STUDIOS = {
    "Basic Room": {
        "description": "Pilihan warna background basic untuk foto bersama teman, pasangan, atau keluarga.",
        "backgrounds": ["White", "Maroon", "Soft Grey", "Silver", "Abstrac Blue"],
    },
    "Close Up Room": {
        "description": "Konsep close-up dengan pilihan background Polka, Rainbow, dan Star.",
        "backgrounds": ["Polka", "Rainbow", "Star"],
    },
}

PACKAGES = {
    "Basic Photo": {
        "price": 35000,
        "people": "1-8 orang",
        "duration": "20 menit sesi foto",
        "prints": "1 print basic frame",
        "details": "Unlimited jepret • soft file dikirim digital",
    },
    "Vintage Photo": {
        "price": 40000,
        "people": "1-4 orang",
        "duration": "20 menit sesi foto",
        "prints": "1 print vintage frame",
        "details": "Unlimited jepret • soft file dikirim digital",
    },
    "XXL Photo": {
        "price": 65000,
        "people": "1-6 orang",
        "duration": "20 menit sesi foto",
        "prints": "1 print XXL frame",
        "details": "Unlimited jepret • soft file dikirim digital",
    },
}

# Atur jam operasional dan interval slot di sini.
TIME_SLOTS = [
    "10:00", "10:30", "11:00", "11:30",
    "12:00", "12:30", "13:00", "13:30",
    "14:00", "14:30", "15:00", "15:30",
    "16:00", "16:30", "17:00", "17:30",
    "18:00", "18:30", "19:00", "19:30",
    "20.00", "20.30", "21.00"
]

def booked_slots(day):
    """Mengambil jam yang sudah terisi dari Supabase."""
    response = (supabase.table("bookings")
                .select("booking_time")
                .eq("booking_date", day.isoformat())
                .neq("status", "Dibatalkan")
                .execute())
    return {row["booking_time"] for row in (response.data or [])}

def rupiah(amount):
    return "Rp" + f"{amount:,.0f}".replace(",", ".")

def stepper(active):
    labels = ["Studio", "Paket", "Jadwal", "Data Diri"]
    html = '<div class="stepper">'
    for i, label in enumerate(labels, 1):
        cls = "step active" if i <= active else "step"
        mark = "✓" if i < active else str(i)
        html += f'<div class="{cls}"><b>{mark}</b><br>{label}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def reset_booking():
    for key in ["studio", "package", "background", "booking_date", "booking_time"]:
        st.session_state.pop(key, None)
    st.session_state.stage = 1


# ============================================================
# NAVIGASI SIDEBAR + HALAMAN ADMIN
# Password admin diatur melalui .streamlit/secrets.toml
# ============================================================
st.sidebar.markdown("## 📸 SNAPKLIK")
st.sidebar.caption("PHOTOBOX BOOKING SYSTEM")
page = st.sidebar.radio("MENU", ["Booking Pelanggan", "Admin"], label_visibility="visible")

if page == "Admin":
    st.markdown('<div class="brandbar"><div class="brandname">SNAPKLIK<span style="color:#d5a4ac">.</span> ADMIN</div><div class="brandtag">MANAGE YOUR BOOKINGS ♥</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">ADMIN AREA</div><h2>Dashboard Booking</h2>', unsafe_allow_html=True)

    configured_password = os.environ.get("SNAPKLIK_ADMIN_PASSWORD", "")
    try:
        configured_password = st.secrets.get("admin_password", configured_password)
    except Exception:
        pass

    if not configured_password:
        st.warning("Password admin belum diatur. Atur terlebih dahulu agar halaman admin dapat digunakan.")
        st.markdown("Buat file **`.streamlit/secrets.toml`** di folder project, lalu isi:")
        st.code('admin_password = "GANTI_DENGAN_PASSWORD_KUAT"', language="toml")
        st.info("Setelah menyimpan file tersebut, jalankan ulang Streamlit. Jangan bagikan password kepada pelanggan.")
        st.stop()

    if not st.session_state.get("admin_logged_in", False):
        with st.form("admin_login_form"):
            admin_password_input = st.text_input("Password Admin", type="password")
            login = st.form_submit_button("Masuk Admin", type="primary", use_container_width=True)
        if login:
            if hmac.compare_digest(admin_password_input, str(configured_password)):
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Password salah. Silakan coba lagi.")
        st.caption("Halaman ini khusus pengelola SnapKlik.")
        st.stop()

    top_a, top_b = st.columns([4, 1])
    with top_a:
        st.caption("Ringkasan dan pengelolaan pesanan pelanggan")
    with top_b:
        if st.button("Keluar", key="admin_logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

    try:
        response = (supabase.table("bookings")
                    .select("*")
                    .order("created_at", desc=True)
                    .execute())
        df = pd.DataFrame(response.data or [])
    except Exception as exc:
        st.error(f"Gagal mengambil data booking dari Supabase: {exc}")
        st.stop()

    if df.empty:
        st.info("Belum ada booking yang masuk. Pesanan pelanggan akan muncul di halaman ini.")
        st.stop()

    total_bookings = len(df)
    waiting = int((df["status"] == "Menunggu konfirmasi").sum())
    confirmed = int((df["status"] == "Dikonfirmasi").sum())
    completed = int((df["status"] == "Selesai").sum())
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Booking", total_bookings)
    m2.metric("Menunggu", waiting)
    m3.metric("Dikonfirmasi", confirmed)
    m4.metric("Selesai", completed)

    st.markdown("### Data Booking")
    search_text = st.text_input("Cari booking", placeholder="Nama, kode booking, atau nomor WhatsApp")
    status_options = ["Semua", "Menunggu konfirmasi", "Dikonfirmasi", "Selesai", "Dibatalkan"]
    chosen_status = st.selectbox("Filter status", status_options)
    filtered = df.copy()
    if chosen_status != "Semua":
        filtered = filtered[filtered["status"] == chosen_status]
    if search_text.strip():
        q = search_text.strip().lower()
        mask = (filtered["customer_name"].fillna("").str.lower().str.contains(q, regex=False) |
                filtered["booking_code"].fillna("").str.lower().str.contains(q, regex=False) |
                filtered["phone"].fillna("").str.lower().str.contains(q, regex=False))
        filtered = filtered[mask]

    display_cols = ["booking_code", "customer_name", "phone", "studio", "package_name", "background", "booking_date", "booking_time", "people", "total", "status"]
    display = filtered[display_cols].rename(columns={
        "booking_code":"Kode Booking", "customer_name":"Nama", "phone":"WhatsApp",
        "studio":"Studio", "package_name":"Paket", "background":"Background",
        "booking_date":"Tanggal", "booking_time":"Jam", "people":"Orang",
        "total":"Total (Rp)", "status":"Status"
    })
    st.caption(f"Menampilkan {len(filtered)} dari {total_bookings} booking")
    st.dataframe(display, use_container_width=True, hide_index=True)

    csv_data = display.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Download Data Booking (CSV)", data=csv_data, file_name="data_booking_snapklik.csv", mime="text/csv")

    st.markdown("### Kelola Status Booking")
    booking_codes = filtered["booking_code"].tolist()
    if booking_codes:
        selected_code = st.selectbox("Pilih kode booking", booking_codes)
        selected_row = df[df["booking_code"] == selected_code].iloc[0]
        st.write(f"**{selected_row['customer_name']}** · {selected_row['phone']} · {selected_row['booking_date']} pukul {selected_row['booking_time']}")
        status_list = ["Menunggu konfirmasi", "Dikonfirmasi", "Selesai", "Dibatalkan"]
        current_status = selected_row["status"] if selected_row["status"] in status_list else status_list[0]
        new_status = st.selectbox("Ubah status", status_list, index=status_list.index(current_status), key="admin_new_status")
        if st.button("Simpan Status", type="primary", key="save_booking_status"):
            try:
                (supabase.table("bookings")
                 .update({"status": new_status})
                 .eq("booking_code", selected_code)
                 .execute())
                st.success(f"Status {selected_code} berhasil diperbarui menjadi {new_status}.")
                st.rerun()
            except Exception as exc:
                st.error(f"Gagal memperbarui status booking: {exc}")
    else:
        st.caption("Tidak ada booking yang cocok dengan pencarian atau filter.")

    st.markdown("### Detail Catatan Pelanggan")
    if booking_codes:
        detail_code = st.selectbox("Lihat catatan booking", booking_codes, key="admin_detail_code")
        detail_row = df[df["booking_code"] == detail_code].iloc[0]
        st.write(detail_row.get("notes") or "Tidak ada catatan tambahan.")
        st.caption(f"Email: {detail_row.get('email') or '-'} · Jumlah orang: {detail_row.get('people')}")

    st.markdown('<div class="small-note">SNAPKLIK ADMIN • Kelola booking dengan teliti ♥</div>', unsafe_allow_html=True)
    st.stop()

if "stage" not in st.session_state:
    st.session_state.stage = 1

st.markdown('<div class="brandbar"><div class="brandname">SNAPKLIK<span style="color:#d5a4ac">.</span></div><div class="brandtag">PHOTOBOOTH EXPERIENCE · PLEASE TAKE YOUR PHOTOS ♥</div></div>', unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="hero-kicker">Your moment, your story</div><div class="hero-title">Book Your Photo Session</div><p class="hero-sub">Create little memories worth keeping. Pick your favorite setup and let’s capture it!</p></div>', unsafe_allow_html=True)
stepper(st.session_state.stage)

# STEP 1 - PILIH STUDIO
if st.session_state.stage == 1:
    st.markdown('<div class="section-kicker">01 · Find your vibe</div><h2>Pilih Studio Favoritmu</h2>', unsafe_allow_html=True)
    st.write("Pilih konsep foto yang ingin kamu gunakan.")
    for name, info in STUDIOS.items():
        selected = st.session_state.get("studio") == name
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.subheader(name)
                st.caption(info["description"])
                st.caption("Background: " + " • ".join(info["backgrounds"]))
            with c2:
                if st.button("Dipilih ✓" if selected else "Pilih", key=f"studio_{name}", type="primary" if selected else "secondary"):
                    st.session_state.studio = name
                    st.rerun()
    st.write("")
    if st.button("Lanjut →", type="primary", disabled=not st.session_state.get("studio")):
        st.session_state.stage = 2
        st.rerun()

# STEP 2 - PAKET DAN BACKGROUND
elif st.session_state.stage == 2:
    st.markdown('<div class="section-kicker">02 · Make it yours</div><h2>Pilih Paket Foto</h2>', unsafe_allow_html=True)
    st.caption(f"Studio: **{st.session_state.studio}**")
    for name, p in PACKAGES.items():
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{name}**")
                st.caption(f"{p['people']} • {p['duration']} • {p['prints']}")
                st.caption(p["details"])
            with c2:
                st.markdown(f'<div class="price">{rupiah(p["price"])}</div>', unsafe_allow_html=True)
            if st.button("Pilih paket ini" if st.session_state.get("package") != name else "Paket dipilih ✓",
                         key=f"pkg_{name}", type="primary" if st.session_state.get("package") == name else "secondary"):
                st.session_state.package = name
                st.rerun()

    backgrounds = STUDIOS[st.session_state.studio]["backgrounds"]
    st.markdown("**Pilih Warna Background**")
    current_bg = st.session_state.get("background", backgrounds[0])
    st.session_state.background = st.radio(
        "Background", backgrounds,
        index=backgrounds.index(current_bg) if current_bg in backgrounds else 0,
        horizontal=True, label_visibility="collapsed"
    )
    b1, b2 = st.columns(2)
    with b1:
        if st.button("← Kembali", type="secondary"):
            st.session_state.stage = 1
            st.rerun()
    with b2:
        if st.button("Lanjut →", type="primary", disabled=not st.session_state.get("package")):
            st.session_state.stage = 3
            st.rerun()

# STEP 3 - TANGGAL DAN JAM
elif st.session_state.stage == 3:
    st.markdown('<div class="section-kicker">03 · Save the date</div><h2>Pilih Tanggal & Jam</h2>', unsafe_allow_html=True)
    st.caption(f"Paket: **{st.session_state.package}** • Background: **{st.session_state.background}**")
    today = date.today()
    available_dates = [today + timedelta(days=i) for i in range(14)]
    date_labels = {d: d.strftime("%a, %d %b %Y") for d in available_dates}
    chosen = st.session_state.get("booking_date", today)
    if chosen not in available_dates:
        chosen = today
    selected_date = st.selectbox(
        "Pilih tanggal sesi foto",
        available_dates,
        index=available_dates.index(chosen),
        format_func=lambda d: date_labels[d]
    )
    st.session_state.booking_date = selected_date

    taken = booked_slots(selected_date)
    available_slots = [t for t in TIME_SLOTS if t not in taken]
    st.markdown("**Pilih Slot Waktu Sesi Foto**")
    st.caption(f"{len(available_slots)} slot tersedia")
    if available_slots:
        previous = st.session_state.get("booking_time")
        idx = available_slots.index(previous) if previous in available_slots else 0
        st.session_state.booking_time = st.radio(
            "Slot waktu", available_slots, index=idx, horizontal=True, label_visibility="collapsed"
        )
    else:
        st.warning("Semua slot pada tanggal ini sudah terisi. Silakan pilih tanggal lain.")
        st.session_state.pop("booking_time", None)

    b1, b2 = st.columns(2)
    with b1:
        if st.button("← Kembali", type="secondary"):
            st.session_state.stage = 2
            st.rerun()
    with b2:
        if st.button("Lanjut →", type="primary", disabled=not available_slots):
            st.session_state.stage = 4
            st.rerun()

# STEP 4 - DATA DIRI DAN SIMPAN BOOKING
elif st.session_state.stage == 4:
    st.markdown('<div class="section-kicker">04 · Almost there</div><h2>Lengkapi Data Pemesan</h2>', unsafe_allow_html=True)
    package = PACKAGES[st.session_state.package]
    max_people = 2 if st.session_state.package == "Self Photo Session" else 8
    min_people = 1 if max_people == 2 else 3

    st.markdown("#### Ringkasan Booking")
    with st.container(border=True):
        st.write(f"**Studio:** {st.session_state.studio}")
        st.write(f"**Paket:** {st.session_state.package} — {rupiah(package['price'])}")
        st.write(f"**Background:** {st.session_state.background}")
        st.write(f"**Jadwal:** {st.session_state.booking_date.strftime('%d %B %Y')} • {st.session_state.booking_time}")
        st.write(f"**Jumlah orang:** {package['people']}")

    with st.form("customer_form"):
        customer_name = st.text_input("Nama lengkap *")
        phone = st.text_input("Nomor WhatsApp aktif *", placeholder="08xxxxxxxxxx")
        email = st.text_input("Email (opsional)")
        people = st.number_input("Jumlah orang", min_value=min_people, max_value=max_people, value=min_people, step=1)
        notes = st.text_area("Catatan tambahan (opsional)", placeholder="Contoh: request pose, kebutuhan khusus, dll.")
        agree = st.checkbox("Saya memastikan data booking sudah benar.")
        submitted = st.form_submit_button("Konfirmasi Booking", type="primary", use_container_width=True)

    if submitted:
        clean_phone = re.sub(r"[\s\-+]", "", phone)
        if not customer_name.strip():
            st.error("Nama lengkap wajib diisi.")
        elif not re.fullmatch(r"0\d{8,13}", clean_phone):
            st.error("Nomor WhatsApp belum valid. Gunakan format 08xxxxxxxxxx.")
        elif email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            st.error("Format email belum valid.")
        elif not agree:
            st.error("Centang persetujuan sebelum melanjutkan.")
        else:
            code = "SK" + datetime.now().strftime("%y%m%d%H%M%S%f")
            booking_payload = {
                "booking_code": code,
                "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "studio": st.session_state.studio,
                "package_name": st.session_state.package,
                "background": st.session_state.background,
                "booking_date": st.session_state.booking_date.isoformat(),
                "booking_time": st.session_state.booking_time,
                "customer_name": customer_name.strip(),
                "phone": clean_phone,
                "email": email.strip() or None,
                "people": int(people),
                "notes": notes.strip() or None,
                "total": package["price"],
            }
            try:
                supabase.table("bookings").insert(booking_payload).execute()
                st.session_state.confirmed_code = code
                st.session_state.confirmed_name = customer_name.strip()
                st.session_state.stage = 5
                st.rerun()
            except Exception as exc:
                error_text = str(exc).lower()
                if "23505" in error_text or "duplicate" in error_text or "unique" in error_text:
                    st.error("Maaf, slot ini baru saja dipesan orang lain. Silakan kembali dan pilih jam lain.")
                else:
                    st.error(f"Booking belum berhasil disimpan. Periksa koneksi Supabase atau hubungi admin. Detail: {exc}")

    if st.button("← Kembali", type="secondary"):
        st.session_state.stage = 3
        st.rerun()

# BOOKING SUCCESS
elif st.session_state.stage == 5:
    st.success("Booking berhasil tersimpan!")
    st.markdown('<div class="section-kicker" style="text-align:center">Your booking is saved</div><h2 style="text-align:center">Thank You ♥</h2>', unsafe_allow_html=True)
    st.write(f"Terima kasih, **{st.session_state.confirmed_name}**. Data booking kamu sudah masuk ke sistem SnapKlik.")
    with st.container(border=True):
        st.caption("KODE BOOKING")
        st.markdown(f"<h2 style='text-align:center'>{st.session_state.confirmed_code}</h2>", unsafe_allow_html=True)
        st.write(f"**Studio:** {st.session_state.studio}")
        st.write(f"**Paket:** {st.session_state.package}")
        st.write(f"**Background:** {st.session_state.background}")
        st.write(f"**Jadwal:** {st.session_state.booking_date.strftime('%d %B %Y')} • {st.session_state.booking_time}")
        st.write(f"**Total:** {rupiah(PACKAGES[st.session_state.package]['price'])}")
        st.caption("Status: Menunggu konfirmasi admin")
    st.info("Simpan kode booking ini. Admin SnapKlik dapat menghubungi pemesan melalui WhatsApp untuk konfirmasi.")
    if st.button("Buat Booking Baru", type="primary"):
        reset_booking()
        st.rerun()

st.markdown("---")
st.markdown('<div class="small-note" style="text-align:center">SNAPKLIK PHOTOBOX • Please take your photos ♥</div>', unsafe_allow_html=True)
