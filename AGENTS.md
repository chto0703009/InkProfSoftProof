# InkProf Soft Proof working preferences

Keep GPL-3.0-or-later declarations and the author/contact details:
Christer Törnkvist <christer@borgasundsfotografiska.se>.
Preserve upstream license notices and the full unmodified GPL text.

User photographs, measurement originals and ICC originals must never be
silently overwritten, deleted or included in releases. Build outputs,
virtual environments and user datasets stay outside Git.

When documentation PDFs are generated or changed, preserve the repository
copy under output/pdf/ and copy each resulting PDF to ~/Downloads/ using the
same filename. Verify the copies match. Render and inspect pages before
delivery. Keep headings with their following content; no orphan headings.

The standalone installer is built with tools/build_softproof_dmg.py from
Python source. Verify the app independently of the source checkout, include
application source and notices, and accurately state target architecture
and notarization status. Keep original-file overwrite protection intact.
