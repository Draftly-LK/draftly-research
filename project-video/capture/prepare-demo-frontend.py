"""Copy the actual frontend for isolated local recording without secrets."""
from pathlib import Path
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT.parent.parent / "draftly-platform"
SOURCE = PLATFORM / "frontend"
TARGET = ROOT / "out" / "recording-app"
CONFIGS = ("package.json", "tsconfig.json", "next-env.d.ts", "next.config.ts", "tailwind.config.ts", "postcss.config.mjs", "components.json")

def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    files = []
    for directory in ("src", "public"):
        shutil.copytree(SOURCE / directory, TARGET / directory, dirs_exist_ok=True)
        files.extend(p for p in (SOURCE / directory).rglob("*") if p.is_file())
    for name in CONFIGS:
        shutil.copy2(SOURCE / name, TARGET / name)
        files.append(SOURCE / name)
    hashes = {str(p.relative_to(PLATFORM)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (ROOT / "out" / "platform-source-hashes.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    token = TARGET / "src" / "lib" / "api" / "use-token-provider.ts"
    text = token.read_text(encoding="utf-8")
    assert "const noToken: TokenProvider = async () => null;" in text
    token.write_text(text.replace("const noToken: TokenProvider = async () => null;",
                                  'const noToken: TokenProvider = async () => "film-local";'), encoding="utf-8")
    def change_values(value):
        if isinstance(value, dict):
            return {k: change_values(v) for k, v in value.items()}
        if isinstance(value, list):
            return [change_values(v) for v in value]
        if isinstance(value, str):
            return re.sub("synthetic", lambda m: "Demonstration" if m[0][0].isupper() else "demonstration", value, flags=re.I)
        return value
    for name in ("en.json", "si.json"):
        path = TARGET / "src" / "lib" / "i18n" / "messages" / name
        path.write_text(json.dumps(change_values(json.loads(path.read_text(encoding="utf-8"))), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (TARGET / ".env.local").write_text("AUTH_BYPASS=true\nNEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:4325\nNEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=\nCLERK_SECRET_KEY=\nNEXT_DIST_DIR=.next-demo\n", encoding="utf-8")
    peer = SOURCE / "node_modules" / ".pnpm" / "@tiptap+pm@2.27.2" / "node_modules" / "@tiptap" / "pm"
    if not (SOURCE / "node_modules" / "@tiptap" / "pm").exists() and peer.exists():
        config = TARGET / "next.config.ts"
        config.write_text(config.read_text(encoding="utf-8").replace("  reactStrictMode: true,",
            "  reactStrictMode: true,\n  // Local capture setup: resolve the existing installed Tiptap peer package.\n"
            "  webpack(config) {\n    config.resolve.alias = { ...config.resolve.alias, "
            f'"@tiptap/pm": "{peer.as_posix()}" }};\n    return config;\n  }},'), encoding="utf-8")
    print(f"Copied actual frontend ({len(files)} source/config files); platform source hashes recorded.")

if __name__ == "__main__":
    main()
