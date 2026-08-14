import pytest
import pandas as pd
import os
from src.ingestion import read_file

def test_read_csv(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "test.csv"
    p.write_text("a,b,c\n1,2,3")
    
    df = read_file(str(p))
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ['a', 'b', 'c']

def test_read_missing_file():
    with pytest.raises(FileNotFoundError):
        read_file("nonexistent.csv")

def test_unsupported_format(tmp_path):
    p = tmp_path / "test.txt"
    p.write_text("hello")
    with pytest.raises(ValueError):
        read_file(str(p))
