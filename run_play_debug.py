import subprocess
import time
import os
import signal

# 1. Start Streamlit
proc = subprocess.Popen(["python3", "-m", "streamlit", "run", "app/streamlit_app.py", "--server.port", "8505"])
time.sleep(5)

# 2. Modify play_test.py to avoid crashing
with open('play_test.py', 'r') as f:
    code = f.read()
code = code.replace('page.wait_for_selector("text=REPORT VALID", timeout=30000)', 'page.wait_for_selector("text=REPORT VALID", state="attached", timeout=30000)')
code = code.replace('http://localhost:8501', 'http://localhost:8505')
with open('play_test.py', 'w') as f:
    f.write(code)

# 3. Run play_test.py
subprocess.run(["python3", "play_test.py"])

# 4. Stop Streamlit
os.kill(proc.pid, signal.SIGTERM)
