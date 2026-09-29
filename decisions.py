"""Explanations of a bot's shop decisions (Playerbots 2.2.39+): why an item
landed on a counter and how its price was calculated, step by step. The
engine writes this to log.playerbot_listing (and log.playerbot_equip for
equipment swaps, not yet surfaced here) whenever EXPLAIN retention is on
(7 days by default, per Tieru's changelog -- confirmed live: rows started
appearing on this server the moment it updated to 2.2.41).

decision_tables.py holds the enum vocabularies, ported verbatim from Tieru's
own classic admin_panel.py (the reference implementation) rather than
guessed. This module ports just enough of its decode logic (decode_explain_pairs,
_dx_param/_dx_fill, decision_step_rows, explain_listing) to show the same
information here, picking Polish or English server-side by ui_language
instead of a fourth {pl,en,de,tr} dict slot.

Scope note: only the shop-listing explanation ships in this pass (the
"dlaczego wystawił i jak wyliczył cenę" the operator asked about first).
Equipment-swap explanations and the standalone /decisions page are a
natural follow-up, using the same tables.
"""
import re

from decision_tables import (
    DECISION_CODE_NAMES, DECISION_ENUMS, DECISION_EVENTS, DECISION_GOODS,
    DECISION_OFF, DECISION_SHAPES, DECISION_STAND, DECISION_STEPS,
)

_DX_SLOT = re.compile(r"\{(value|a|b|c)\}")


def _pick(texts, lang):
    return texts.get(lang) or texts.get("en") or ""


def _int_text(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return str(value)
    return ("-" if n < 0 else "") + "{:,}".format(abs(n)).replace(",", " ")


def _dec_text(value, digits, lang):
    text = ("%." + str(int(digits)) + "f") % float(value)
    return text if lang == "en" else text.replace(".", ",")


def decode_explain_pairs(text):
    """A steps/terms column as [(code, value, a, b, c)], and whether it was
    cut short (trailing "~", the core ran out of column room)."""
    out, cut = [], False
    for part in str(text or "").split(";"):
        part = part.strip()
        if not part:
            continue
        if part == "~":
            cut = True
            continue
        code, sep, rest = part.partition("=")
        if not sep:
            continue
        try:
            numbers = [int(x) for x in rest.split(":")][:4]
            code = int(code)
        except ValueError:
            continue
        numbers += [0] * (4 - len(numbers))
        out.append((code, numbers[0], numbers[1], numbers[2], numbers[3]))
    return out, cut


def decision_code_name(prefix, code):
    code = int(code or 0)
    return DECISION_CODE_NAMES.get(prefix, {}).get(code) or "%s_%d" % (prefix, code)


def _dx_unknown(code, raw, lang):
    params = ", ".join("%s=%s" % (k, raw[k]) for k in ("value", "a", "b", "c") if raw.get(k))
    base = "code %d" % code if lang == "en" else "kod %d" % code
    return base + (" (" + params + ")" if params else "")


def _dx_param(kind, raw, params, lang, item_name, apply_text):
    """One number of a code, written by its kind. `item_name(vnum)` and
    `apply_text(apply_type, value)` are injected from app.py so this module
    doesn't need its own DB/ITEM_DEFS access."""
    try:
        raw = int(raw or 0)
    except (TypeError, ValueError):
        return str(raw)
    if kind in ("int", "yang"):
        return _int_text(raw)
    if kind == "plus":
        return "+%d" % raw
    if kind == "level":
        return str(raw)
    if kind == "pct":
        return "%d%%" % raw
    if kind == "pctsigned":
        return ("+%d%%" % raw) if raw > 0 else ("%d%%" % raw)
    if kind == "permille":
        return "%d‰" % raw
    if kind == "x100":
        return "×" + _dec_text(raw / 100.0, 2, lang)
    if kind == "x10000":
        return "×" + _dec_text(raw / 10000.0, 4, lang)
    if kind == "minutes":
        return "%d %s" % (raw, "min" if lang == "en" else "min")
    if kind == "item":
        return item_name(raw) if raw > 0 else "—"
    if kind == "apply":
        return apply_text(raw, 0).rsplit(" ", 1)[0] if raw else "—"
    if kind.startswith("applyval:"):
        ref = params.get(kind[len("applyval:"):], 0)
        full = apply_text(ref, raw) if ref else ""
        return full.rsplit(" ", 1)[-1] if full else str(raw)
    if kind.startswith("enum:"):
        entry = DECISION_ENUMS.get(kind[len("enum:"):], {}).get(raw)
        return _pick(entry, lang) if entry else str(raw)
    return str(raw)


def _dx_fill(template, kinds, raw, lang, item_name, apply_text):
    def one(match):
        name = match.group(1)
        return _dx_param(kinds.get(name, "int"), raw.get(name, 0), raw, lang, item_name, apply_text)
    return _DX_SLOT.sub(one, template)


def decision_label(table, code, lang):
    entry = table.get(int(code or 0))
    return _pick(entry, lang) if entry else (str(code))


def decision_goods_text(code, a, b, c, lang, item_name, apply_text):
    entry = DECISION_GOODS.get(int(code or 0))
    raw = {"a": a or 0, "b": b or 0, "c": c or 0}
    if not entry:
        return _dx_unknown(int(code or 0), raw, lang)
    kinds, texts = entry
    return _dx_fill(_pick(texts, lang), kinds, raw, lang, item_name, apply_text)


def decision_step_rows(text, lang, item_name, apply_text):
    """A price-steps column as rows of (name, detail, effect on the running
    price, price after this step); and whether the column was cut short."""
    steps, cut = decode_explain_pairs(text)
    rows, running = [], None
    for code, value, a, b, c in steps:
        raw = {"value": value, "a": a, "b": b, "c": c}
        entry = DECISION_STEPS.get(code)
        if entry:
            value_kind, kinds, names, details = entry
            kinds = dict(kinds)
            if value_kind:
                kinds["value"] = value_kind
            label = _pick(names, lang)
            detail = _dx_fill(_pick(details, lang), kinds, raw, lang, item_name, apply_text)
        else:
            value_kind, label, detail = None, _dx_unknown(code, {}, lang), _dx_unknown(code, raw, lang)
        effect = shown = ""
        if value_kind is None:
            shown = _int_text(value)
            if running is not None and running:
                ratio = float(value) / float(running)
                if ratio >= 2.0 or ratio <= 0.5:
                    effect = "×" + _dec_text(ratio, 2, lang)
                else:
                    change = (ratio - 1.0) * 100.0
                    effect = ("+" if change > 0 else "") + _dec_text(change, 1, lang) + "%"
            running = value
        rows.append({"name": label, "detail": detail, "effect": effect, "value": shown})
    return rows, cut


_LISTING_END_EVENTS = frozenset((8, 9, 10))
_LISTING_CHANGE_EVENTS = frozenset((4, 5, 6, 7))


def explain_listing(row, lang, item_name, apply_text, counter_price=None):
    """One row of log.playerbot_listing, in the panel's current language:
    why the item is goods and on this counter, the price step by step, what
    happened to it since, and (for a still-listed line) whether the
    counter's current price still matches what was last explained."""
    count = int(row.get("count") or 0)
    goods = decision_goods_text(row.get("why"), row.get("why_a"), row.get("why_b"), row.get("why_c"),
                                 lang, item_name, apply_text)
    stand = int(row.get("stand_reason") or 0)
    stand_text = (("Stragan: " if lang != "en" else "Stall: ") + decision_label(DECISION_STAND, stand, lang)) if stand else ""
    list_event = int(row.get("list_event") or 0)
    steps, steps_cut = decision_step_rows(row.get("list_steps"), lang, item_name, apply_text)
    last_event = int(row.get("last_event") or 0)
    last = None
    if last_event in _LISTING_CHANGE_EVENTS:
        last_steps, last_cut = decision_step_rows(row.get("last_steps"), lang, item_name, apply_text)
        last = {"title": decision_label(DECISION_EVENTS, last_event, lang), "steps": last_steps, "steps_cut": last_cut,
                "was": _int_text(row.get("was")), "now": _int_text(row.get("price"))}
    end = ""
    if last_event in _LISTING_END_EVENTS:
        if last_event == 10:
            end = ("Sprzedane za " if lang != "en" else "Sold for ") + _int_text(row.get("sold_price")) + " Yang"
        else:
            end = decision_label(DECISION_OFF, row.get("off_reason"), lang)
    explained = int(row.get("price") or 0) or int(row.get("list_price") or 0)
    price_note = ""
    if counter_price is not None and explained and int(counter_price or 0) != explained and last_event not in _LISTING_END_EVENTS:
        price_note = (
            "Cena na ladzie (%s) różni się od wyjaśnionej (%s) — tej zmiany nic nie zapisało."
            % (_int_text(counter_price), _int_text(explained)) if lang != "en" else
            "The counter's price (%s) differs from the explained one (%s) — nothing recorded that change."
            % (_int_text(counter_price), _int_text(explained))
        )
    return {
        "goods": goods, "stand": stand_text,
        "listed_event": decision_label(DECISION_EVENTS, list_event, lang) if list_event else "",
        "listed_time": _dx_time(row.get("listed_at")),
        "steps": steps, "steps_cut": steps_cut,
        "last": last, "end": end, "last_time": _dx_time(row.get("last_at")),
        "price": _int_text(explained) if explained else "", "price_note": price_note,
        "count": count,
    }


def _dx_time(value):
    if hasattr(value, "strftime"):
        return value.strftime("%d.%m %H:%M")
    return str(value or "")
