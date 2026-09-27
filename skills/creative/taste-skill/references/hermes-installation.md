# Hermes Installation Steps for taste-skill

1. Clone the source:
   ```bash
   git clone https://github.com/Leonxlnx/taste-skill.git /tmp/taste-skill
   ```

2. Copy the skill to Hermes skills directory:
   ```bash
   mkdir -p ~/.hermes/skills/creative/taste-skill
   cp -r /tmp/taste-skill/skills/taste-skill/* ~/.hermes/skills/creative/taste-skill/
   ```

3. Verify:
   ```bash
   hermes skills list | grep taste-skill
   skill_view('taste-skill')
   ```

The skill is now ready for use via `skill_view('taste-skill')`.