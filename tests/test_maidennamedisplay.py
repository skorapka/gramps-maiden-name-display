"""Unit tests for MaidenNameDisplay.

Run against the Gramps installed in the macOS app bundle:
    python3.13 -m pytest tests/  (see conftest.py for the GLib/locale stubs)
"""

import pytest

from gramps.gen.display.name import NameDisplay
from gramps.gen.lib import Name, NameType, Person, Surname

import maidennamedisplay as mnd

FMT_GIVEN_SURNAME = "Given Surname"
FMT_SURNAME_GIVEN = "Surname, Given"


def make_name(given, surnames, name_type):
    name = Name()
    name.set_first_name(given)
    name.set_type(NameType(name_type))
    surname_list = []
    for index, text in enumerate(surnames):
        surname = Surname()
        surname.set_surname(text)
        surname.set_primary(index == 0)
        surname_list.append(surname)
    name.set_surname_list(surname_list)
    return name


def make_person(gender, primary, *alternates):
    person = Person()
    person.set_gender(gender)
    person.set_primary_name(primary)
    for alternate in alternates:
        person.add_alternate_name(alternate)
    return person


def ladislava(married=("Slováčková",), maiden="Malotová"):
    return make_person(
        Person.FEMALE,
        make_name("Ladislava", married, NameType.MARRIED),
        make_name("Ladislava", [maiden], NameType.BIRTH),
    )


@pytest.fixture(scope="module")
def displayer():
    mnd.load_on_reg(None, None, None)
    nd = NameDisplay()
    nd.set_default_format(nd.add_name_format("test", FMT_GIVEN_SURNAME))
    return nd


def test_married_woman_shows_maiden_in_brackets(displayer):
    assert displayer.display(ladislava()) == "Ladislava Slováčková (Malotová)"


def test_bracket_follows_surname_in_other_formats(displayer):
    num = displayer.add_name_format("surname first", FMT_SURNAME_GIVEN)
    assert displayer.display_format(ladislava(), num) == "Slováčková (Malotová), Ladislava"


def test_woman_keeping_both_surnames_has_no_brackets(displayer):
    person = ladislava(married=("Slováčková", "Malotová"))
    assert displayer.display(person) == "Ladislava Slováčková Malotová"


def test_same_surname_has_no_brackets(displayer):
    person = ladislava(maiden="Slováčková")
    assert displayer.display(person) == "Ladislava Slováčková"


def test_unmarried_woman_unchanged(displayer):
    person = make_person(Person.FEMALE, make_name("Marie", ["Nováková"], NameType.BIRTH))
    assert displayer.display(person) == "Marie Nováková"


def test_men_are_never_changed(displayer):
    person = make_person(
        Person.MALE,
        make_name("Jiri", ["Slovacek"], NameType.MARRIED),
        make_name("Jiří", ["Slováček"], NameType.BIRTH),
    )
    assert displayer.display(person) == "Jiri Slovacek"


def test_married_woman_without_birth_name_unchanged(displayer):
    person = make_person(Person.FEMALE, make_name("Jana", ["Dvořáková"], NameType.MARRIED))
    assert displayer.display(person) == "Jana Dvořáková"


def test_stored_name_is_not_modified(displayer):
    person = ladislava()
    displayer.display(person)
    assert person.get_primary_name().get_surname() == "Slováčková"


def test_sorted_includes_maiden(displayer):
    assert "(Malotová)" in displayer.sorted(ladislava())


def test_patch_is_applied_once():
    first = NameDisplay.display
    mnd.load_on_reg(None, None, None)
    assert NameDisplay.display is first
