- https://stackoverflow.com/questions/43923996/adb-root-is-not-working-on-emulator-cannot-run-as-root-in-production-builds/45668555#45668555
- https://forum.videohelp.com/threads/408031-Dumping-Your-own-L3-CDM-with-Android-Studio

Frida is a dynamic instrumentation toolkit for developers, reverse-engineers, and security researchers.

- https://github.com/frida/frida/issues/1932
- https://github.com/frida/frida/releases

Dumper doesn't work on newer android versions and couldn't get it
to work on android 9 Pie as OP explained.

- https://github.com/wvdumper/dumper

KeyDive worked to dump on Android 12 API 31.
Force frida pip module to install 16.11.4-11.
Make sure to check other pip modules versions.

!!! ALWAYS MAKE SURE TO USE THE SAME FRIDA SERVER VERSION AS THE FRIDA PYTHON MODULE. !!!

- https://github.com/hyugogirubato/KeyDive

Create a wvd file from the dump.

- https://forum.videohelp.com/threads/407466-how-get-wvd
