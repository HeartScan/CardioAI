import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import { spawn } from "node:child_process";

const PID_FILE = path.resolve(process.cwd(), ".playwright-backend.pid");
const MOCK_PID_FILE = path.resolve(process.cwd(), ".playwright-mock-llm.pid");
const CONFIG_BACKUP_FILE = path.resolve(process.cwd(), ".playwright-config.ini.bak");
const MOCK_PORT = parseInt(process.env.MOCK_LLM_PORT || "18080", 10);

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function waitForHttpOk(url, timeoutMs) {
  const start = Date.now();
  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      await new Promise((resolve, reject) => {
        const req = http.get(url, (res) => {
          res.resume();
          if (res.statusCode && res.statusCode >= 200 && res.statusCode < 500) {
            resolve();
          } else {
            reject(new Error(`status ${res.statusCode}`));
          }
        });
        req.on("error", reject);
        req.setTimeout(2000, () => req.destroy(new Error("timeout")));
      });
      return;
    } catch {
      if (Date.now() - start > timeoutMs) {
        throw new Error(`Backend did not become ready at ${url} within ${timeoutMs}ms`);
      }
      await sleep(250);
    }
  }
}

export default async function globalSetup() {
  // Start backend (uvicorn) from repo root (../)
  const repoRoot = path.resolve(process.cwd(), "..");
  const isWin = process.platform === "win32";
  const pythonLauncher = isWin ? "py" : "python3";

  // By default, run backend against a local mock OpenAI-compatible server
  // to avoid flakiness from external HF endpoint availability.
  const useRealLlm = process.env.E2E_REAL_LLM === "1";

  if (!useRealLlm) {
    // Backup config.ini then replace [HF] BASE_URL to point at the mock server.
    const cfgPath = path.join(repoRoot, "config.ini");
    const cfgOriginal = fs.readFileSync(cfgPath, "utf-8");
    fs.writeFileSync(CONFIG_BACKUP_FILE, cfgOriginal, "utf-8");

    const lines = cfgOriginal.split(/\r?\n/);
    let inHf = false;
    const next = lines.map((line) => {
      const t = line.trim();
      if (/^\[HF\]\s*$/i.test(t)) inHf = true;
      else if (/^\[.+\]\s*$/.test(t)) inHf = false;
      if (inHf && /^BASE_URL\s*=/.test(t)) {
        return `BASE_URL = http://127.0.0.1:${MOCK_PORT}`;
      }
      return line;
    });
    fs.writeFileSync(cfgPath, next.join("\n"), "utf-8");

    // Start mock server as a separate process to keep it alive during tests
    const mock = spawn(process.execPath, ["e2e/mock-openai-server.js"], {
      cwd: process.cwd(),
      stdio: "inherit",
      env: { ...process.env, MOCK_LLM_PORT: String(MOCK_PORT) },
    });
    if (!mock.pid) throw new Error("Failed to start mock LLM server (no pid)");
    fs.writeFileSync(MOCK_PID_FILE, String(mock.pid), "utf-8");
    await waitForHttpOk(`http://127.0.0.1:${MOCK_PORT}/health`, 20_000);
  }

  const args = ["-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8000"];
  const child = spawn(pythonLauncher, args, {
    cwd: repoRoot,
    stdio: "inherit",
    env: { ...process.env },
  });

  if (!child.pid) {
    throw new Error("Failed to start backend (no pid)");
  }

  fs.writeFileSync(PID_FILE, String(child.pid), "utf-8");

  await waitForHttpOk("http://127.0.0.1:8000/docs", 60_000);
}

