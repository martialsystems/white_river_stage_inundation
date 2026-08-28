# Copyright (c) 2026 Martial Systems LLC


class GateError(RuntimeError):
    """Stage hard gate failed."""


class ClaimBanError(GateError):
    """Report text hit a banned claim."""


class SiblingShaError(GateError):
    """Sibling HAND/P/FIRM grid does not match the locked transform."""


class ChannelUnlockedError(GateError):
    """Wet mask requested before h_channel is locked."""


class RatingError(GateError):
    """Stage is off the published rating, or the rating is empty."""


class FetchError(RuntimeError):
    """NWIS or NHD download failed."""
