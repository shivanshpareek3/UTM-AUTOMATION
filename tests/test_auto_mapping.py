import pytest
from src.inspection import suggest_mapping, load_aliases

@pytest.fixture
def aliases():
    return load_aliases()

def test_a_exact_column_names(aliases):
    # A. Exact column names auto-map correctly
    assert suggest_mapping('email', ['email', 'other'], aliases) == 'email'
    assert suggest_mapping('campaign', ['something', 'campaign'], aliases) == 'campaign'

def test_b_common_aliases(aliases):
    # B. Common aliases auto-map correctly
    assert suggest_mapping('email', ['Customer Email', 'foo'], aliases) == 'Customer Email'
    assert suggest_mapping('campaign', ['Campaign Name', 'foo'], aliases) == 'Campaign Name'
    assert suggest_mapping('registration_date', ['Created At', 'foo'], aliases) == 'Created At'

def test_c_ad_set_aliases(aliases):
    # C. Ad Set aliases auto-map correctly
    ad_set_variants = ['Ad Set', 'Ad Set Name', 'Adset', 'Adset Name']
    for variant in ad_set_variants:
        assert suggest_mapping('ad_set', [variant, 'other'], aliases) == variant

def test_d_creative_ad_aliases(aliases):
    # D. Creative/Ad aliases auto-map correctly
    creative_variants = ['Creative', 'Creative Name', 'Ad', 'Ad Name', 'Ad Creative', 'Ad Creative Name']
    for variant in creative_variants:
        assert suggest_mapping('ad_creative', [variant, 'other'], aliases) == variant

def test_e_unknown_columns(aliases):
    # E. Unknown columns are NOT auto-mapped
    assert suggest_mapping('email', ['customer_identifier_xyz', 'foo'], aliases) == '-- Ignore/Missing --'
    assert suggest_mapping('campaign', ['random_string_123'], aliases) == '-- Ignore/Missing --'

def test_h_wrong_fuzzy_match_rejected(aliases):
    # H. A wrong fuzzy match such as Customer Name -> email is rejected
    assert suggest_mapping('email', ['Customer Name'], aliases) == '-- Ignore/Missing --'
    assert suggest_mapping('campaign', ['Customer Name'], aliases) == '-- Ignore/Missing --'
    assert suggest_mapping('ad_set', ['Customer Name'], aliases) == '-- Ignore/Missing --'

def test_f_manual_dropdown_still_works():
    # F. Manual dropdown mapping still works
    # This is a UI-level test, but we can verify the function returns '-- Ignore/Missing --' 
    # when forced to manual fallback, allowing the UI to present the dropdown.
    aliases = load_aliases()
    assert suggest_mapping('email', ['some_weird_column'], aliases) == '-- Ignore/Missing --'

def test_g_different_files_no_leak():
    # G. Different uploaded files cannot leak mappings/state
    # suggest_mapping is purely functional and stateless.
    aliases = load_aliases()
    res1 = suggest_mapping('email', ['Customer Email'], aliases)
    res2 = suggest_mapping('email', ['Email Address'], aliases)
    assert res1 == 'Customer Email'
    assert res2 == 'Email Address'

