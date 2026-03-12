# Simple placeholder generator script

from config import SITE_NAME, OUTPUT_DIR

def build():
    print(f"Building static site for {SITE_NAME}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("Static build placeholder complete")

if __name__ == "__main__":
    build()
