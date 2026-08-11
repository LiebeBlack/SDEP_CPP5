# 🚀 GitHub Actions Workflows

This directory contains the GitHub Actions workflows for automated CI/CD of the Sistema de Gestión de Personal.

## 📁 Workflow Files

| Workflow | Purpose | Triggers |
|----------|---------|----------|
| [ci.yml](ci.yml) | Continuous Integration - Testing and Quality Checks | Push to main/develop/canary, Pull Requests |
| [build.yml](build.yml) | Build Executables - Windows and Cross-platform | Push, Tags, Manual Dispatch |
| [release.yml](release.yml) | Automated Releases - Semantic Versioning | Push to main, Manual Dispatch |
| [canary-deployment.yml](canary-deployment.yml) | Canary Deployments - Gradual Rollout | Push to canary, Manual Dispatch |
| [notifications.yml](notifications.yml) | Notifications and Monitoring | All workflow events, Schedule |

## 🎯 Quick Start

### 1. Initial Setup

Configure the required secrets and variables in your GitHub repository:

**Required Secrets:**
- `SONAR_TOKEN` - SonarQube authentication token
- `SONAR_HOST_URL` - SonarQube server URL
- `SLACK_WEBHOOK_URL` - Slack incoming webhook (optional)
- `TEAMS_WEBHOOK_URL` - Microsoft Teams webhook (optional)
- `SMTP_SERVER` - SMTP server for email notifications (optional)
- `SMTP_PORT` - SMTP port (default: 587)
- `SMTP_USERNAME` - SMTP authentication username (optional)
- `SMTP_PASSWORD` - SMTP authentication password (optional)
- `SMTP_FROM` - Sender email address (optional)

**Required Variables:**
- `NOTIFICATION_EMAIL` - Default email for notifications (optional)

### 2. Branch Protection

Configure branch protection rules:
- **main**: Require PR reviews, status checks (CI, Build, Quality Gate)
- **develop**: Require PR reviews, status checks (CI)
- **canary**: Require status checks (CI, Canary Pre-checks)

### 3. Environment Setup

Create environments in GitHub repository settings:
- **staging**: For canary deployments
- **production**: For production deployments

## 🔄 Workflow Usage

### Automatic Triggers

Most workflows run automatically based on Git events:

```bash
# Push to main - triggers CI, Build, Release
git push origin main

# Push to develop - triggers CI, Build
git push origin develop

# Push to canary - triggers CI, Build, Canary Deployment
git push origin canary

# Create PR - triggers CI, Notifications
gh pr create --title "New feature" --body "Description"
```

### Manual Triggers

Use GitHub CLI to manually trigger workflows:

```bash
# Trigger build with specific type
gh workflow run build.yml -f build_type=release

# Trigger release with version type
gh workflow run release.yml -f release_type=minor -f pre_release=false

# Trigger canary deployment
gh workflow run canary-deployment.yml -f deployment_percentage=10 -f environment=staging

# Trigger with rollback
gh workflow run canary-deployment.yml -f rollback=true
```

## 📊 Workflow Status

View workflow status and logs:

```bash
# List recent workflow runs
gh run list

# View specific run
gh run view <run-id>

# View logs
gh run view <run-id> --log

# Download artifacts
gh run download <run-id>
```

## 🧪 Testing Locally

Before pushing, test workflows locally:

```bash
# Run tests
pytest tests/ -v

# Run quality checks
black --check src/
isort --check-only src/
flake8 src/
pylint src/

# Build executable
python build.py
```

## 🚨 Troubleshooting

### Workflow Failures

1. Check the specific job that failed
2. Review error logs: `gh run view <run-id> --log`
3. Fix the issue locally
4. Commit and push the fix

### Common Issues

- **CI fails**: Check code quality and test failures
- **Build fails**: Verify dependencies and build script
- **Release fails**: Check git tags and permissions
- **Canary fails**: Verify environment configuration

## 📚 Documentation

For detailed documentation, see:
- [CI_CD_DOCUMENTATION.md](../../CI_CD_DOCUMENTATION.md) - Complete CI/CD documentation
- [README.md](../../README.md) - Project documentation
- [ESTRUCTURA_PROYECTO_COMPLETO.md](../../ESTRUCTURA_PROYECTO_COMPLETO.md) - Project structure

## 🔐 Security Notes

- Never commit secrets to the repository
- Use GitHub Secrets for sensitive data
- Rotate tokens regularly
- Review workflow permissions
- Monitor security reports

## 📞 Support

For issues or questions:
- Create a GitHub Issue
- Contact the DevOps team
- Check workflow logs for errors

---

**Last Updated**: 2026-08-11  
**Workflow Version**: 1.0.0
