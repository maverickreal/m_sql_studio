# Sandbox Worker Rollback Plan

## Migration: Node.js → Bun (oven/bun:1.4)

### Rollback Trigger
If the Bun-based sandbox worker fails in production with:
- Unresolvable Bun-specific bugs (worker crashes, BullMQ incompatibilities)
- Performance regressions vs Node.js baseline
- Native addon compatibility issues (none expected - zero native addons in deps)

### Rollback Procedure
1. **Image rollback** - Revert to previous Node.js-based image:
   ```bash
   docker pull m_sql_studio-sandbox:node-latest  # Previous tagged image
   docker tag m_sql_studio-sandbox:node-latest m_sql_studio-sandbox:latest
   docker compose up -d sandbox-executor
   ```

2. **Dockerfile rollback** - Restore Node.js Dockerfile:
   ```bash
   git checkout HEAD~1 -- m_sql_studio_sandbox/Dockerfile
   # Or manually restore FROM node:20-alpine with npm ci
   ```

3. **Config rollback** - No config changes required (env vars unchanged)

4. **Verification** - Run test suite against rolled-back image:
   ```bash
   docker run --rm m_sql_studio-sandbox:node-latest bun test
   ```

### Rollback Time Estimate
- Image pull + deploy: ~2 minutes
- Full verification: ~5 minutes
- **Total: < 10 minutes**

### Validation Gates (Pre-rollback)
Before rolling back, verify:
- [ ] Worker process stays alive > 30 min
- [ ] BullMQ job processing latency < 500ms p99
- [ ] Zero unhandled rejections in logs
- [ ] Memory stable (no leaks > 100MB/hour)

### Contacts
- Primary: CTO (agy harness)
- On-call: Platform team