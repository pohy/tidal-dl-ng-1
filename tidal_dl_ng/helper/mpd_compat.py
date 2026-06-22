"""Compatibility shims for parsing TIDAL's MPEG-DASH manifests.

TIDAL emits MPD manifests that violate the DASH schema in minor ways, e.g.
`<AdaptationSet ... group="main">` where `group` is defined as an unsignedInt.
The strict `mpegdash` parser raises `ValueError: invalid literal for int()`
on these, which surfaces as `ManifestDecodeError` and aborts every download.

This module patches `mpegdash.utils.parse_attr_value` so that a failed numeric
conversion falls back to the raw string instead of raising. Import it once
before any manifest is parsed.
"""

import mpegdash.nodes as _mpd_nodes
import mpegdash.utils as _mpd_utils

_PATCHED_FLAG = "_tidal_dl_ng_lenient"


def apply() -> None:
    """Monkeypatch mpegdash to tolerate non-spec attribute values. Idempotent."""
    if getattr(_mpd_utils.parse_attr_value, _PATCHED_FLAG, False):
        return

    _orig = _mpd_utils.parse_attr_value

    def parse_attr_value(xmlnode, attr_name, value_type):
        try:
            return _orig(xmlnode, attr_name, value_type)
        except (ValueError, TypeError):
            # Non-spec value (e.g. group="main"): keep the raw string.
            if attr_name not in xmlnode.attributes:
                return None

            return xmlnode.attributes[attr_name].nodeValue

    setattr(parse_attr_value, _PATCHED_FLAG, True)
    _mpd_utils.parse_attr_value = parse_attr_value
    # `mpegdash.nodes` imports the symbol directly, so patch that binding too.
    _mpd_nodes.parse_attr_value = parse_attr_value
