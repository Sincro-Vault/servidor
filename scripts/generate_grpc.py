"""Compila proto/secrets.proto a stubs Python en src/grpc_server/generated/.

Ejecutar: python scripts/generate_grpc.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTO_DIR = ROOT / "proto"
OUT_DIR = ROOT / "src" / "grpc_server" / "generated"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    init_file = OUT_DIR / "__init__.py"
    if not init_file.exists():
        init_file.touch()

    proto_file = PROTO_DIR / "secrets.proto"
    if not proto_file.exists():
        print(f"ERROR: no existe {proto_file}", file=sys.stderr)
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"-I{PROTO_DIR}",
        f"--python_out={OUT_DIR}",
        f"--grpc_python_out={OUT_DIR}",
        str(proto_file),
    ]
    print("Ejecutando:", " ".join(cmd))
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print("ERROR al compilar .proto", file=sys.stderr)
        sys.exit(result.returncode)

    # Parchar el import en secrets_pb2_grpc.py para que sea relativo
    grpc_file = OUT_DIR / "secrets_pb2_grpc.py"
    if grpc_file.exists():
        text = grpc_file.read_text(encoding="utf-8")
        text = text.replace("import secrets_pb2 as", "from . import secrets_pb2 as")
        grpc_file.write_text(text, encoding="utf-8")

    print(f"Stubs generados en {OUT_DIR}")


if __name__ == "__main__":
    main()
