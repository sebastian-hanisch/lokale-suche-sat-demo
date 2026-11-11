"""Permalink (Begrenzen/Einrasten), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio).

Die Regler mit festen Werten (`options`) rasten ein: ein Wert aus der Adresszeile wird auf den nächsten erlaubten Wert gesetzt (Zahlen)
bzw. verworfen (Text, der nicht zur Auswahl gehört). Der Zufalls-Seed ist ein Zahlenfeld mit Grenzen (`lo`, `hi`). Zu den Einstellungen
zählen auch die Auswahlen im Hauptbereich (Formel, Messzelle, Aufgabe, Fall): ein Preset setzt sie, und ihre Änderung hebt die Markierung auf.
"""

from dataclasses import dataclass

import streamlit as st

import lks_constants as C
from lks_rng import SplitMix64


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    options: tuple = ()
    lo: int | None = None
    hi: int | None = None


_ERSTES = C.PRESETS[next(iter(C.PRESETS))]
SETTING_SPECS = {
    "seed": SettingSpec("seed", int, _ERSTES["seed"], lo=0, hi=C.SEED_MAX),
    "flips": SettingSpec("flips", int, _ERSTES["flips"], C.FLIP_OPTIONEN),
    "konflikte": SettingSpec("konflikte", int, _ERSTES["konflikte"], C.KONFLIKT_OPTIONEN),
    "cb": SettingSpec("cb", float, _ERSTES["cb"], C.CB_OPTIONEN),
    "eps": SettingSpec("eps", float, _ERSTES["eps"], C.EPS_OPTIONEN),
    "formel": SettingSpec("formel", str, _ERSTES["formel"], C.FORMELN),
    "zufall_n": SettingSpec("zn", int, _ERSTES["zufall_n"], C.ZUFALL_N),
    "zufall_v": SettingSpec("zv", float, _ERSTES["zufall_v"], C.VERHAELTNISSE),
    "struktur": SettingSpec("struktur", str, _ERSTES["struktur"], C.STRUKTUR_LABELS),
    "fall": SettingSpec("fall", str, _ERSTES["fall"], C.FALL_LABELS),
}
PRESET_KEYS = {k: k for k in SETTING_SPECS}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def einrasten(spec: SettingSpec, roh):
    """Wert aus der Adresszeile auf einen erlaubten Wert bringen (Zahlen: nächster erlaubter, Grenzen), sonst None."""
    try:
        wert = spec.caster(roh)
    except (ValueError, TypeError):
        return None
    if not spec.options:
        return max(spec.lo, min(spec.hi, wert))
    if spec.caster in (int, float):
        return min(spec.options, key=lambda o: abs(o - wert))
    return wert if wert in spec.options else None


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf erlaubte Werte begrenzt."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            wert = einrasten(spec, qp[spec.url_param])
            if wert is not None:
                st.session_state[state_key] = wert
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen Standardwert)
    mit dem Session State. Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def _naechster_seed() -> int:
    """Neuer Zufalls-Seed aus einem Zähler der Sitzung über SplitMix64 (kein Python-`random`)."""
    st.session_state["seed_zaehler"] = st.session_state.get("seed_zaehler", 0) + 1
    return SplitMix64(1000 + st.session_state["seed_zaehler"]).below(C.SEED_MAX + 1)


def randomize_seed():
    st.session_state["seed"] = _naechster_seed()


def randomize_klein_seed():
    st.session_state["klein_seed"] = _naechster_seed()
