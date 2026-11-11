"""Presets: Vollständigkeit, erlaubte Werte, erstes Preset = Standardeinstellungen, Permalink (Einrasten), Namen und Auswahlen."""

import lks_constants as C
import lks_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_allowed():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            if spec.options:
                assert preset[key] in spec.options, (name, key)
            else:
                assert spec.lo <= preset[key] <= spec.hi, (name, key)


def test_default_preset_equals_the_default_settings():
    erstes = C.PRESETS[next(iter(C.PRESETS))]
    assert {P.PRESET_KEYS[k]: v for k, v in erstes.items()} == {k: s.default for k, s in P.SETTING_SPECS.items()}


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_presets_differ_in_at_least_one_setting():
    werte = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(werte)) == len(werte)


def test_handbeispiel_preset_stellt_seed_20_und_voreinstellungen_ein():
    p = C.PRESETS["Handbeispiel"]
    assert p["seed"] == 20 == C.HAND_SEED and p["cb"] == 2.3 and p["eps"] == 0.9 and p["formel"] == C.FORMEL_HAND
    assert p["flips"] == 300000 and p["konflikte"] == 20000


def test_url_parameter_sind_eindeutig():
    namen = [s.url_param for s in P.SETTING_SPECS.values()]
    assert len(namen) == len(set(namen))


def test_permalink_rastet_auf_erlaubte_werte_ein():
    cb = P.SETTING_SPECS["cb"]
    assert P.einrasten(cb, "2.31") == 2.3 and P.einrasten(cb, "2.05") == 2.06 and P.einrasten(cb, "99") == 3.5 and P.einrasten(cb, "abc") is None
    seed = P.SETTING_SPECS["seed"]
    assert P.einrasten(seed, "20") == 20 and P.einrasten(seed, "-5") == 0 and P.einrasten(seed, "9999999999") == C.SEED_MAX and P.einrasten(seed, "x") is None
    text = P.SETTING_SPECS["fall"]
    assert P.einrasten(text, C.FAELLE["schubfach5"]) == C.FAELLE["schubfach5"] and P.einrasten(text, "gibt es nicht") is None
    assert P.einrasten(P.SETTING_SPECS["zufall_n"], "250") in (150, 300) and P.einrasten(P.SETTING_SPECS["zufall_v"], "4.25") == 4.26


def test_auswahlen_haben_eindeutige_labels_und_schluessel():
    assert len(C.STRUKTUR_LABELS) == len(set(C.STRUKTUR_LABELS)) == len(C.STRUKTUREN)
    assert len(C.FALL_LABELS) == len(set(C.FALL_LABELS)) == len(C.FAELLE)
    for k, label in C.STRUKTUREN.items():
        assert C.STRUKTUR_VON_LABEL[label] == k
    for k, label in C.FAELLE.items():
        assert C.FALL_VON_LABEL[label] == k


def test_budget_optionen_enthalten_die_referenzbudgets():
    assert C.BUDGET_REFERENZ_FLIPS in C.FLIP_OPTIONEN and C.BUDGET_REFERENZ_KONFLIKTE in C.KONFLIKT_OPTIONEN
    assert max(C.FLIP_OPTIONEN) == 300000 and C.LIVE_N[1] == 150
