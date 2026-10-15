# Optional Fire OS update

[Deutsch](UPDATE_DE.md) · [Main instructions](README.md)

Start the normal main menu: `bash 00_setup.sh` on Linux or `00_setup.bat` on Windows.

| Selection | Result |
|---|---|
| `ALL` | Phases 1–5, without a firmware update |
| `ALL U` | Phase 1, combined phase 2 + update, then phases 3–5 |
| `2 U` | Permanent root and update in one TWRP session |
| `U` | Update an existing installation; unlock and backup if not already verified |
| `U 3 4` | Update, then Google/microG and Emotn |

U targets **8.1.8.2 / RS8182.3811N / 0032548774788** on verified karat devices. Exact model, firmware and kernel gates remain active. It does not downgrade newer firmware or reflash already installed 8.1.8.2. A completed update transaction is not repeated.

## Sequence

1. Download the firmware with progress; verify pinned SHA-256 and ZIP integrity. Reuse matching local files.
2. Verify device identity and ask for `UPDATE`; a new unlock also requires `UNLOCK`. Use the Amonet karat TWRP **3.7.1_12-0** installed by this setup. An unrelated recovery sharing that version label is not proof of the same partition protections.
3. Reuse the verified PC backup or create it once. Never overwrite backups. After verifying PC copies, remove only the setup-owned device backup folders to free space.
4. Before leaving Android, disable Google's verifier if Play Store is present; require exactly Amazon's receiver. In TWRP, save the enabled states of Vector and microG promotion and disable both. Previously disabled modules stay disabled. Pending module installations block the update.
5. In **one TWRP session**, flash firmware, perform the three known adbd byte checks, flash Post-OTA, then Magisk. No intermediate Android boot. Failed checks prevent subsequent flashes.
6. Boot and verify the exact target firmware/kernel and Magisk 30.7. Restore Wi-Fi only after verifying OTA blocking. Install and hash-check the full local Magisk app.
7. On the TV, run **Magisk → Install → Direct Install (Recommended)**, then enter `RESUME` in the terminal. The script reboots and checks writable Magisk preinit storage. If missing, it asks for Direct Install again and verifies after another scripted reboot. Vector cannot be restored before this succeeds.
8. Restore previously enabled Vector by reinstalling the pinned module; check both preinit rules `xposed_file` and `xposed_data`, then reboot. For previously enabled microG promotion: disable/check Google's verifier, enable promotion, reboot, check again. These verification boots are intentional.
9. Verify restored module flags, preinit and verifier state. Remove setup-owned temporary firmware, Magisk, Post-OTA and restored Vector ZIP files. Preserve PC backups. Subsequent selected phases use the updated firmware identity.

Preinit checks also apply to normal phases 2 and 3. Reboots initiated from fully booted Android check the verifier whenever Play Store is installed. Package Manager cannot be queried from TWRP; the pre-update verification and disabled promotion cover that transition.

## Resume and boot problems

Restart the **same main menu in the same folder**. Saved plans and per-device checkpoints select remaining work. A confirmed successful firmware flash is not repeated after a later failure. The old backup's source firmware identity is retained separately from the running firmware.

If a flash began but success was not confirmed, automatic replay stays blocked. Preserve runtime, PC backups and the recovery log. Do not delete checkpoints or mark writes complete by hand. A manually performed firmware change outside this transaction is intentionally not adopted by rewriting old checkpoints.

A boot timeout prints diagnostic guidance. `There must be exactly one verifier` supports the repair in `MANUAL-REPAIR.md`. Invalid `xposed_file` labels or denied `dex2oat` execution require checking Magisk preinit and Vector rules. A verifier repair alone cannot fix missing SELinux rules. Keep Vector disabled until those checks pass.

## Firmware and preview

An existing `.bin` can be renamed to `FireOS-8.1.8.2.zip` and placed in `packages/root/`; do not extract it.

- Original: `update-kindle-karat-RS8182_user_3811_0032548774788.bin`
- Size: **748897613 bytes**
- SHA-256: `559cddbc9e57fa786b396aa4939b54fcb8ff85c789f0ef55df9b0ed4138c7578`
- Published MD5: `fcaf730cf8bfee8bc50788e24ed65d2d`
- Amazon HTTPS URL included in `config/sources.local.json`; firmware is not bundled.

```bash
bash 00_setup.sh --lang en --preview-only --steps "ALL U"
```

Use `--dry-run` to really download/check files while simulating device operations. Windows accepts the same options through `00_setup.bat`.

## Validation limits

The firmware download was checked against the published MD5, ZIP CRC and exact OTA metadata; its SHA-256 is pinned. Offline tests cover ordering, failure gates, checkpoint resume, identity migration, module state preservation and preinit/verifier checks. English/German previews and Bash syntax are checked, including the extracted release ZIP. The underlying manual sequence succeeded on a user's 4K Plus. This new automation has not been hardware-tested on every model or executed on a Windows device. No test guarantees protection against every boot failure, power loss or hardware fault.
