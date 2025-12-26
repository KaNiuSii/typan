import os
import sys
import subprocess

def main() -> None:
    from typan_lab.app import TypanLabApp
    TypanLabApp().run()

if __name__ == "__main__":
    if os.environ.get("TYPAN_NO_SPAWN") == "1":
        main()
        raise SystemExit

    if os.environ.get("TYPAN_NEW_CMD") != "1":
        env = os.environ.copy()
        env["TYPAN_NEW_CMD"] = "1"

        subprocess.Popen(
            [
                "cmd", "/c", "start", "/max", "cmd", "/k",
                "mode con cols=200 lines=60 &&",
                sys.executable, __file__,
            ],
            env=env,
        )
        raise SystemExit

    main()
