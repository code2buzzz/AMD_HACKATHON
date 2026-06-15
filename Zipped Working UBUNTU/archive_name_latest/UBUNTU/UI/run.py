# run.py
import subprocess
import sys
import time


def start_pipeline():
    print("🚀 Starting BankDB System Services...")

    # 1. Spin up FastAPI Backend
    print("⚡ Launching FastAPI Backend on http://127.0.0.1:8000")
    backend = subprocess.Popen([sys.executable, "main.py"])

    # Give the backend 2 seconds to bind to the port before launching frontend
    time.sleep(2)

    # 2. Spin up Streamlit Frontend
    print("🎨 Launching Streamlit UI...")
    frontend = subprocess.Popen(["streamlit", "run", "app.py"])

    try:
        # Keep orchestrator alive while both processes run
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down system services safely...")
        backend.terminate()
        frontend.terminate()
        print("👋 All processes terminated.")


if __name__ == "__main__":
    start_pipeline()
