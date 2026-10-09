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
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
"""
Show a married woman's maiden surname next to her married surname.

A woman whose preferred name is a "Married Name" and who also has an
alternate "Birth Name" with a different surname is displayed as
"Given Married (Maiden)" in every name format, for example
"Ladislava Slováčková (Malotová)" or "Slováčková (Malotová), Ladislava".

Nothing is written to the database: the display is computed from the
stored Married Name and Birth Name, so correcting either one updates the
display everywhere.

When the maiden surname is already part of the married name (a woman who
kept both surnames, entered as one name with two surnames), no brackets
are added: "Ladislava Slováčková Malotová".
"""

import logging

from gramps.gen.display.name import _F_FN, NameDisplay
from gramps.gen.lib import Name, NameType, Person

LOG = logging.getLogger(".MaidenNameDisplay")

SURNAME_FORMAT = "{married} ({maiden})"
_PATCHED_FLAG = "_maiden_name_display_patched"


# ------------------------------------------------------------------------
#
# Pure logic
#
# ------------------------------------------------------------------------
def _surname_texts(name):
    return {surname.get_surname().strip() for surname in name.get_surname_list()}


def maiden_surname(person):
    """
    Return the maiden surname to show for the person, or "" if none.

    Rules: female, preferred name of type Married Name, first alternate
    name of type Birth Name has a primary surname that is not already
    part of the preferred name.
    """
    if person is None or person.get_gender() != Person.FEMALE:
        return ""
    primary = person.get_primary_name()
    if primary.get_type() != NameType.MARRIED:
        return ""
    for alternate in person.get_alternate_names():
        if alternate.get_type() != NameType.BIRTH:
            continue
        surname = alternate.get_primary_surname()
        maiden = surname.get_surname().strip() if surname else ""
        if maiden and maiden not in _surname_texts(primary):
            return maiden
        return ""
    return ""


def name_with_maiden(name, maiden):
    """Return a copy of name whose primary surname reads "Married (Maiden)"."""
    shown = Name(source=name)
    surnames = shown.get_surname_list()
    if not surnames:
        return shown
    primary = next((s for s in surnames if s.get_primary()), surnames[0])
    married = primary.get_surname().strip()
    primary.set_surname(
        SURNAME_FORMAT.format(married=married, maiden=maiden) if married else maiden
    )
    return shown


def displayed_name(person):
    """Primary name of the person, extended with the maiden surname if any."""
    maiden = maiden_surname(person)
    primary = person.get_primary_name()
    return name_with_maiden(primary, maiden) if maiden else primary


# ------------------------------------------------------------------------
#
# Patches
#
# ------------------------------------------------------------------------
def _patch_name_displayer():
    original_sorted = NameDisplay.sorted

    def display(self, person):
        return self.display_name(displayed_name(person))

    def display_formal(self, person):
        return self.display_name(displayed_name(person))

    def display_format(self, person, num):
        return self.name_formats[num][_F_FN](displayed_name(person))

    def sorted_(self, person):
        if not maiden_surname(person):
            return original_sorted(self, person)
        return self.sorted_name(displayed_name(person))

    NameDisplay.display = display
    NameDisplay.display_formal = display_formal
    NameDisplay.display_format = display_format
    NameDisplay.sorted = sorted_


def _is_candidate(data):
    """Cheap check on raw person data before loading the full person."""
    try:
        return (
            data.gender == Person.FEMALE
            and data.primary_name.type.value == NameType.MARRIED
            and len(data.alternate_names) > 0
        )
    except (AttributeError, KeyError, TypeError):
        return False


def _patch_people_view():
    """The person list builds names from raw data; route women through display()."""
    try:
        from gramps.gen.display.name import displayer
        from gramps.gui.views.treemodels import peoplemodel
    except ImportError:
        return  # command line, no GUI
    model = peoplemodel.PeopleBaseModel
    original_column_name = model.column_name

    def column_name(self, data):
        if not _is_candidate(data):
            return original_column_name(self, data)
        cached, name = self.get_cached_value(data.handle, "NAME")
        if cached:
            return name
        person = self.db.get_person_from_handle(data.handle)
        name = displayer.display(person)
        self.set_cached_value(data.handle, "NAME", name)
        return name

    model.column_name = column_name


def load_on_reg(dbstate, uistate, plugin):
    """Called by Gramps when the plugin is registered at startup."""
    if getattr(NameDisplay, _PATCHED_FLAG, False):
        return []
    try:
        _patch_name_displayer()
        _patch_people_view()
        setattr(NameDisplay, _PATCHED_FLAG, True)
    except Exception:  # never break Gramps startup because of a display tweak
        LOG.exception("MaidenNameDisplay: patching failed, names shown unchanged")
    return []
