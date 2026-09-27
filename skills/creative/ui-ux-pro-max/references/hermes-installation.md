# Hermes Installation Steps for ui-ux-pro-max Skill

1. Clone the source:
   ```bash
   git clone https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git /tmp/ui-ux-pro-max-skill
   ```

2. (Optional) Build the CLI for external use:
   ```bash
   cd /tmp/ui-ux-pro-max-skill/cli
   npm install
   npx bun build src/index.ts --outdir dist --target node
   ```

3. Copy to Hermes skills directory:
   ```bash
   mkdir -p ~/.hermes/skills/creative/ui-ux-pro-max
   cp -r /tmp/ui-ux-pro-max-skill/* ~/.hermes/skills/creative/ui-ux-pro-max/
   ```

4. Verify:
   ```bash
   hermes skills list | grep ui-ux-pro-max
   skill_view('ui-ux-pro-max')
   ```