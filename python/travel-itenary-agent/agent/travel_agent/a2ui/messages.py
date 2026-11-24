"""Typed builders for A2UI v1.0 server-to-client messages.

Spec: https://a2ui.org (protocol v1.0). Four message types:

* ``createSurface``    : open a rendering area tied to a component catalog
* ``updateComponents`` : add/replace components (a flat list; children by ID)
* ``updateDataModel``  : set a value at a JSON Pointer path in the surface's data
* ``deleteSurface``    : remove the surface

Every message carries ``"version": "1.0"``. The builders add it so callers can't forget.
Component helpers (``text``, ``button``…) return plain dicts in the v1.0 shape:
``{"id": ..., "component": "Text", ...props}``.

What changed from v0.9, and where this module handles it:

* ``"version": "1.0"`` (no ``v``) and the v1 basic catalog id.
* Data bindings are ``{"@path": ...}`` and function calls ``{"@call": ...}`` (``bind`` / ``call``).
* ``createSurface`` has no ``theme``; the client styles surfaces with CSS variables.
* Component ids must be identifiers (``it_day_title``, not ``it-day-title``): checked here.
* ``Text`` only has ``body`` / ``caption``; headings are Markdown. ``text(..., variant="h2")``
  still works and emits ``## ...`` for you.
"""

from __future__ import annotations

import re
from typing import Any, Literal

A2UI_VERSION = "1.0"
# ID of the standard component catalog that ships with @a2ui/web_core (v1.0).
BASIC_CATALOG_ID = "https://a2ui.org/specification/v1_0/catalogs/basic/catalog.json"
# v1.0 requires component ids to be identifiers (UAX #31); we allow the ASCII subset.
_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

Message = dict[str, Any]
Component = dict[str, Any]


# --- messages ---------------------------------------------------------------

def create_surface(
    surface_id: str,
    catalog_id: str = BASIC_CATALOG_ID,
    *,
    send_data_model: bool | None = None,
) -> Message:
    body: dict[str, Any] = {"surfaceId": surface_id, "catalogId": catalog_id}
    if send_data_model is not None:
        body["sendDataModel"] = send_data_model
    return {"version": A2UI_VERSION, "createSurface": body}


def update_components(surface_id: str, components: list[Component]) -> Message:
    ids = [c["id"] for c in components]
    bad = [i for i in ids if not _ID.match(i)]
    if bad:
        raise ValueError(f"Component ids must be identifiers in A2UI v1.0 (use '_', not '-'): {bad}")
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        raise ValueError(f"Duplicate component ids: {dupes}")
    return {"version": A2UI_VERSION, "updateComponents": {"surfaceId": surface_id, "components": components}}


def update_data_model(surface_id: str, value: Any, path: str = "/") -> Message:
    if not path.startswith("/"):
        raise ValueError("path must be a JSON Pointer starting with '/'")
    return {"version": A2UI_VERSION, "updateDataModel": {"surfaceId": surface_id, "path": path, "value": value}}


def delete_surface(surface_id: str) -> Message:
    return {"version": A2UI_VERSION, "deleteSurface": {"surfaceId": surface_id}}


# --- dynamic values -----------------------------------------------------------

def bind(path: str) -> dict[str, str]:
    """A data binding: the value comes from the surface's data model at ``path``."""
    return {"@path": path}


def call(fn: str, return_type: str = "boolean", **args: Any) -> dict[str, Any]:
    """A client-side function call from the catalog (e.g. ``required``, ``formatString``)."""
    return {"@call": fn, "args": args, "returnType": return_type}


def fmt(template: str) -> dict[str, Any]:
    """``formatString`` interpolation, e.g. ``fmt("Budget: ${/trip/budget}")``."""
    return call("formatString", "string", value=template)


def check(condition: Any, message: str) -> dict[str, Any]:
    return {"condition": condition, "message": message}


# --- basic-catalog components -------------------------------------------------

def _c(id_: str, component: str, **props: Any) -> Component:
    return {"id": id_, "component": component, **{k: v for k, v in props.items() if v is not None}}


TextVariant = Literal["h1", "h2", "h3", "h4", "h5", "caption", "body"]
_HEADING = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### ", "h5": "##### "}


def _as_heading(value: Any, prefix: str) -> Any:
    """v1.0 has no heading variants: turn the text into a Markdown heading."""
    if isinstance(value, str):
        return prefix + value
    if isinstance(value, dict) and "@path" in value:  # bound text: "## ${/path}"
        return fmt(f"{prefix}${{{value['@path']}}}")
    if isinstance(value, dict) and value.get("@call") == "formatString":
        return fmt(prefix + value["args"]["value"])
    raise ValueError("Headings need literal, bound or formatString text; use variant=None for other calls")


def text(id_: str, value: Any, variant: TextVariant | None = None, *, weight: float | None = None) -> Component:
    if variant in _HEADING:
        return _c(id_, "Text", text=_as_heading(value, _HEADING[variant]), weight=weight)
    return _c(id_, "Text", text=value, variant=variant, weight=weight)


Children = list[str] | dict[str, str]


def template(component_id: str, path: str) -> dict[str, str]:
    """Dynamic children: render ``component_id`` once per item of the list at ``path``.

    Inside the template, relative paths (no leading ``/``) read from the current item.
    """
    return {"componentId": component_id, "path": path}


def column(id_: str, children: Children, *, align: str | None = None, justify: str | None = None,
           weight: float | None = None) -> Component:
    return _c(id_, "Column", children=children, align=align, justify=justify, weight=weight)


def row(id_: str, children: Children, *, align: str | None = None, justify: str | None = None,
        weight: float | None = None) -> Component:
    return _c(id_, "Row", children=children, align=align, justify=justify, weight=weight)


def card(id_: str, child: str, *, weight: float | None = None) -> Component:
    return _c(id_, "Card", child=child, weight=weight)


def divider(id_: str) -> Component:
    return _c(id_, "Divider")


def icon(id_: str, name: str) -> Component:
    return _c(id_, "Icon", name=name)


def checkbox(id_: str, label: Any, value: Any) -> Component:
    return _c(id_, "CheckBox", label=label, value=value)


def currency(value: Any, code: str = "USD") -> dict[str, Any]:
    """Client-side ``formatCurrency``: the renderer formats the number for the user's locale."""
    return call("formatCurrency", "string", value=value, currency=code, decimals=0)


def text_field(id_: str, label: Any, value: Any, *, variant: str | None = None,
               checks: list[dict[str, Any]] | None = None, weight: float | None = None) -> Component:
    return _c(id_, "TextField", label=label, value=value, variant=variant, checks=checks, weight=weight)


def date_input(id_: str, label: Any, value: Any, *, min_: Any = None, weight: float | None = None) -> Component:
    return _c(id_, "DateTimeInput", label=label, value=value, enableDate=True, min=min_, weight=weight)


def slider(id_: str, label: Any, value: Any, *, min_: float, max_: float) -> Component:
    return _c(id_, "Slider", label=label, value=value, min=min_, max=max_)


def choice_picker(id_: str, label: Any, options: list[tuple[str, str]], value: Any, *,
                  multiple: bool = True, chips: bool = True) -> Component:
    return _c(
        id_,
        "ChoicePicker",
        label=label,
        options=[{"label": lbl, "value": val} for val, lbl in options],
        value=value,
        variant="multipleSelection" if multiple else "mutuallyExclusive",
        displayStyle="chips" if chips else "checkbox",
    )


def button(id_: str, label_id: str, action_name: str, context: dict[str, Any] | None = None, *,
           primary: bool = False, borderless: bool = False,
           checks: list[dict[str, Any]] | None = None) -> Component:
    """A Button whose click sends a server event. Its child must be a Text with id ``label_id``."""
    event: dict[str, Any] = {"name": action_name}
    if context:
        event["context"] = context
    return _c(id_, "Button", child=label_id, action={"event": event},
              variant="primary" if primary else ("borderless" if borderless else None), checks=checks)
