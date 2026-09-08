// Playwright config for public/ smoke + MVP field acceptance (#62).
// @playwright/test@1.56.1 expects chromium / chromium_headless_shell build 1194.
// If the headless_shell package for that rev is missing (partial local cache), fall
// back to the full Chromium 1194 binary under PLAYWRIGHT_BROWSERS_PATH.
import { defineConfig } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const BROWSERS = process.env.PLAYWRIGHT_BROWSERS_PATH || "/opt/pw-browsers";
const REV = "1194"; // keep in lockstep with package.json pin 1.56.1

function exists(p) {
  try { return fs.existsSync(p); } catch { return false; }
}

function fullChromium1194() {
  const mac = path.join(BROWSERS, `chromium-${REV}`, "chrome-mac", "Chromium.app", "Contents", "MacOS", "Chromium");
  const linux = path.join(BROWSERS, `chromium-${REV}`, "chrome-linux", "chrome");
  if (exists(mac)) return mac;
  if (exists(linux)) return linux;
  return undefined;
}

function headlessShell1194() {
  const mac = path.join(BROWSERS, `chromium_headless_shell-${REV}`, "chrome-mac", "headless_shell");
  const linux = path.join(BROWSERS, `chromium_headless_shell-${REV}`, "chrome-linux", "headless_shell");
  if (exists(mac)) return mac;
  if (exists(linux)) return linux;
  return undefined;
}

const launchOptions = {};
if (!headlessShell1194()) {
  const exe = fullChromium1194();
  if (exe) launchOptions.executablePath = exe;
}

export default defineConfig({
  testDir: ".",
  timeout: 60_000,
  use: Object.keys(launchOptions).length ? { launchOptions } : {},
});
