import json
from pathlib import Path

from oei_api.main import app


def main() -> None:
    destination = Path(__file__).resolve().parents[1] / "openapi.json"
    destination.write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
