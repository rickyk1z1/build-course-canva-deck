# build-course-canva-deck

Private Codex Skill for turning course outlines into detailed Canva recording decks using a fixed teaching and visual system.

## Install

```bash
gh auth login
gh auth setup-git

python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo rickyk1z1/build-course-canva-deck \
  --path skills/build-course-canva-deck \
  --method git
```

Restart Codex after installation. Skip `gh auth login` when the device is already authenticated. Final delivery requires a connected Canva account with access to template `DAHM5fsVEB0`.

## Update

Move the existing installed directory to a backup, run the install command again, verify the new version, then remove the backup.
