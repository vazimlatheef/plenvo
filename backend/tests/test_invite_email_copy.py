from app.services.email import _usable_inviter_name, greeting_name, organisation_display_name


def test_deepmode_org_name_is_kept():
    class Org:
        name = "Deepmode"

    class Admin:
        company_name = None

    assert organisation_display_name(Org(), Admin()) == "Deepmode"


def test_company_name_preferred_over_org_label():
    class Org:
        name = "Deepmode"

    class Admin:
        company_name = "Plenvo"

    assert organisation_display_name(Org(), Admin()) == "Plenvo"


def test_mailbox_hi_is_not_used_as_inviter():
    assert _usable_inviter_name("Hi", "Deepmode") is None
    assert _usable_inviter_name("Hi User", "Deepmode") is None
    assert _usable_inviter_name("Alex Vale", "Deepmode") == "Alex Vale"


def test_greeting_skips_mailbox_hi():
    assert greeting_name("Hi") == "there"
    assert greeting_name("Alex Vale") == "Alex"
