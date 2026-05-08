import os
import time


def main():
    interval = int(os.getenv("COLLECTOR_INTERVAL_SECONDS", "60"))
    print("collector service placeholder started", flush=True)

    while True:
        print("collector heartbeat: no external systems are connected in M1", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    main()
