import streamlit as st
from supabase import create_client
from datetime import date, datetime, timedelta, time
import os
import hmac
import re
import pandas as pd

# ============================================================
# SNAPKLIK - SIMPLE BOOKING
# Customer hanya memilih tanggal dan jam.
# Jam operasional diatur dari halaman Admin dan disimpan di Supabase.
# ============================================================

st.set_page_config(
    page_title="SnapKlik | Booking",
    page_icon="📸",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DEFAULT_OPEN = time(10, 0)
DEFAULT_CLOSE = time(21, 0)
DEFAULT_INTERVAL = 30
SETTINGS_TABLE = "app_settings"
BOOKINGS_TABLE = "bookings"

@st.cache_resource
def get_supabase():
    try:
        url = (
            st.secrets.get("SUPABASE_URL", "")
            or st.secrets.get("supabase", {}).get("url", "")
            or os.environ.get("SUPABASE_URL", "")
        )
        key = (
            st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", "")
            or st.secrets.get("supabase", {}).get("service_role_key", "")
            or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        )
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

    if not url or not key:
        st.error("Koneksi Supabase belum dikonfigurasi. Isi SUPABASE_URL dan SUPABASE_SERVICE_ROLE_KEY di Streamlit Secrets.")
        st.stop()
    return create_client(url, key)

supabase = get_supabase()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700;800&display=swap');
:root { --cream:#faf6f2; --maroon:#713746; --pink:#d9aeb4; --rose:#f3e4e3; --ink:#382d30; --muted:#887a7d; --line:#eadfdb; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:linear-gradient(180deg,#fbf7f3 0%,#f7efeb 100%); color:var(--ink); }
.block-container { max-width:680px; padding:1.5rem 1.1rem 3rem; }
header[data-testid="stHeader"] { background:transparent; }
#MainMenu, footer { visibility:hidden; }
h1,h2,h3,h4 { color:var(--maroon)!important; }
h2 { font-family:'Playfair Display',serif!important; font-size:1.8rem!important; }
.brandbar { display:flex; align-items:center; justify-content:space-between; padding:13px 18px; border:1px solid #eee3df; border-radius:18px; background:rgba(255,255,255,.85); box-shadow:0 8px 24px rgba(91,49,58,.045); margin-bottom:22px; }
.brandname { color:var(--maroon); font-weight:800; letter-spacing:3px; font-size:1.12rem; }
.brandtag { color:#9b8589; font-size:.76rem; letter-spacing:.5px; }
.hero { background:linear-gradient(125deg,#713746 0%,#955866 58%,#c18e96 100%); color:white; border-radius:24px; padding:30px 22px; text-align:center; margin-bottom:22px; box-shadow:0 15px 35px rgba(113,55,70,.13); }
.hero-kicker { font-size:.72rem; letter-spacing:3px; text-transform:uppercase; color:#f3dfe1; font-weight:700; }
.hero-title { font-family:'Playfair Display',serif; color:#fff; font-size:2.35rem; font-weight:700; line-height:1.15; margin:10px 0; }
.hero-sub { color:#f8e9e9; font-size:.94rem; margin:0; }
div[data-testid="stVerticalBlockBorderWrapper"] { background:rgba(255,255,255,.9); border:1px solid var(--line); border-radius:18px; }
div[data-testid="stForm"] { background:#fff; padding:20px; border-radius:18px; border:1px solid var(--line); }
div.stButton > button { border-radius:13px; min-height:44px; font-weight:700; }
div.stButton > button[kind="primary"] { background:var(--maroon); border:1px solid var(--maroon); color:white; width:100%; }
div.stButton > button[kind="secondary"] { border:1px solid #d9c4c6; color:var(--maroon); background:#fff; }
.stTextInput input, .stNumberInput input, div[data-baseweb="select"] > div { border-radius:11px!important; border-color:#e5d7d4!important; background:#fff!important; }

/* Teks pilihan jam booking: hitam dan tidak transparan */
[data-testid="stRadio"] label,
[data-testid="stRadio"] label p,
[data-testid="stRadio"] label span,
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    color: #000000 !important;
    opacity: 1 !important;
}

/* Label Data Diri */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stTextInput"] label,
[data-testid="stTextInput"] label p {
    color: #000000 !important;
    opacity: 1 !important;
    font-weight: 600 !important;
}

/* Teks yang diketik di kolom Nama, WhatsApp, dan Email */
[data-testid="stTextInput"] input {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    opacity: 1 !important;
}

/* Placeholder dibuat abu-abu gelap agar terbaca */
[data-testid="stTextInput"] input::placeholder {
    color: #555555 !important;
    -webkit-text-fill-color: #555555 !important;
    opacity: 1 !important;
}

div[data-testid="stAlert"] { border-radius:13px; }
.small-note { color:var(--muted); font-size:.82rem; text-align:center; padding-top:12px; }
@media(max-width:640px) { .block-container{padding:1rem .8rem 2rem;} .hero{padding:25px 15px;} .hero-title{font-size:2rem;} .brandbar{padding:11px 13px;} .brandtag{font-size:.65rem;} }
</style>
""", unsafe_allow_html=True)


def rupiah(amount):
    return "Rp" + f"{amount:,.0f}".replace(",", ".")


def get_operating_settings():
    """Ambil jam operasional dari Supabase; gunakan default jika belum tersimpan."""
    defaults = {
        "open_time": DEFAULT_OPEN.strftime("%H:%M"),
        "close_time": DEFAULT_CLOSE.strftime("%H:%M"),
        "interval": DEFAULT_INTERVAL,
    }
    try:
        result = (
            supabase.table(SETTINGS_TABLE)
            .select("setting_value")
            .eq("setting_key", "operating_hours")
            .execute()
        )
        if result.data:
            saved = result.data[0].get("setting_value") or {}
            defaults.update(saved)
    except Exception:
        # Pengaturan default tetap bisa dipakai. Admin akan diberi instruksi jika tabel belum dibuat.
        pass
    return defaults


def generate_slots(open_text, close_text, interval):
    """Buat slot mulai dari jam buka hingga sebelum jam tutup."""
    opening = datetime.strptime(open_text, "%H:%M")
    closing = datetime.strptime(close_text, "%H:%M")
    if closing <= opening:
        return []
    slots = []
    current = opening
    while current < closing:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=int(interval))
    return slots


def booked_slots(day):
    result = (
        supabase.table(BOOKINGS_TABLE)
        .select("booking_time")
        .eq("booking_date", day.isoformat())
        .neq("status", "Dibatalkan")
        .execute()
    )
    return {str(row["booking_time"])[:5] for row in (result.data or []) if row.get("booking_time")}


def page_header(admin=False):
    label = "ADMIN" if admin else ""
    st.markdown(
        f'<div class="brandbar"><div class="brandname">SNAPKLIK<span style="color:#d5a4ac">.</span> {label}</div>'
        '<div class="brandtag">PHOTOBOX BOOKING</div></div>',
        unsafe_allow_html=True,
    )


# ============================================================
# NAVIGASI
# ============================================================
page = st.sidebar.radio("Menu", ["Booking Customer", "Admin"], label_visibility="visible")

# ============================================================
# ADMIN
# ============================================================
if page == "Admin":
    page_header(admin=True)
    st.markdown('<h2>Dashboard Admin</h2>', unsafe_allow_html=True)

    configured_password = os.environ.get("SNAPKLIK_ADMIN_PASSWORD", "")
    try:
        configured_password = st.secrets.get("admin_password", configured_password)
    except Exception:
        pass

    if not configured_password:
        st.warning("Password admin belum diatur.")
        st.code('admin_password = "GANTI_DENGAN_PASSWORD_KUAT"', language="toml")
        st.caption("Tambahkan pada Streamlit Secrets. Jangan bagikan password kepada pelanggan.")
        st.stop()

    if not st.session_state.get("admin_logged_in", False):
        with st.form("admin_login"):
            password_input = st.text_input("Password Admin", type="password")
            login = st.form_submit_button("Masuk Admin", type="primary", use_container_width=True)
        if login:
            if hmac.compare_digest(password_input, str(configured_password)):
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Password salah.")
        st.stop()

    top_a, top_b = st.columns([4, 1])
    with top_a:
        st.caption("Atur jam operasional dan kelola jadwal booking.")
    with top_b:
        if st.button("Keluar", key="logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

    # Pengaturan jam operasional
    st.markdown("### Pengaturan Jam Operasional")
    settings = get_operating_settings()
    try:
        current_open = datetime.strptime(settings["open_time"], "%H:%M").time()
        current_close = datetime.strptime(settings["close_time"], "%H:%M").time()
    except Exception:
        current_open, current_close = DEFAULT_OPEN, DEFAULT_CLOSE
    current_interval = int(settings.get("interval", DEFAULT_INTERVAL))

    with st.form("operating_hours_form"):
        c1, c2 = st.columns(2)
        with c1:
            open_time = st.time_input("Jam buka", value=current_open, step=timedelta(minutes=15))
        with c2:
            close_time = st.time_input("Jam tutup", value=current_close, step=timedelta(minutes=15))
        interval = st.selectbox(
            "Jarak antar-slot booking",
            [15, 30, 60],
            index=[15, 30, 60].index(current_interval) if current_interval in [15, 30, 60] else 1,
            format_func=lambda x: f"{x} menit",
        )
        save_hours = st.form_submit_button("Simpan Jam Operasional", type="primary", use_container_width=True)

    if save_hours:
        if close_time <= open_time:
            st.error("Jam tutup harus lebih akhir daripada jam buka.")
        else:
            new_settings = {
                "open_time": open_time.strftime("%H:%M"),
                "close_time": close_time.strftime("%H:%M"),
                "interval": interval,
            }
            try:
                supabase.table(SETTINGS_TABLE).upsert({
                    "setting_key": "operating_hours",
                    "setting_value": new_settings,
                }, on_conflict="setting_key").execute()
                st.success("Jam operasional berhasil disimpan dan langsung diterapkan pada halaman customer.")
                st.rerun()
            except Exception as exc:
                st.error("Pengaturan belum tersimpan. Pastikan tabel app_settings sudah dibuat di Supabase.")
                st.code(str(exc))

    st.caption(
        f"Jam saat ini: {settings.get('open_time')}–{settings.get('close_time')} "
        f"· Slot setiap {settings.get('interval')} menit."
    )
    st.divider()

    # Data booking
    st.markdown("### Data Booking")
    try:
        response = (
            supabase.table(BOOKINGS_TABLE)
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        df = pd.DataFrame(response.data or [])
    except Exception as exc:
        st.error(f"Gagal mengambil data booking: {exc}")
        st.stop()

    if df.empty:
        st.info("Belum ada booking yang masuk.")
        st.stop()

    for col, default in {
        "booking_code": "-", "booking_date": "-", "booking_time": "-",
        "status": "Menunggu konfirmasi", "customer_name": "Pelanggan",
        "phone": "-", "created_at": None
    }.items():
        if col not in df.columns:
            df[col] = default

    total = len(df)
    waiting = int((df["status"] == "Menunggu konfirmasi").sum())
    confirmed = int((df["status"] == "Dikonfirmasi").sum())
    completed = int((df["status"] == "Selesai").sum())
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", total)
    m2.metric("Menunggu", waiting)
    m3.metric("Dikonfirmasi", confirmed)
    m4.metric("Selesai", completed)

    search = st.text_input(
        "Cari booking",
        placeholder="Nama, nomor WhatsApp, kode booking, atau tanggal",
    )
    status_options = ["Semua", "Menunggu konfirmasi", "Dikonfirmasi", "Selesai", "Dibatalkan"]
    chosen_status = st.selectbox("Filter status", status_options)
    filtered = df.copy()
    if chosen_status != "Semua":
        filtered = filtered[filtered["status"] == chosen_status]
    if search.strip():
        q = search.strip().lower()
        searchable_columns = ["booking_code", "booking_date", "customer_name", "phone"]
        mask = pd.Series(False, index=filtered.index)
        for column in searchable_columns:
            if column in filtered.columns:
                mask = mask | filtered[column].fillna("").astype(str).str.lower().str.contains(q, regex=False)
        filtered = filtered[mask]

    for col, default in {"customer_name": "-", "phone": "-", "email": "-"}.items():
        if col not in filtered.columns:
            filtered[col] = default

    display_columns = ["booking_code", "customer_name", "phone", "email", "booking_date", "booking_time", "status"]
    display = filtered[display_columns].rename(columns={
        "booking_code": "Kode Booking",
        "customer_name": "Nama",
        "phone": "WhatsApp",
        "email": "Email",
        "booking_date": "Tanggal",
        "booking_time": "Jam",
        "status": "Status",
    })
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.download_button(
        "Download Data Booking (CSV)",
        data=display.to_csv(index=False).encode("utf-8-sig"),
        file_name="booking_snapklik.csv",
        mime="text/csv",
    )

    st.markdown("### Kelola Status Booking")
    if not filtered.empty:
        codes = filtered["booking_code"].astype(str).tolist()
        selected_code = st.selectbox("Pilih kode booking", codes)
        selected_row = df[df["booking_code"].astype(str) == selected_code].iloc[0]
        st.write(f"**{selected_row['booking_date']} · {str(selected_row['booking_time'])[:5]}**")
        status_list = ["Menunggu konfirmasi", "Dikonfirmasi", "Selesai", "Dibatalkan"]
        current_status = selected_row["status"] if selected_row["status"] in status_list else status_list[0]
        new_status = st.selectbox("Status", status_list, index=status_list.index(current_status))
        if st.button("Simpan Status", type="primary", key="save_status"):
            try:
                supabase.table(BOOKINGS_TABLE).update({"status": new_status}).eq("booking_code", selected_code).execute()
                st.success("Status booking berhasil diperbarui.")
                st.rerun()
            except Exception as exc:
                st.error(f"Gagal memperbarui status: {exc}")

    st.markdown('<div class="small-note">SNAPKLIK ADMIN</div>', unsafe_allow_html=True)
    st.stop()


# ============================================================
# CUSTOMER - HANYA TANGGAL DAN JAM
# ============================================================
page_header()
st.markdown(
    '<div class="hero"><div class="hero-kicker">SNAPKLIK PHOTOBOX</div>'
    '<div class="hero-title">Book Your Session</div>'
    '<p class="hero-sub">Pilih tanggal dan waktu yang tersedia untuk sesi fotomu.</p></div>',
    unsafe_allow_html=True,
)
st.markdown("<h2>Booking Jadwal</h2>", unsafe_allow_html=True)

settings = get_operating_settings()
open_text = settings.get("open_time", DEFAULT_OPEN.strftime("%H:%M"))
close_text = settings.get("close_time", DEFAULT_CLOSE.strftime("%H:%M"))
interval = int(settings.get("interval", DEFAULT_INTERVAL))
slots = generate_slots(open_text, close_text, interval)

st.caption(f"Jam operasional: **{open_text}–{close_text}**")
if not slots:
    st.error("Jadwal belum tersedia. Silakan hubungi admin.")
    st.stop()

today = date.today()
available_dates = [today + timedelta(days=i) for i in range(30)]
selected_date = st.date_input(
    "Pilih tanggal",
    value=today,
    min_value=today,
    max_value=available_dates[-1],
    format="DD/MM/YYYY",
)

try:
    taken = booked_slots(selected_date)
except Exception as exc:
    st.error(f"Tidak dapat memuat jadwal. Silakan coba kembali. Detail: {exc}")
    st.stop()

available_slots = [slot for slot in slots if slot not in taken]
st.markdown("**Pilih jam booking**")
if available_slots:
    selected_time = st.radio(
        "Jam tersedia",
        available_slots,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.caption(f"{len(available_slots)} pilihan waktu tersedia.")

    st.markdown("### Data Diri")
    st.caption("Isi data berikut agar admin SnapKlik dapat menghubungi kamu untuk konfirmasi booking.")
    with st.form("customer_booking_form"):
        customer_name = st.text_input("Nama lengkap *", placeholder="Masukkan nama lengkap")
        phone = st.text_input("Nomor WhatsApp *", placeholder="Contoh: 081234567890")
        email = st.text_input("Email (opsional)", placeholder="nama@email.com")
        submitted = st.form_submit_button(
            "Booking Sekarang",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        clean_phone = re.sub(r"[\s\-+]", "", phone)
        if not customer_name.strip():
            st.error("Nama lengkap wajib diisi.")
        elif not re.fullmatch(r"0\d{8,13}", clean_phone):
            st.error("Nomor WhatsApp belum valid. Gunakan format 08xxxxxxxxxx.")
        elif email.strip() and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
            st.error("Format email belum valid.")
        else:
            booking_code = "SK" + datetime.now().strftime("%y%m%d%H%M%S%f")
            payload = {
                "booking_code": booking_code,
                "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "booking_date": selected_date.isoformat(),
                "booking_time": selected_time,
                "customer_name": customer_name.strip(),
                "phone": clean_phone,
                "email": email.strip() or None,
                # Nilai bawaan menjaga kompatibilitas dengan kolom wajib
                # pada tabel bookings versi aplikasi sebelumnya.
                "studio": "Booking Jadwal",
                "package_name": "Booking Jadwal",
                "background": "-",
                "people": 1,
                "notes": None,
                "total": 0,
                "status": "Menunggu konfirmasi",
            }
            try:
                supabase.table(BOOKINGS_TABLE).insert(payload).execute()
                st.session_state.last_booking_code = booking_code
                st.session_state.last_booking_date = selected_date
                st.session_state.last_booking_time = selected_time
                st.session_state.last_customer_name = customer_name.strip()
                st.session_state.last_customer_phone = clean_phone
                st.session_state.booking_success = True
                st.rerun()
            except Exception as exc:
                error_text = str(exc).lower()
                if "23505" in error_text or "duplicate" in error_text or "unique" in error_text:
                    st.error("Maaf, jam tersebut baru saja dipesan. Silakan pilih jam lainnya.")
                else:
                    st.error(f"Booking belum berhasil disimpan. Detail: {exc}")
else:
    st.warning("Semua jam pada tanggal ini sudah dipesan. Silakan pilih tanggal lain.")

if st.session_state.get("booking_success"):
    st.success("Booking berhasil dicatat!")
    st.markdown("### Detail Booking")
    with st.container(border=True):
        st.caption("KODE BOOKING")
        st.markdown(
            f"<h2 style='text-align:center'>{st.session_state.last_booking_code}</h2>",
            unsafe_allow_html=True,
        )
        st.write(f"**Nama:** {st.session_state.last_customer_name}")
        st.write(f"**WhatsApp:** {st.session_state.last_customer_phone}")
        st.write(f"**Tanggal:** {st.session_state.last_booking_date.strftime('%d/%m/%Y')}")
        st.write(f"**Jam:** {st.session_state.last_booking_time}")
        st.caption("Status: Menunggu konfirmasi admin")
    st.info("Simpan kode booking ini untuk ditunjukkan kepada admin SnapKlik.")

st.markdown('<div class="small-note">SNAPKLIK PHOTOBOX · See you in your photo session ♥</div>', unsafe_allow_html=True)
