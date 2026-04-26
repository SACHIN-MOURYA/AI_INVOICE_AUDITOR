import subprocess
import sys
import time
import atexit
from pathlib import Path

# Global list to track all processes
processes = []

def cleanup_processes():
    """Clean up all running processes on exit."""
    print("\n" + "=" * 60)
    print("🛑 Shutting down all services...")
    print("=" * 60)
    for name, process in processes:
        if process.poll() is None:  # Process still running
            print(f"  Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    print("✅ All services stopped")

# Register cleanup function
atexit.register(cleanup_processes)

if __name__ == "__main__":
    base_dir = Path(__file__).parent
    mock_erp_path = base_dir / "mock_erp" / "app.py"
    dashboard_path = base_dir / "ui" / "streamlit_app.py"
    extraction_agent_path = base_dir / "a_2_a" / "extractor_agent_a2a_server.py"
    validation_agent_path = base_dir / "a_2_a" / "validation_agent_a2a_server.py"
    reporting_agent_path = base_dir / "a_2_a" / "reporting_agent_a2a_server.py"
    translation_agent_path = base_dir / "a_2_a" / "translation_agent_a2a_server.py"

    print("=" * 60)
    print("🚀 Starting AI Invoice Auditor Environment")
    print("=" * 60)

    try:
        # 1️⃣ Start Mock ERP API
        print("\n📡 Launching Mock ERP API (http://localhost:8001)...")
        erp_process = subprocess.Popen(
            [sys.executable, str(mock_erp_path)],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        processes.append(("Mock ERP API", erp_process))
        time.sleep(3)  # Give ERP more time to start
        
        # Verify ERP is running
        if erp_process.poll() is not None:
            print("❌ Mock ERP failed to start!")
            sys.exit(1)

        # 2️⃣ Start Extractor Agent A2A Server
        print("🔧 Launching Extractor Agent A2A Server (http://localhost:9999)...")
        extractor_process = subprocess.Popen(
            [sys.executable, str(extraction_agent_path)],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        processes.append(("Extractor Agent", extractor_process))
        time.sleep(3)

        # 3️⃣ Start Translation Agent A2A Server
        print("🌐 Launching Translation Agent A2A Server (http://localhost:9998)...")
        translation_process = subprocess.Popen(
            [sys.executable, str(translation_agent_path)],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        processes.append(("Translation Agent", translation_process))
        time.sleep(3)

        # 4️⃣ Start Validation Agent A2A Server
        print("✅ Launching Validation Agent A2A Server (http://localhost:9997)...")
        validation_process = subprocess.Popen(
            [sys.executable, str(validation_agent_path)],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        processes.append(("Validation Agent", validation_process))
        time.sleep(3)

        # 5️⃣ Start Reporting Agent A2A Server
        print("📊 Launching Reporting Agent A2A Server (http://localhost:9996)...")
        reporting_process = subprocess.Popen(
            [sys.executable, str(reporting_agent_path)],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        processes.append(("Reporting Agent", reporting_process))
        time.sleep(3)

        print("\n" + "=" * 60)
        print("✅ All backend services started successfully!")
        print("=" * 60)
        print("\n📋 Service Status:")
        print("  ├─ Mock ERP API:        http://localhost:8001")
        print("  ├─ Extractor Agent:     http://localhost:9999")
        print("  ├─ Translation Agent:   http://localhost:9998")
        print("  ├─ Validation Agent:    http://localhost:9997")
        print("  └─ Reporting Agent:     http://localhost:9996")
        print("\n" + "=" * 60)

        # 6️⃣ Start Streamlit Dashboard (blocking)
        print("\n🧠 Launching Streamlit Dashboard (http://localhost:8501)...")
        print("=" * 60)
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(dashboard_path),
            "--server.port=8501",
            "--server.headless=false"
        ])

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup will be handled by atexit
        pass
