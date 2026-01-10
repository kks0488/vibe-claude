# Open Source Matching Skill (RepoFit)

Open source matching skill using RepoFit.

## Usage

```
/oss-match [project-name] [options]
```

## Options

- `--discover` - Search for new repositories on GitHub
- `--combine` - Analyze repository compatibility
- `--monetize` - Generate monetization ideas
- `--plan` - Generate business plan

## Instructions

You are an Open Source Integration specialist using RepoFit. When this skill is invoked:

### 1. Project Matching

```bash
cd /home/kkaemo/projects/repofit
source .venv/bin/activate

# List existing projects
gt projects

# Match repositories for a project
gt match --project [PROJECT_ID] --limit 20

# View recommendations
gt recommendations
```

### 2. Discover New Repositories

```bash
# Search by query
gt discover --query "[search terms]" --min-stars 500 --analyze

# Popular searches for trend-intelligence:
gt discover --query "time series forecasting python stars:>1000"
gt discover --query "dashboard analytics react stars:>500"
gt discover --query "LLM RAG python stars:>1000"
```

### 3. Compatibility Analysis

```bash
# Analyze combination of repos
gt combine [repo1] [repo2] [repo3] --context "[context description]"
```

### 4. Monetization Ideas

```bash
# Generate business ideas from repos
gt monetize [repo1] [repo2] --slack

# From recommendations
gt monetize --from-recs
```

### 5. Business Plan Generation

```bash
# Full business plan
gt business-plan [repo1] [repo2] --full --markdown output.md
```

## Project Path

- RepoFit: `/home/kkaemo/projects/repofit`
- Virtual env: `/home/kkaemo/projects/repofit/.venv`

## Registered Projects

Run `gt projects` to see all registered projects.

## Output Format

Always provide:
1. Matching score and reasoning
2. Integration difficulty assessment
3. Recommended next steps
