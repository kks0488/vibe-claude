---
description: Check for and install vibe-claude updates
---

[UPDATE CHECK]

$ARGUMENTS

## Checking for Updates

I will check for available updates to vibe-claude.

### What This Does

1. **Check Version**: Compare your installed version against the latest release on GitHub
2. **Show Release Notes**: Display what's new in the latest version
3. **Perform Update**: If an update is available and you confirm, download and install it

### Update Methods

**Automatic (Recommended):**
Run the install script to update:
```bash
curl -fsSL https://raw.githubusercontent.com/kks0488/vibe-claude/main/scripts/install.sh | bash
```

**Manual:**
1. Check your current version in `~/.claude/.vibe-version.json`
2. Visit https://github.com/kks0488/vibe-claude/releases
3. Download and run the install script from the latest release

### Version Info Location

Your version information is stored at: `~/.claude/.vibe-version.json`

---

Let me check for updates now. I'll read your version file and compare against the latest GitHub release.
