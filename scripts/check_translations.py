import json, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(ROOT, "translations.js")
HTML = os.path.join(ROOT, "index.html")
APP = os.path.join(ROOT, "app.js")


def load_i18n():
    txt = open(JS, encoding="utf-8").read()
    m = re.match(r"^\s*window\.I18N\s*=\s*(.*);\s*$", txt, re.S)
    if not m:
        print("ERROR: cannot parse translations.js")
        sys.exit(1)
    return json.loads(m.group(1))


def main():
    data = load_i18n()
    if "en" not in data:
        print("ERROR: missing 'en' source language")
        sys.exit(1)
    en = data["en"]
    en_keys = set(en.keys())
    errors = []

    # 1. source language values must be non-empty
    for k, v in en.items():
        if not str(v).strip():
            errors.append("[en] empty value for key '%s'" % k)

    # 2. every other language must have all keys, non-empty, and not equal to the key
    for lang, d in data.items():
        if lang == "en":
            continue
        for k in en_keys:
            v = d.get(k)
            if v is None:
                errors.append("[%s] missing key '%s'" % (lang, k))
            elif not str(v).strip():
                errors.append("[%s] empty value for key '%s'" % (lang, k))
            elif str(v).strip() == k:
                errors.append("[%s] value equals key (untranslated) for '%s'" % (lang, k))

    # 3. every key used in the source must exist in the translation source
    html = open(HTML, encoding="utf-8").read()
    app = open(APP, encoding="utf-8").read()
    used = set(re.findall(r'data-i18n(?:-ph|-title|-summary)?="([a-z_]+)"', html))
    used |= set(re.findall(r't\("([a-z_]+)"\)', app)) - {"option", "div"}
    for k in used:
        if k not in en_keys:
            errors.append("key '%s' used in source but missing from translations.js" % k)

    if errors:
        print("TRANSLATION CHECK FAILED:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("Translation check OK: %d languages, %d keys each." % (len(data), len(en_keys)))


if __name__ == "__main__":
    main()
