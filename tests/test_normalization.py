import pytest
import pandas as pd
from src.normalization import clean_text, normalize_email, normalize_phone, unify_campaign_name

def test_clean_text():
    assert clean_text("  hello   world  ") == "hello world"
    assert clean_text("mojibake ‚Äì fix") == "mojibake – fix"
    assert clean_text(float('nan')) == ""

def test_normalize_email():
    assert normalize_email(" Test@Email.com ") == "test@email.com"

def test_normalize_phone():
    assert normalize_phone("+91 98765-43210") == "9876543210"
    assert normalize_phone("(123) 456 7890") == "1234567890"
    assert normalize_phone("919876543210") == "9876543210"

def test_unify_campaign_name():
    assert unify_campaign_name("Webinar Campaign") == "webinar campaign"
    assert unify_campaign_name("webinar  campaign") == "webinar campaign"
