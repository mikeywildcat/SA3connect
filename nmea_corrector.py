"""NMEA sentence correction and AIS own-boat filtering.

Corrections applied before relaying to downstream navigation apps:

1. $SLCLI (Sailaway heel) → $IIXDR,A,<heel>,D,ROLL
   Sailaway uses +port / -starboard convention; NMEA XDR uses -port / +starboard.
   Sign is inverted on conversion.

2. $RIRSA (Sailaway rudder) → $IIRSA,<angle>,A,,V
   Reformats to the standard RSA sentence talker/format.

3. $WIMWV angles > 180° are rewritten as negative (±180° signed).
   This corrects the port-side wind angle representation for downstream apps.

4. AIS sentences from own boat are filtered out to prevent echo of own vessel.
"""

from __future__ import annotations

import logging

_logger = logging.getLogger(__name__)

# AIS payload armoring table (6-bit ASCII)
_AIS_ARMOR = "0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVW`abcdefghijklmnopqrstuvw"


def nmea_checksum(body: str) -> str:
    """Return two-hex-digit XOR checksum for an NMEA sentence body (no $ or *)."""
    chk = 0
    for ch in body:
        chk ^= ord(ch)
    return f"{chk:02X}"


def correct_sentence(sentence: str, own_boat_id: str | None = None) -> str | None:
    """Return a corrected/standardised NMEA sentence, or None to drop it.

    Args:
        sentence: Raw NMEA line received from Sailaway (may or may not have checksum).
        own_boat_id: Sailaway boat ID (e.g. "6246") used to filter own-boat AIS sentences.

    Returns:
        Corrected sentence string (with CRLF), or None if the sentence should be dropped.
    """
    line = sentence.strip()
    if not line:
        return None

    # --- Drop own-boat AIS sentences ---
    if own_boat_id and _is_own_boat_ais(line, own_boat_id):
        return None

    # --- Proprietary sentence conversions ---
    if line.startswith("$SLCLI"):
        return _convert_slcli_to_xdr(line)

    if line.startswith("$RIRSA"):
        return _convert_rirsa_to_rsa(line)

    if line.startswith("$WIMWV") or line.startswith("$IIMWV"):
        return _fix_mwv_angle(line)

    # All other sentences pass through unchanged (preserve original checksum).
    if not sentence.endswith("\n"):
        return sentence + "\r\n"
    return sentence


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def _strip_checksum(line: str) -> str:
    """Remove trailing *XX checksum and return the raw sentence body."""
    star = line.rfind("*")
    return line[:star] if star != -1 else line


def _build_sentence(body_with_dollar: str) -> str:
    """Given '$TALKER,...', compute checksum and return full sentence with CRLF."""
    body = body_with_dollar[1:]  # strip leading $
    return f"{body_with_dollar}*{nmea_checksum(body)}\r\n"


def _convert_slcli_to_xdr(line: str) -> str:
    """$SLCLI,<heel> → $IIXDR,A,<heel_inverted>,D,ROLL*XX"""
    try:
        raw = _strip_checksum(line)
        parts = raw.split(",")
        if len(parts) < 2:
            return line + "\r\n"
        heel_sa = float(parts[1])
        heel_nmea = -heel_sa  # invert Sailaway sign convention
        body = f"$IIXDR,A,{heel_nmea:.1f},D,ROLL"
        return _build_sentence(body)
    except Exception as exc:
        _logger.debug("SLCLI conversion failed: %s", exc)
        return line + "\r\n"


def _convert_rirsa_to_rsa(line: str) -> str:
    """$RIRSA,<angle>,<status>,... → $IIRSA,<angle>,<status>,,V*XX"""
    try:
        raw = _strip_checksum(line)
        parts = raw.split(",")
        if len(parts) < 2:
            return line + "\r\n"
        angle = float(parts[1])
        status = parts[2].strip() if len(parts) >= 3 else "A"
        body = f"$IIRSA,{angle:.1f},{status},,V"
        return _build_sentence(body)
    except Exception as exc:
        _logger.debug("RIRSA conversion failed: %s", exc)
        return line + "\r\n"


def _fix_mwv_angle(line: str) -> str:
    """Rewrite WIMWV/IIMWV angles > 180° as negative (±180° signed convention)."""
    try:
        raw = _strip_checksum(line)
        parts = raw.split(",")
        # MWV: $--MWV,<angle>,<R/T>,<speed>,<units>,<status>
        if len(parts) < 5:
            return line + "\r\n"
        try:
            angle = float(parts[1])
        except ValueError:
            return line + "\r\n"
        if angle > 180.0:
            parts[1] = f"{angle - 360.0:.1f}"
            body = ",".join(parts)
            # Recalculate checksum (body starts with $)
            return _build_sentence(body)
        # Angle already in valid range; just ensure line ending
        if not line.endswith("\n"):
            return line + "\r\n"
        return line
    except Exception as exc:
        _logger.debug("MWV correction failed: %s", exc)
        return line + "\r\n"


# ---------------------------------------------------------------------------
# AIS own-boat filtering
# ---------------------------------------------------------------------------

def _payload_to_bits(payload: str) -> str:
    bits = ""
    for ch in payload:
        val = ord(ch) - 48
        if val > 40:
            val -= 8
        bits += format(val, "06b")
    return bits


def _extract_boat_id_from_mmsi(mmsi: int) -> str | None:
    """Extract Sailaway boat ID from a Sailaway-generated AIS MMSI."""
    s = str(mmsi)
    for prefix_len in (5, 4, 3):
        prefix = s[:prefix_len]
        if prefix in ("24400", "2440", "244"):
            suffix = s[prefix_len:].lstrip("0")
            if suffix:
                return suffix
    return None


def _is_own_boat_ais(line: str, own_boat_id: str) -> bool:
    """Return True if *line* is an AIS sentence from the own boat."""
    try:
        if not (line.startswith("!AIVDM") or line.startswith("!AIVDO")):
            return False
        parts = line.split(",")
        if len(parts) < 6:
            return False
        payload_field = parts[5]
        payload = payload_field.split("*")[0] if "*" in payload_field else payload_field
        if not payload or len(payload) < 7:
            return False
        bits = _payload_to_bits(payload)
        if len(bits) < 38:
            return False
        mmsi = int(bits[8:38], 2)
        extracted = _extract_boat_id_from_mmsi(mmsi)
        return extracted is not None and extracted == own_boat_id
    except Exception:
        return False
