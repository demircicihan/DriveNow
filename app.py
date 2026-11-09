"""DriveNow Premium — Streamlit uygulama girişi.

Çalıştırma:  streamlit run app.py
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from drivenow import db
from drivenow.components import esc, initials
from drivenow.config import APP_NAME, APP_SUFFIX, DEMO_MODE
from drivenow.state import (
    current_user,
    init_state,
    is_guest,
    logout,
    session_expired,
    set_flash,
    show_flash,
    touch_session,
)
from drivenow.theme import inject_theme
from drivenow.views import account, admin, auth, booking, fleet

st.set_page_config(
    page_title=f"{APP_NAME} {APP_SUFFIX} • Araç Kiralama",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": f"{APP_NAME} {APP_SUFFIX} — premium araç kiralama deneyimi.",
    },
)


@st.cache_resource(show_spinner=False)
def _bootstrap() -> bool:
    db.init_db()
    return True


_bootstrap()
inject_theme()
init_state()

# --- Oturum süresi ----------------------------------------------------------
if (
    st.session_state.get("auth")
    and not is_guest()
    and session_expired()
):
    logout()
    set_flash("Oturum süreniz doldu. Güvenliğiniz için tekrar giriş yapın.", "warning")
    st.rerun()
touch_session()


def _topbar() -> None:
    user = current_user() or {}
    guest = is_guest()
    left, right = st.columns([3, 1.15], vertical_alignment="center")

    with left:
        st.markdown(
            '<div class="dn-topbar" style="padding-bottom:6px">'
            '<div class="dn-brand">'
            '<div class="dn-brand-mark">🚗</div>'
            "<div>"
            f'<div class="dn-brand-name">{esc(APP_NAME)} <span>{esc(APP_SUFFIX)}</span></div>'
            '<div class="dn-brand-sub">Premium Araç Kiralama</div>'
            "</div></div></div>",
            unsafe_allow_html=True,
        )

    with right:
        if st.session_state.get("auth") and not guest:
            chip, action = st.columns([2.1, 1], vertical_alignment="center")
            with chip:
                st.markdown(
                    '<div class="dn-user-chip">'
                    f'<div class="dn-avatar">{esc(initials(user.get("ad", "")))}</div>'
                    "<div>"
                    f'<b>{esc(user.get("ad", "Müşteri"))}</b>'
                    f'<small>{esc(user.get("email", "") or "Doğrulanmış üye")}</small>'
                    "</div></div>",
                    unsafe_allow_html=True,
                )
            with action:
                if st.button("Çıkış", width="stretch", key="topbar_logout"):
                    logout()
                    set_flash("Güvenli çıkış yapıldı. Tekrar bekleriz.", "info")
                    st.rerun()
        elif guest:
            chip, action = st.columns([2.1, 1], vertical_alignment="center")
            with chip:
                st.markdown(
                    '<div class="dn-user-chip">'
                    '<div class="dn-avatar">👤</div>'
                    "<div><b>Misafir</b><small>Keşif modu</small></div></div>",
                    unsafe_allow_html=True,
                )
            with action:
                if st.button("Giriş yap", width="stretch", key="topbar_login"):
                    st.session_state["auth"] = False
                    st.session_state["guest"] = False
                    st.session_state["user"] = None
                    st.rerun()


def _login_prompt(title: str, text: str) -> None:
    st.markdown(
        f'<div class="dn-empty"><div class="dn-empty__icon">🔐</div>'
        f"<b>{esc(title)}</b><span>{esc(text)}</span></div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("Giriş ekranına dön", type="primary", width="stretch"):
            st.session_state["auth"] = False
            st.session_state["guest"] = False
            st.session_state["user"] = None
            st.session_state["auth_notice"] = "Devam etmek için lütfen giriş yapın."
            st.rerun()


def _footer() -> None:
    demo = " • Demo modu" if DEMO_MODE else ""
    year = date.today().year
    st.markdown(
        '<div class="dn-footer">'
        f"<div><b>{esc(APP_NAME)} {esc(APP_SUFFIX)}</b> • Premium filo, kapınıza teslim{demo}</div>"
        "<div>destek@drivenow.com.tr • 0850 000 00 00 • Konya / Türkiye</div>"
        f"<div>© {year} DriveNow. Tüm hakları saklıdır.</div>"
        "</div>",
        unsafe_allow_html=True,
    )


# --- Giriş yapılmamış -------------------------------------------------------
if not st.session_state.get("auth"):
    auth.render()
    _footer()
    st.stop()

_topbar()
show_flash()

booking_active = bool(
    st.session_state.get("secili") or st.session_state.get("show_booking_success")
)

if booking_active:
    booking.render()
    _footer()
    st.stop()

NAV_ICONS = {
    "Filo": "🚗",
    "Rezervasyonlarım": "🧾",
    "Hesabım": "👤",
    "Yönetim": "🛠️",
}
nav = st.segmented_control(
    "Gezinme",
    list(NAV_ICONS.keys()),
    key="nav",
    format_func=lambda item: f"{NAV_ICONS[item]} {item}",
    label_visibility="collapsed",
    width="stretch",
    wrap=True,
)
nav = nav or "Filo"

if nav == "Filo":
    fleet.render()
elif nav == "Rezervasyonlarım":
    if is_guest():
        _login_prompt(
            "Rezervasyonlar için giriş gerekli",
            "Misafir modunda yalnızca filoyu keşfedebilirsiniz.",
        )
    else:
        account.render("reservations")
elif nav == "Hesabım":
    if is_guest():
        _login_prompt(
            "Hesabınıza erişmek için giriş yapın",
            "Profil, favoriler ve geçmiş kiralamalar üyelere özeldir.",
        )
    else:
        account.render()
elif nav == "Yönetim":
    admin.render()

_footer()
