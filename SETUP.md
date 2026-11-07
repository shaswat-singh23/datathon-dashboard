# Setup

## Tonight (everyone, about 10 minutes)
1. Install git and VS Code. On Windows, work inside WSL2 if you have it.
2. Accept the GitHub invite, then clone:
   ```bash
   git clone <repo-url> && cd datathon
   ```
3. Make sure git knows who you are:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```
4. Skim AGENTS.md (2 minutes). These are the team rules, and AI tools read them.
5. Join the Devpost team, the Discord channel, and the Drive folder.

The stack (languages, packages) gets set up after we pick a challenge. Its commands will be added to this file at kickoff.

## AI tools
- **Claude Code (VS Code):** install the "Claude Code" extension by Anthropic, sign in, open this folder, and trust it. Repo skills: `/triage`, `/kickoff`, `/ship-check`.
- **Cursor, Copilot, Codex:** they read AGENTS.md. Nothing to do.
- **ChatGPT, Gemini, or claude.ai in a browser:** paste AGENTS.md at the start of the chat.

## API keys
- Keys go in `.env` at the repo root, which git ignores. Code reads them from environment variables.
- Never commit a key, paste one into code, or share one in chat. If one leaks, revoke it right away.
- Rate limits are per project, so each person making their own free key means more total capacity than sharing one.

## Git cheat sheet
```bash
git switch -c <name>/<topic>            # start work
git add -A && git commit -m "what"      # save
git pull origin master                    # get teammates' work into your branch
git push -u origin HEAD                 # share; merge to master on GitHub
```
Conflict? Ask the Claude driver. Don't force-push.

<!-- kickoff adds a "Stack setup" section below -->
