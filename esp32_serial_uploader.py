#!/usr/bin/env python3
"""Upload text files to MicroPython board through friendly REPL over serial.
Works when raw-repl tools fail but normal REPL is accessible.
"""
import argparse
import serial
import time
from pathlib import Path


def read_until_idle(ser: serial.Serial, idle_s: float = 0.4, max_s: float = 3.0) -> str:
    buf = bytearray()
    start = time.time()
    last = time.time()
    while time.time() - start < max_s:
        chunk = ser.read(1024)
        if chunk:
            buf.extend(chunk)
            last = time.time()
        elif time.time() - last >= idle_s:
            break
    return buf.decode("utf-8", errors="ignore")


def send_cmd(ser: serial.Serial, cmd: str, settle: float = 0.08) -> str:
    ser.write(cmd.encode("utf-8") + b"\r\n")
    ser.flush()
    time.sleep(settle)
    return read_until_idle(ser)


def ensure_prompt(ser: serial.Serial) -> str:
    # Interrupt any running loop and sync prompt
    ser.write(b"\x03\x03\r\n")
    ser.flush()
    time.sleep(0.2)
    out = read_until_idle(ser, idle_s=0.5, max_s=4.0)
    return out


def upload_text_file(ser: serial.Serial, local_path: Path, remote_name: str) -> None:
    text = local_path.read_text(encoding="utf-8")
    print(f"[UPLOAD] {local_path.name} -> {remote_name} ({len(text)} chars)")

    out = send_cmd(ser, f"f=open('{remote_name}','w')")
    if "Traceback" in out:
        raise RuntimeError(f"Cannot open remote file {remote_name}:\n{out}")

    chunk_size = 240
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        out = send_cmd(ser, f"f.write({chunk!r})")
        if "Traceback" in out:
            raise RuntimeError(f"Write failed at chunk {i // chunk_size}:\n{out}")

    out = send_cmd(ser, "f.close()")
    if "Traceback" in out:
        raise RuntimeError(f"Close failed for {remote_name}:\n{out}")

    # quick stat check
    out = send_cmd(ser, f"import os; print('SIZE', os.stat('{remote_name}')[6])")
    print(out.strip().splitlines()[-1] if out.strip() else "SIZE ?")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM10")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--run", action="store_true", help="Run diagnostic after upload")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    files = [
        (root / "esp32_camera_config.py", "esp32_camera_config.py"),
        (root / "esp32_flash_diagnostic.py", "esp32_flash_diagnostic.py"),
    ]

    for path, _ in files:
        if not path.exists():
            raise FileNotFoundError(path)

    print(f"[INFO] Connecting to {args.port} @ {args.baud}")
    with serial.Serial(args.port, args.baud, timeout=0.15) as ser:
        prompt = ensure_prompt(ser)
        print("[INFO] REPL sync output:")
        print(prompt[-500:] if prompt else "(no text)")

        # sanity probe
        out = send_cmd(ser, "import sys; print('MICROPY', sys.implementation.name)")
        if "MICROPY" not in out:
            print("[WARN] MicroPython probe did not return expected token.")
            print(out[-500:])
        else:
            print("[OK] MicroPython probe succeeded")

        for local_path, remote_name in files:
            upload_text_file(ser, local_path, remote_name)

        # optional: set boot runner
        send_cmd(ser, "f=open('main.py','w')")
        send_cmd(ser, "f.write(\"import esp32_flash_diagnostic\\n\")")
        send_cmd(ser, "f.close()")
        print("[OK] main.py updated to launch esp32_flash_diagnostic")

        if args.run:
            print("[RUN] Launching diagnostic script now (Ctrl+C to stop)")
            ser.write(b"\x03\x03\r\n")
            ser.flush()
            time.sleep(0.1)
            ser.write(b"import esp32_flash_diagnostic\r\n")
            ser.flush()
            start = time.time()
            while time.time() - start < 25:
                chunk = ser.read(1024)
                if chunk:
                    print(chunk.decode("utf-8", errors="ignore"), end="")
            print("\n[INFO] Diagnostic capture window ended (25s)")

    print("[DONE] Upload complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
