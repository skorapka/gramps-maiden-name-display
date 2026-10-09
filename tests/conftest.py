"""Make the Gramps library from the macOS app bundle importable without GTK.

Gramps' const/locale modules need GLib and gettext domain functions; for
pure name-display tests these are stubbed. GRAMPSHOME points to a temporary
directory so the real user configuration is never touched.
"""

import locale
import os
import sys
import tempfile
import types
from pathlib import Path

GRAMPS_SITE = os.environ.get(
    "GRAMPS_SITE",
    "/Applications/Gramps.app/Contents/Resources/lib/python3.13/site-packages",
)
_HOME = tempfile.mkdtemp(prefix="gramps-test-home-")
os.environ["GRAMPSHOME"] = _HOME

for _fn in ("textdomain", "bindtextdomain", "bind_textdomain_codeset"):
    setattr(locale, _fn, lambda *args, **kwargs: None)


class _GLibStub:
    def __getattr__(self, attr):
        if attr[0].isupper():
            return _GLibStub()
        return lambda *args, **kwargs: _HOME


_gi = types.ModuleType("gi")
_repository = types.ModuleType("gi.repository")
_repository.GLib = _GLibStub()
_gi.repository = _repository
_gi.require_version = lambda *args, **kwargs: None
sys.modules.setdefault("gi", _gi)
sys.modules.setdefault("gi.repository", _repository)

sys.path.append(GRAMPS_SITE)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
