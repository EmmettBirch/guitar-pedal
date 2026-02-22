# test_idle_screen.py - Tests for the idle screen date display
# Verifies that the idle screen uses the dynamic date from datetime.

import sys
import os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pi'))


class TestIdleScreenDate:
    def test_date_import_exists(self):
        """The idle_screen module should import date from datetime."""
        import ui.idle_screen as mod
        source = open(mod.__file__).read()
        assert "from datetime import date" in source

    def test_uses_dynamic_date(self):
        """The idle screen should use date.today() not a hardcoded string."""
        import ui.idle_screen as mod
        source = open(mod.__file__).read()
        assert "date.today().isoformat()" in source
        # Should NOT contain a hardcoded date
        assert "'2026-" not in source
