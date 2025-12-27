import os
import shutil
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

        terminal_size = shutil.get_terminal_size()

        subprocess.Popen(
            [
                "cmd", "/c", "start", "/max", "cmd", "/k",
                f"mode con cols={terminal_size[0]} lines={terminal_size[1]} &&",
                sys.executable, __file__,
            ],
            env=env,
        )
        raise SystemExit

    main()
