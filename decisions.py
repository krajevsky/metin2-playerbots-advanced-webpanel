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
    DECISION_CODE_NAMES, DECISION_ENUMS, DECISION_EVENTS, DECISION_GOODS, DECISION_LFLAGS,
    DECISION_LISTING_UNUSUAL, DECISION_OFF, DECISION_SHAPES, DECISION_SHEET_STEPS, DECISION_STAND,
    DECISION_STEPS, DECISION_TEXTS,
)

# Names this module cannot look up itself; app.py fills these in at import
# (a skill's name by its id, a monster's by its vnum). Without them the
# number is said with its word: "umiejętność #46", "potwór #2091".
NAME_SOURCES = {"skill": None, "mob": None}

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


def _text(key, lang, **values):
    """One of the explanation's framing phrases (DECISION_TEXTS, Tieru's ex_*)."""
    return _pick(DECISION_TEXTS.get(key, {}), lang).format(**values)


def _dx_unknown(code, raw, lang):
    """A code this panel has no words for (a newer core's): its number and parameters."""
    params = ", ".join("%s=%s" % (k, raw[k]) for k in ("value", "a", "b", "c") if raw.get(k))
    return _text("ex_code_n", lang, n=code) + (" (" + params + ")" if params else "")


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
    if kind == "x1000":
        return "×" + _dec_text(raw / 1000.0, 2, lang)
    if kind == "x10000":
        return "×" + _dec_text(raw / 10000.0, 4, lang)
    if kind == "skill":
        name = NAME_SOURCES["skill"](raw) if NAME_SOURCES["skill"] and raw > 0 else None
        return name or (_text("ex_skill_n", lang, n=raw) if raw > 0 else "—")
    if kind == "mob":
        name = NAME_SOURCES["mob"](raw, lang) if NAME_SOURCES["mob"] and raw > 0 else None
        return name or (_text("ex_mob_n", lang, n=raw) if raw > 0 else "—")
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


def _dx_change(before, after, lang):
    """How a step moved the price: "=" when it did not, a percentage, or a multiple when large."""
    if not before or before == after:
        return "=" if before else ""
    ratio = float(after) / float(before)
    if ratio >= 2.0 or ratio <= 0.5:
        return "×" + _dec_text(ratio, 2, lang)
    change = (ratio - 1.0) * 100.0
    return ("+" if change > 0 else "") + _dec_text(change, 1, lang) + "%"


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
            effect = _dx_change(running, value, lang) if running is not None else ""
            running = value
        rows.append({"name": label, "detail": detail, "effect": effect, "value": shown})
    return rows, cut


_LISTING_END_EVENTS = frozenset((8, 9, 10))
_LISTING_CHANGE_EVENTS = frozenset((4, 5, 6, 7))


def decision_flags(flags, lang):
    """A counter line's flag badges, each marked when it is an unusual one."""
    flags, out, bit = int(flags or 0), [], 1
    while bit <= flags:
        if flags & bit:
            entry = DECISION_LFLAGS.get(bit)
            out.append({"label": _pick(entry, lang) if entry else "#%d" % bit,
                        "unusual": bool(bit & DECISION_LISTING_UNUSUAL)})
        bit <<= 1
    return out


def decision_sheet_ratio(row, steps):
    """One unit's price against the sheet's (the first sheet step, with the
    bonus premium after it for gear, and a slip's meant price); None when the
    price came from no sheet."""
    sheet = meant = None
    for code, value, a, _b, _c in steps:
        if code in DECISION_SHEET_STEPS and sheet is None:
            sheet = value
        elif code == 11 and sheet:
            sheet = value
        elif code == 39:
            meant = a
    count = max(1, int(row.get("count") or 0))
    price = meant or int(row.get("list_price") or 0)
    if not sheet or not price:
        return None
    return {"unit": price // count, "sheet": sheet, "ratio": float(price) / count / sheet}


def explain_listing(row, lang, item_name, apply_text, counter_price=None):
    """One row of log.playerbot_listing in the panel's language, the way Tieru's
    panel says it: why the item is goods (and its score), why the stall is
    open, how it was picked and cut from its stack, the price step by step and
    against the sheet, what happened to it since, and its flags."""
    count = int(row.get("count") or 0)
    goods = decision_goods_text(row.get("why"), row.get("why_a"), row.get("why_b"), row.get("why_c"),
                                lang, item_name, apply_text)
    if int(row.get("score") or 0):
        goods += " · " + _text("ex_score", lang, score=_int_text(row.get("score")))
    stand = int(row.get("stand_reason") or 0)
    stand_text = _text("ex_stand", lang, reason=decision_label(DECISION_STAND, stand, lang)) if stand else ""
    candidates = int(row.get("candidates") or 0)
    pick = ""
    if candidates:
        # pick_rank is the index among the scored candidates, 0 the first
        pick = _text("ex_pick", lang, rank=int(row.get("pick_rank") or 0) + 1, n=candidates)
        if int(row.get("refused_above") or 0):
            pick += _text("ex_pick_refused", lang, k=int(row.get("refused_above") or 0))
    cut = ""
    if int(row.get("cut_from") or 0):
        cut = _text("ex_cut", lang, shape=decision_label(DECISION_SHAPES, row.get("cut_shape"), lang),
                    whole=_int_text(row.get("cut_from")), take=_int_text(count), keep=_int_text(row.get("cut_keep")))
    if int(row.get("held") or 0):
        cut += ("; " if cut else "") + _text("ex_held", lang, held=_int_text(row.get("held")))
    list_event = int(row.get("list_event") or 0)
    list_price = int(row.get("list_price") or 0)
    listed_event = decision_label(DECISION_EVENTS, list_event, lang) if list_event else ""
    listed_time = _dx_time(row.get("listed_at"))
    listed = " · ".join(p for p in (listed_event, listed_time,
                                    _text("ex_list_price", lang, price=_int_text(list_price)) if list_price else "") if p)
    steps, steps_cut = decision_step_rows(row.get("list_steps"), lang, item_name, apply_text)
    last_event = int(row.get("last_event") or 0)
    last_time = _dx_time(row.get("last_at"))
    last = None
    if last_event in _LISTING_CHANGE_EVENTS:
        last_steps, last_cut = decision_step_rows(row.get("last_steps"), lang, item_name, apply_text)
        line = _text("ex_was_now", lang, was=_int_text(row.get("was")), now=_int_text(row.get("price")))
        if int(row.get("changes") or 0):
            line += " · " + _text("ex_changes", lang, n=int(row.get("changes") or 0))
        last = {"title": decision_label(DECISION_EVENTS, last_event, lang) + " · " + last_time, "line": line,
                "steps": last_steps, "steps_cut": last_cut,
                "was": _int_text(row.get("was")), "now": _int_text(row.get("price"))}
    end = ""
    if last_event in _LISTING_END_EVENTS:
        if last_event == 10:
            end = _text("ex_end_sold", lang, price=_int_text(row.get("sold_price")))
        else:
            end = _text("ex_end_off", lang, reason=decision_label(DECISION_OFF, row.get("off_reason"), lang))
        end += " · " + last_time
    explained = int(row.get("price") or 0) or list_price
    price_note = ""
    if counter_price is not None and explained and int(counter_price or 0) != explained \
            and last_event not in _LISTING_END_EVENTS:
        price_note = _text("ex_price_differs", lang, now=_int_text(counter_price), explained=_int_text(explained))
    flags = int(row.get("flags") or 0)
    ratio = decision_sheet_ratio(row, decode_explain_pairs(row.get("list_steps"))[0])
    return {
        "goods": goods, "stand": stand_text, "pick": pick, "cut": cut,
        "listed": listed, "listed_event": listed_event, "listed_time": listed_time,
        "steps": steps, "steps_cut": steps_cut,
        "sheet": _text("ex_sheet_ratio", lang, unit=_int_text(ratio["unit"]), sheet=_int_text(ratio["sheet"]),
                       ratio="×" + _dec_text(ratio["ratio"], 2, lang)) if ratio else "",
        "last": last, "end": end, "last_time": last_time,
        "price": _int_text(explained) if explained else "", "price_note": price_note,
        "flags": decision_flags(flags, lang),
        "unusual": _text("ex_unusual", lang) if flags & DECISION_LISTING_UNUSUAL else "",
        "count": count,
    }


def _dx_time(value):
    if hasattr(value, "strftime"):
        return value.strftime("%d.%m %H:%M:%S")
    return str(value or "")
