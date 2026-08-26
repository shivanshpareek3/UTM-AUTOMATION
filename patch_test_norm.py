with open('tests/test_normalization.py', 'r') as f:
    content = f.read()

import re
content = re.sub(
    r'def test_unify_campaign_name\(\):.*?(?=\n\n|\Z)',
    'def test_unify_campaign_name():\n    assert unify_campaign_name("Webinar Campaign") == "webinarcampaign"\n    assert unify_campaign_name("WEBINAR CAMPAIGN") == "webinarcampaign"\n    assert unify_campaign_name("ForemostLeads-GS-13-09-V1 <foo>") == "foremostleadsgs1309v1foo"\n    assert unify_campaign_name("foremostleads-gs-13-09") == "foremostleadsgs1309"\n    assert unify_campaign_name(None) == ""',
    content,
    flags=re.DOTALL
)

with open('tests/test_normalization.py', 'w') as f:
    f.write(content)
