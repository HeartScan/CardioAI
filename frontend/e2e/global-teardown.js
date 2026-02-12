import fs from "node:fs";
import path from "node:path";

const PID_FILE = path.resolve(process.cwd(), ".playwright-backend.pid");
const MOCK_PID_FILE = path.resolve(process.cwd(), ".playwright-mock-llm.pid");
const CONFIG_BACKUP_FILE = path.resolve(process.cwd(), ".playwright-config.ini.bak");

export default async function globalTeardown() {
  try {
    if (fs.existsSync(PID_FILE)) {
      const pid = parseInt(fs.readFileSync(PID_FILE, "utf-8").trim(), 10);
      if (Number.isFinite(pid)) {
        try {
          process.kill(pid);
        } catch {
          // ignore
        }
      }
      fs.unlinkSync(PID_FILE);
    }
  } catch {
    // ignore teardown failures
  }

  // Stop mock LLM if started
  try {
    if (fs.existsSync(MOCK_PID_FILE)) {
      const pid = parseInt(fs.readFileSync(MOCK_PID_FILE, "utf-8").trim(), 10);
      if (Number.isFinite(pid)) {
        try {
          process.kill(pid);
        } catch {
          // ignore
        }
      }
      fs.unlinkSync(MOCK_PID_FILE);
    }
  } catch {
    // ignore
  }

  // Restore config.ini if we patched it
  try {
    if (fs.existsSync(CONFIG_BACKUP_FILE)) {
      const repoRoot = path.resolve(process.cwd(), "..");
      const cfgPath = path.join(repoRoot, "config.ini");
      const original = fs.readFileSync(CONFIG_BACKUP_FILE, "utf-8");
      fs.writeFileSync(cfgPath, original, "utf-8");
      fs.unlinkSync(CONFIG_BACKUP_FILE);
    }
  } catch {
    // ignore
  }
}

