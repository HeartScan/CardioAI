import http from "node:http";

const HOST = "127.0.0.1";
const PORT = parseInt(process.env.MOCK_LLM_PORT || "18080", 10);

function readJson(req) {
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (c) => (data += c));
    req.on("end", () => {
      try {
        resolve(data ? JSON.parse(data) : {});
      } catch (e) {
        reject(e);
      }
    });
    req.on("error", reject);
  });
}

const server = http.createServer(async (req, res) => {
  const url = req.url || "/";
  if (req.method === "GET" && (url === "/health" || url === "/")) {
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ ok: true }));
    return;
  }

  if (req.method === "GET" && url === "/v1/models") {
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ object: "list", data: [{ id: "mock", object: "model" }] }));
    return;
  }

  if (req.method === "POST" && url === "/v1/chat/completions") {
    // Ignore request payload; return a deterministic response.
    await readJson(req).catch(() => ({}));
    const payload = {
      id: "chatcmpl_mock",
      object: "chat.completion",
      created: Math.floor(Date.now() / 1000),
      model: "mock",
      choices: [
        {
          index: 0,
          message: {
            role: "assistant",
            content:
              "I am CardioAI, a virtual cardiologist assistant.\n\n(Mock LLM) Dialog initialized successfully.\n\nThis advice does not replace a doctor's visit.",
          },
          finish_reason: "stop",
        },
      ],
    };
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify(payload));
    return;
  }

  res.writeHead(404, { "content-type": "application/json" });
  res.end(JSON.stringify({ error: "not_found", path: url }));
});

server.listen(PORT, HOST, () => {
  console.log(`[mock-openai-server] listening on http://${HOST}:${PORT}`);
});

