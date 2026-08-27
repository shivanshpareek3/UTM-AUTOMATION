import pytest
import os

def test_acceptance_criteria():
    app_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'streamlit_app.py')
    with open(app_path, "r") as f:
        content = f.read()
        
    assert "suggest_mapping" not in content, "Auto mapping must be completely disabled."
    assert "aliases.json" not in content, "Must not use aliases for UI."
    
    # Check that we use buttons for manual mapping.
    assert "container.button(c" in content or "container.button" in content, "Must use buttons for manual mapping."
    assert "st.selectbox(f\"Select column" not in content, "Must not use dropdowns for column mapping."

    print("Acceptance checks passed: No auto-mapping, no dropdowns in mapping, buttons present.")
