import os
import sys

# Ensure project root is on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookscart.settings")

try:
    import django
    django.setup()
    from django.template.loader import get_template
    templates = ["orders/history.html", "books/home.html", "books/list.html"]
    for t in templates:
        try:
            tpl = get_template(t)
            print(f"OK: found template {t} -> {tpl}")
        except Exception as e:
            print(f"ERROR: cannot load template {t}: {e}")
except Exception as e:
    print("Failed to initialize Django:", e)
