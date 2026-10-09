#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2026 Jiri Slovacek
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

register(
    GENERAL,
    id="MaidenNameDisplay",
    name=_("Maiden Name Display"),
    description=_(
        "Shows a married woman as 'Given Married (Maiden)' everywhere, "
        "computed from her Married Name and Birth Name"
    ),
    version="0.1.1",
    gramps_target_version="6.0",
    status=STABLE,
    fname="maidennamedisplay.py",
    authors=["Jiri Slovacek"],
    authors_email=[""],
    load_on_reg=True,
    category="MISC",
)
