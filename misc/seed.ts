#!/usr/bin/env bun

import fs from "node:fs";
import path from "node:path";

// Explicit .env loader preserving identical fallback behavior
const envPath = path.resolve(__dirname, "../.env");
if (fs.existsSync(envPath)) {
  const envFile = fs.readFileSync(envPath, "utf8");
  envFile.split("\n").forEach((line) => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith("#")) {
      const parts = trimmed.split("=");
      const key = parts[0].trim();
      const value = parts
        .slice(1)
        .join("=")
        .trim()
        .replace(/^['"]|['"]$/g, "");
      if (key && !process.env[key]) {
        process.env[key] = value;
      }
    }
  });
}

const API_GATEWAY_URL: string =
  process.env.API_GATEWAY_URL || "http://127.0.0.1:8000";
const CLIENT_URL: string = process.env.CLIENT_URL || "http://127.0.0.1:3000";
const ADMIN_EMAIL: string =
  process.env.DEFAULT_ADMIN_EMAIL || "admin@m-sql-studio.dev";
const ADMIN_PASSWORD: string =
  process.env.DEFAULT_ADMIN_PASSWORD || "admin123";

interface HealthCheckResponse {
  status?: string;
  checks?: {
    mongodb?: string;
    redis?: string;
    queue?: string;
    sandbox_service?: string;
    sandbox_db?: string;
  };
}

/**
 * Bootstrap guard: wait for API Gateway and MongoDB readiness before proceeding.
 */
const waitForGateway = async (
  url: string,
  retries: number,
  interval: number,
): Promise<boolean> => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url);
      const body = (await response
        .json()
        .catch(() => null)) as HealthCheckResponse | null;
      const mongoOk = body?.checks?.mongodb === "ok";

      // Bootstrap only requires the API and MongoDB; sandbox_db may still be warming up.
      if (response.ok || mongoOk) {
        console.log("API Gateway is up and ready for bootstrap!");
        return true;
      } else {
        console.log(
          `API Gateway returned status ${response.status}\n${url}. Attempt number ${i + 1} of ${retries}.`,
        );
      }
    } catch (err: any) {
      console.log(
        `Error: ${err.message}\nAttempt number ${i + 1} of ${retries}.`,
      );
    }
    await new Promise((resolve) => setTimeout(resolve, interval));
  }

  return false;
};

/**
 * Admin user bootstrap guard: authenticate as default admin.
 * Canonical assignments are managed via problems-sync (m_sql_studio_problems repo).
 */
const bootstrapAdmin = async (): Promise<string | null> => {
  console.log("Authenticating as admin user...");
  const maxRetries = 15;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const signInRes = await fetch(`${API_GATEWAY_URL}/api/auth/sign-in/email`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Origin: CLIENT_URL,
        },
        body: JSON.stringify({ email: ADMIN_EMAIL, password: ADMIN_PASSWORD }),
        redirect: "manual",
      });

      if (signInRes.ok) {
        const sessionCookie = signInRes.headers.get("set-cookie");
        console.log("Admin authentication complete.");
        return sessionCookie;
      }

      if (attempt < maxRetries) {
        console.log(
          `Admin authentication attempt ${attempt}/${maxRetries} (${signInRes.status}). Retrying in 2s...`,
        );
        await new Promise((r) => setTimeout(r, 2000));
      } else {
        const errorText = await signInRes.text();
        console.error(
          `Admin authentication failed! Status ${signInRes.status}: ${errorText}`,
        );
        process.exit(1);
      }
    } catch (err: any) {
      if (attempt < maxRetries) {
        console.log(
          `Admin authentication connection error: ${err.message}. Retrying in 2s...`,
        );
        await new Promise((r) => setTimeout(r, 2000));
      } else {
        console.error("Admin authentication failed due to connection error:", err);
        process.exit(1);
      }
    }
  }
  return null;
};

const main = async (): Promise<void> => {
  console.log("Starting bootstrap guard and admin verification...");
  const isUp = await waitForGateway(`${API_GATEWAY_URL}/health`, 15, 2000);
  if (!isUp) {
    console.error("API Gateway is unreachable or unhealthy; Skipping bootstrap!");
    process.exit(1);
  }

  await bootstrapAdmin();
  console.log(
    "Bootstrap complete. Canonical assignment source is m_sql_studio_problems repo via problems-sync.",
  );
};

main().catch((err) => {
  console.error("Unhandled error in bootstrap seed script!", err);
  process.exit(1);
});
