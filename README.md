# webfix-solo

> **Repo C** of the [evidence-capture three-repo split](https://github.com/appevidence/evidence-capture-app#related-projects-sibling-repositories).
> Minimalist single-binary CLI / desktop utility for **one user on one machine**. No web server, no multi-user, no Docker stack.
> Forked from [`appevidence/evidence-capture-app`](https://github.com/appevidence/evidence-capture-app) (Repo A) with the web layer stripped out.

## What it is

A personal, hash-chained log of web-page captures with **zero deployment complexity**. Run it on your laptop, point it at a URL, get a signed evidence bundle.

Each capture produces a bundle containing:

- HTML, screenshot, PDF, and HAR of the target page (via Playwright)
- SHA-256 of every artifact
- An Ed25519-signed manifest
- Optional: RFC 3161 timestamp, OpenTimestamps proof, Wayback Machine submission, PDF report
- An entry in a tamper-evident, hash-chained local audit log

## What it is **not** — обязательный дисклеймер / mandatory disclaimer

**RU.** Это технический инструмент фиксации. Он **не** заменяет нотариальный протокол осмотра доказательств, **не** является квалифицированной электронной подписью по 63-ФЗ, **не** сертифицирован ФСБ России или Минцифры России и **не** является автоматически принимаемым судом доказательством. Юридическая сила полученных бандлов определяется судом или иным правоприменителем по правилам конкретной юрисдикции и процессуального законодательства.

**EN.** This is a technical capture tool. It is **not** a substitute for a notarial inspection record, it is **not** a qualified electronic signature under any national e-signature law, it is **not** certified by any state cryptographic authority, and it is **not** automatically admissible as evidence in any court. The legal weight of the produced bundles is determined by the trier of fact under the rules of the relevant jurisdiction and procedural law.

## Install

> ⚠️ **Pre-alpha.** The CLI surface is wired up but the capture / signing / verify modules are still being ported from Repo A. See [`docs/Current-State.md`](docs/Current-State.md) for the port checklist.

> 📖 **Подробное руководство (RU)** по установке, развёртыванию, настройке и запуску для технического персонала и для пользователя-юриста, в GitHub Codespaces и на Ubuntu 24.04 локально — см. [`docs/УСТАНОВКА.md`](docs/УСТАНОВКА.md).
> The repo also ships a [`.devcontainer/`](.devcontainer/devcontainer.json) so GitHub Codespaces is a one-click setup.

```bash
pip install webfix-solo
playwright install chromium
```

Optional extras:

```bash
pip install "webfix-solo[ots]"      # OpenTimestamps proofs
pip install "webfix-solo[wayback]"  # Wayback Machine submission
pip install "webfix-solo[eth]"      # Ethereum anchoring (advanced; needs a key and gas)
```

## Usage

```bash
webfix init                          # generate Ed25519 keypair, init local SQLite + audit log
webfix capture https://example.com   # capture a URL; emits a signed .zip bundle
webfix verify ./bundle.zip           # verify signature, hashes, and timestamp
webfix audit list                    # list local audit-log entries
webfix audit verify-all              # verify the full hash chain
webfix export ./bundle.zip --to .    # extract bundle contents
webfix report ./bundle.zip --pdf out.pdf
```

Run `webfix <command> --help` for full options.

## Data layout

By default everything lives under `${XDG_DATA_HOME:-~/.local/share}/webfix-solo/`:

```
webfix-solo/
├── keys/        # Ed25519 keypair (private key encrypted with a passphrase)
├── db.sqlite    # local SQLAlchemy DB (created via Base.metadata.create_all)
├── audit.log    # hash-chained audit log
└── bundles/     # captured evidence bundles (.zip)
```

No data ever leaves your machine unless you explicitly enable `--with-wayback`, `--with-ots`, or `--with-eth`.

## Related projects (sibling repositories)

| Repo | Name | One-liner |
|---|---|---|
| A | [`evidence-capture-app`](https://github.com/appevidence/evidence-capture-app) | Reference web app + CLI; full feature surface. |
| B | `evidence-platform` *(planned)* | Multi-tenant SaaS / on-prem platform built on A. |
| **C** | **`webfix-solo`** *(this repo)* | **Minimalist single-user CLI; no web server.** |

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`SECURITY.md`](SECURITY.md).

## License

[MIT](LICENSE) — © 2026 appevidence.
Includes code derived from [`appevidence/evidence-capture-app`](https://github.com/appevidence/evidence-capture-app); see [`NOTICE.md`](NOTICE.md).
