from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import normalize_game_contract  # noqa: E402


RAW_CONTRACT = """To create the rock-paper-scissors CLI contract for this repo, I'll follow the skill.

Here is the contract:

```text
APP: play.py
DOCS: GAME_README.md
GAME: rock-paper-scissors
MARKER: RPS_SELF_TEST=pass

MODE: human-vs-computer
MODE: human-vs-human

VERIFY: python3 -m py_compile play.py
VERIFY: timeout 10s python3 play.py --self-test
VERIFY: printf '1\\nrock\\nq\\n' | timeout 10s python3 play.py
VERIFY: printf '1\\nlizard\\nq\\n' | timeout 10s python3 play.py
VERIFY: printf '2\\nrock\\nscissors\\nq\\n' | timeout 10s python3 play.py

The app should:
- accept rock, paper, scissors, and q
```

Please create GAME_CONTRACT.md with the above content.
"""


class GameContractTests(unittest.TestCase):
    def test_extracts_contract_from_fenced_model_output(self):
        contract = normalize_game_contract.extract_contract(RAW_CONTRACT)

        self.assertIn("APP: play.py", contract)
        self.assertIn("VERIFY: printf '1\\nrock\\nq\\n' | timeout 10s python3 play.py", contract)
        self.assertNotIn("```", contract)
        self.assertNotIn("Please create", contract)
        self.assertEqual(normalize_game_contract.validate_contract(contract), [])

    def test_cli_writes_clean_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.txt"
            out = Path(tmp) / "GAME_CONTRACT.md"
            raw.write_text(RAW_CONTRACT, encoding="utf-8")

            rc = normalize_game_contract.main([str(raw), str(out)])

            self.assertEqual(rc, 0)
            text = out.read_text(encoding="utf-8")
            self.assertIn("MODE: human-vs-human", text)
            self.assertNotIn("Here is the contract", text)

    def test_rejects_missing_play_smoke(self):
        contract = "APP: play.py\nDOCS: GAME_README.md\nGAME: rock-paper-scissors\n"

        problems = normalize_game_contract.validate_contract(contract)

        self.assertIn("VERIFY: printf '1\\nrock\\nq\\n' | timeout 10s python3 play.py", problems)


if __name__ == "__main__":
    unittest.main()
