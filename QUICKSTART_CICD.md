# ⚡ Quick Start Guide - CI/CD Setup

This guide will help you quickly set up and configure the CI/CD workflows for your repository.

## 🚀 Setup in 5 Minutes

### Step 1: Configure GitHub Secrets (2 minutes)

Go to your repository settings: `Settings > Secrets and variables > Actions`

#### Required Secrets
```yaml
# SonarQube (if using)
SONAR_TOKEN: your_sonarqube_token
SONAR_HOST_URL: https://sonarqube.example.com

# Slack Notifications (optional but recommended)
SLACK_WEBHOOK_URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Email Notifications (optional)
SMTP_SERVER: smtp.gmail.com
SMTP_PORT: 587
SMTP_USERNAME: your_email@gmail.com
SMTP_PASSWORD: your_app_password
SMTP_FROM: noreply@yourdomain.com
```

#### How to get Slack Webhook URL
1. Go to https://api.slack.com/apps
2. Create a new app → "Incoming Webhooks"
3. Activate incoming webhooks
4. Add new webhook to your workspace
5. Copy the webhook URL

### Step 2: Configure Branch Protection (1 minute)

Go to: `Settings > Branches`

#### Main Branch Protection
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- 🔒 Require: `Continuous Integration / Quality Gate`
- 🔒 Require: `Build Executable / Build Windows`

#### Develop Branch Protection
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
- 🔒 Require: `Continuous Integration / Test Suite`

### Step 3: Create Environments (1 minute)

Go to: `Settings > Environments`

#### Create "staging" Environment
- No protection rules needed
- Add deployment branch: `canary`

#### Create "production" Environment
- Required reviewers: Add your team
- Wait timer: 30 minutes (recommended)
- Add deployment branch: `main`

### Step 4: Test Workflows (1 minute)

```bash
# Push a test commit to trigger CI
git commit --allow-empty -m "test: trigger CI workflow"
git push origin main

# Or manually trigger a workflow
gh workflow run ci.yml
```

## 📋 Verification Checklist

After setup, verify:

- [ ] Secrets are configured correctly
- [ ] Branch protection rules are active
- [ ] Environments are created
- [ ] CI workflow runs successfully
- [ ] Build workflow creates executables
- [ ] Notifications are received (if configured)

## 🎯 Common First-Time Issues

### Issue: "Secret not found"
**Solution**: Ensure secrets are configured in repository settings, not organization settings.

### Issue: "Workflow disabled"
**Solution**: Go to Actions tab and enable workflows in repository settings.

### Issue: "Permission denied"
**Solution**: Check that GitHub Actions has write permissions in repository settings.

### Issue: "Branch protection error"
**Solution**: Temporarily disable branch protection, push, then re-enable.

## 🔄 Next Steps

1. **Configure notification channels** for your team
2. **Set up SonarQube** for code quality analysis (optional)
3. **Customize workflow thresholds** in workflow files
4. **Set up scheduled health checks** (already configured)
5. **Configure team-specific rules** in `.github/settings.yml`

## 📚 Detailed Documentation

For comprehensive documentation, see:
- [CI_CD_DOCUMENTATION.md](CI_CD_DOCUMENTATION.md) - Complete CI/CD guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development workflow
- [.github/workflows/README.md](.github/workflows/README.md) - Workflow details

## 🆘 Need Help?

- Check workflow logs: `gh run list` and `gh run view <run-id> --log`
- Review CI/CD documentation
- Create a GitHub Issue
- Contact your DevOps team

---

**Setup Complete! 🎉** Your CI/CD pipeline is now ready to automate your development workflow.
