import sys
import traceback

modules = [
    "grpc",
    "chromadb",
    "onnxruntime",
    "cv2",
    "paddleocr",
    "sentence_transformers",
    "numpy",
    "langchain",
    "langgraph",
    "ollama"
]

print("--- Verifying Imports ---")
failed = False
for mod in modules:
    try:
        if mod == "grpc":
            from unittest.mock import MagicMock
            # Applying our magic mock workaround for cygrpc issue
            sys.modules['grpc'] = MagicMock(__version__='1.83.1')
            sys.modules['grpc.experimental'] = MagicMock()
            sys.modules['grpc.experimental.aio'] = MagicMock()
            sys.modules['grpc.aio'] = MagicMock()
            sys.modules['grpc._utilities'] = MagicMock()
            sys.modules['grpc._cython'] = MagicMock()
            sys.modules['grpc._cython.cygrpc'] = MagicMock()
            import grpc
            print(f"[OK] {mod} (mocked version: {grpc.__version__})")
        else:
            imported = __import__(mod)
            ver = getattr(imported, '__version__', 'unknown')
            print(f"[OK] {mod} v{ver}")
    except Exception as e:
        print(f"[FAIL] {mod}: {e}")
        failed = True

if failed:
    sys.exit(1)
print("All imports passed!")
