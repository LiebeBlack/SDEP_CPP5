# 🚀 CI/CD Documentation - Sistema de Gestión de Personal

## 📋 Table of Contents

1. [Overview](#overview)
2. [Workflow Architecture](#workflow-architecture)
3. [Workflow Descriptions](#workflow-descriptions)
4. [Setup and Configuration](#setup-and-configuration)
5. [Usage Guidelines](#usage-guidelines)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## 🌟 Overview

Este repositorio cuenta con un sistema completo de CI/CD automatizado implementado mediante GitHub Actions. El sistema está diseñado para proporcionar:

- **Integración Continua (CI)**: Validación automática de código, tests y calidad
- **Entrega Continua (CD)**: Construcción automatizada de ejecutables
- **Lanzamientos Automatizados**: Versionamiento semántico y releases
- **Despliegues Canary**: Lanzamientos graduales y controlados
- **Monitoreo y Notificaciones**: Alertas en tiempo real y seguimiento

### Key Features

- ✅ Multi-version Python testing (3.10, 3.11, 3.12)
- ✅ Code quality checks (Black, isort, Flake8, Pylint, mypy)
- ✅ Security scanning (Bandit, Safety)
- ✅ Automated Windows executable building
- ✅ Semantic versioning with automatic changelog
- ✅ Canary deployments with configurable rollout percentages
- ✅ Multi-channel notifications (Slack, Teams, Email)
- ✅ Health monitoring and weekly reports
- ✅ Cross-platform build support

---

## 🏗️ Workflow Architecture

### Workflow Trigger Map

```
┌─────────────────────────────────────────────────────────────┐
│                    TRIGGER EVENTS                            │
├─────────────────────────────────────────────────────────────┤
│  Push to main/develop/canary  →  CI, Build, Release, Canary │
│  Pull Request                  →  CI, Notifications            │
│  Tag push (v*)                 →  Build, Release              │
│  Manual dispatch              →  All workflows               │
│  Schedule (weekly)            →  Health checks               │
│  Release events                →  Notifications                │
└─────────────────────────────────────────────────────────────┘
```

### Workflow Dependencies

```
                    ┌──────────────────┐
                    │   CI Workflow    │
                    │  (ci.yml)        │
                    └────────┬─────────┘
                             │
                             ├─────────────┐
                             │             │
                    ┌────────▼────────┐  ┌▼──────────────┐
                    │  Build Workflow │  │ Release       │
                    │  (build.yml)    │  │ (release.yml) │
                    └────────┬────────┘  └───────────────┘
                             │
                    ┌────────▼────────┐
                    │ Canary Deploy   │
                    │ (canary-deploy) │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Notifications   │
                    │ (notifications) │
                    └─────────────────┘
```

---

## 📚 Workflow Descriptions

### 1. Continuous Integration (ci.yml)

**Purpose**: Ensure code quality and functionality through automated testing and analysis.

**Triggers**:
- Push to `main`, `develop`, `canary` branches
- Pull requests to `main`, `develop`

**Jobs**:

#### Quality Checks
- **Matrix**: Python 3.10, 3.11, 3.12
- **Black**: Code formatting validation
- **isort**: Import sorting validation
- **Flake8**: Linting with configurable severity
- **Pylint**: Advanced code analysis
- **mypy**: Static type checking
- **Bandit**: Security vulnerability scanning
- **Safety**: Dependency security checking

#### Test Suite
- **Matrix**: Python 3.10, 3.11, 3.12
- **pytest**: Test execution with coverage
- **Coverage reports**: XML, HTML, terminal
- **Codecov integration**: Coverage tracking

#### Integration Tests
- **Depends on**: Test suite
- **Integration testing**: End-to-end scenarios
- **Database testing**: SQLite operations

#### SonarQube Analysis
- **Depends on**: Quality checks, tests
- **Trigger**: Push to main/develop only
- **Features**: Code quality metrics, technical debt analysis

#### Quality Gate
- **Depends on**: All previous jobs
- **Purpose**: Final validation before proceeding
- **Criteria**: All checks must pass

**Artifacts**:
- Security reports (bandit-report.json, safety-report.json)
- Coverage reports (htmlcov/, coverage.xml)
- Test results (.pytest_cache/)

---

### 2. Build Executable (build.yml)

**Purpose**: Automated creation of Windows executables and cross-platform packages.

**Triggers**:
- Push to `main`, `develop`, `canary`
- Tag pushes (`v*`)
- Pull requests
- Manual dispatch

**Jobs**:

#### Build Windows
- **Platform**: Windows latest
- **Python**: 3.11
- **Process**:
  1. Install dependencies
  2. Generate version info (Git commit, branch, build number)
  3. Build with PyInstaller using `build.py`
  4. Verify executable exists
  5. Package as ZIP
  6. Generate build metadata
  7. Upload artifacts
  8. Create GitHub release (for tags)

#### Build Cross-Platform
- **Matrix**: Ubuntu, macOS
- **Python**: 3.11
- **Output**: Platform-specific packages

#### Build Verification
- **Depends on**: Build Windows
- **Process**: Extract and test executable integrity
- **Validation**: SHA256 hash verification

**Artifacts**:
- Windows executable ZIP
- Cross-platform packages
- Build metadata (build-metadata.json)
- Build logs

**Inputs** (Manual dispatch):
- `build_type`: release, debug, canary

---

### 3. Automated Release (release.yml)

**Purpose**: Semantic versioning and automated release creation.

**Triggers**:
- Push to `main`
- Manual dispatch

**Jobs**:

#### Version Analysis
- **Process**:
  1. Analyze commits since last release
  2. Detect version bump type (major/minor/patch)
  3. Determine if release should happen
  4. Calculate new version number
- **Detection Logic**:
  - `BREAKING CHANGE` → major
  - `feat:` prefix → minor
  - `fix:` prefix → patch

#### Update Version
- **Process**:
  1. Update `pyproject.toml` version
  2. Update `README.md` version
  3. Commit changes
  4. Create Git tag

#### Create Release
- **Process**:
  1. Generate changelog from commits
  2. Create GitHub release
  3. Attach build artifacts
  4. Trigger build workflow

#### Create Canary Release
- **Trigger**: Push to `canary` branch
- **Process**:
  1. Generate canary version (base-canary.buildNumber)
  2. Create canary tag
  3. Create pre-release
  4. Trigger canary build

#### Post Release
- **Process**:
  1. Update CHANGELOG.md
  2. Merge release to develop branch
  3. Update documentation

**Inputs** (Manual dispatch):
- `release_type`: major, minor, patch
- `pre_release`: boolean

**Outputs**:
- New version number
- Release type
- Pre-release flag

---

### 4. Canary Deployment (canary-deployment.yml)

**Purpose**: Gradual rollout strategy with monitoring and rollback capabilities.

**Triggers**:
- Push to `canary` branch
- Manual dispatch

**Jobs**:

#### Canary Pre-checks
- **Process**:
  1. Run critical tests
  2. Security scan
  3. Check deployment readiness
  4. Analyze recent workflow failures

#### Build Canary
- **Process**:
  1. Generate canary version
  2. Build executable with canary flag
  3. Package with canary metadata
  4. Create canary release (pre-release)

#### Deploy Canary
- **Environments**: staging, production
- **Process**:
  1. Deploy to staging (default)
  2. Deploy to production with percentage rollout
  3. Generate deployment status

#### Monitor Canary
- **Process**:
  1. Initialize monitoring for 24 hours
  2. Configure monitoring checks:
     - Error rate threshold: 5%
     - Response time threshold: 2000ms
     - User complaints threshold: 10
     - Crash rate threshold: 1%
  3. Create monitoring dashboard
  4. Set up scheduled health checks

#### Rollback Canary
- **Trigger**: Manual rollback input
- **Process**:
  1. Get previous stable version
  2. Perform rollback operations
  3. Notify stakeholders
  4. Document rollback

#### Promote Canary
- **Trigger**: Successful monitoring + manual approval
- **Process**:
  1. Check canary health metrics
  2. Promote to full release
  3. Trigger main release workflow
  4. Update deployment status

#### Canary Summary
- **Process**:
  1. Generate deployment summary
  2. Upload summary artifact
  3. Comment on PR (if applicable)

**Inputs** (Manual dispatch):
- `deployment_percentage`: 5, 10, 25, 50, 100
- `environment`: staging, production
- `rollback`: boolean

**Monitoring Configuration**:
- Duration: 24 hours
- Check interval: 30 minutes
- Automated rollback on critical thresholds

---

### 5. Notifications and Monitoring (notifications.yml)

**Purpose**: Real-time alerts and comprehensive monitoring of all CI/CD activities.

**Triggers**:
- Workflow completions
- Push events
- Pull request events
- Release events
- Issue events
- Schedule (weekly health checks)
- Manual dispatch

**Jobs**:

#### Workflow Status Notifications
- **Process**:
  1. Analyze workflow status (success/failure/cancelled)
  2. Determine severity (critical/warning/info)
  3. Generate notification message
  4. Send to multiple channels
  5. Create GitHub issue for critical failures

**Notification Channels**:
- **Slack**: Rich formatting with action buttons
- **Microsoft Teams**: Adaptive cards with color coding
- **Email**: SMTP-based notifications
- **GitHub Issues**: Automatic issue creation for failures

#### Pull Request Notifications
- **Events**: opened, closed, merged
- **Content**: PR details, author, action taken
- **Channels**: Slack (configurable)

#### Release Notifications
- **Events**: created, published, edited, deleted
- **Content**: Release details, tag, prerelease status
- **Channels**: Slack with download links

#### Health Check
- **Schedule**: Weekly (Mondays 9 AM)
- **Process**:
  1. Run health check tests
  2. Analyze recent workflow failures
  3. Check dependency vulnerabilities
  4. Generate health report
  5. Send notification

**Health Metrics**:
- Workflow failure rate
- Dependency security status
- Vulnerability count
- Recommendations

#### Metrics Collection
- **Purpose**: Collect CI/CD metrics for analysis
- **Data**: Event type, repository, branch, actor, timestamp
- **Retention**: 90 days

#### Security Alerts
- **Process**:
  1. Run Bandit security scan
  2. Run Safety dependency check
  3. Analyze results
  4. Send alerts if issues found
  5. Upload security reports

**Security Thresholds**:
- Critical: >10 issues
- Warning: 1-10 issues
- Secure: 0 issues

---

## ⚙️ Setup and Configuration

### Required Secrets

Configure these secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

#### Authentication Secrets
```yaml
GITHUB_TOKEN: # Automatically provided by GitHub Actions
SONAR_TOKEN: # SonarQube authentication token
SONAR_HOST_URL: # SonarQube server URL
```

#### Notification Secrets
```yaml
SLACK_WEBHOOK_URL: # Slack incoming webhook URL
TEAMS_WEBHOOK_URL: # Microsoft Teams webhook URL
SMTP_SERVER: # SMTP server address
SMTP_PORT: # SMTP port (default: 587)
SMTP_USERNAME: # SMTP authentication username
SMTP_PASSWORD: # SMTP authentication password
SMTP_FROM: # Sender email address
```

### Required Variables

Configure these variables in your GitHub repository settings (`Settings > Secrets and variables > Actions > Variables`):

#### Notification Variables
```yaml
NOTIFICATION_EMAIL: # Default email for notifications
```

### Branch Protection Rules

Configure branch protection in repository settings:

**Main Branch**:
- ✅ Require pull request reviews
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- 🔒 Include CI workflow
- 🔒 Include Build workflow
- 🔒 Include Quality Gate

**Develop Branch**:
- ✅ Require pull request reviews
- ✅ Require status checks to pass
- 🔒 Include CI workflow

**Canary Branch**:
- ✅ Require status checks to pass
- 🔒 Include CI workflow
- 🔒 Include Canary Pre-checks

### Environment Configuration

Create environments in repository settings (`Settings > Environments`):

**Staging Environment**:
- Protection rules: Required reviewers
- Deployment branches: canary

**Production Environment**:
- Protection rules: Required reviewers, wait timer
- Deployment branches: main

---

## 📖 Usage Guidelines

### Development Workflow

#### Feature Development
1. Create feature branch from `develop`
2. Make changes and commit with conventional commits
3. Push and create PR to `develop`
4. CI workflow runs automatically
5. Address any quality issues
6. Merge when approved

#### Release Process
1. Merge PR to `main`
2. Release workflow triggers automatically
3. Version is bumped based on commits
4. GitHub release is created
5. Build workflow creates executables
6. Release is published

#### Canary Deployment
1. Merge feature to `canary` branch
2. Canary workflow triggers automatically
3. Build creates canary release
4. Deploy to staging (default)
5. Monitor for 24 hours
6. Promote to production or rollback

### Manual Workflow Triggers

#### Trigger Build Workflow
```bash
gh workflow run build.yml -f build_type=release
```

#### Trigger Release Workflow
```bash
gh workflow run release.yml -f release_type=minor -f pre_release=false
```

#### Trigger Canary Deployment
```bash
gh workflow run canary-deployment.yml -f deployment_percentage=10 -f environment=staging
```

#### Trigger with Rollback
```bash
gh workflow run canary-deployment.yml -f rollback=true
```

### Conventional Commits

Use conventional commit format for automatic versioning:

```bash
# Major release
git commit -m "feat: breaking change - new user management system"

# Minor release
git commit -m "feat: add PDF export functionality"

# Patch release
git commit -m "fix: resolve database connection timeout"

# Other (no version bump)
git commit -m "docs: update README with new features"
git commit -m "chore: update dependencies"
git commit -m "style: format code with black"
```

### Monitoring and Debugging

#### View Workflow Runs
```bash
gh run list
gh run view <run-id>
```

#### Download Artifacts
```bash
gh run download <run-id>
```

#### View Logs
```bash
gh run view <run-id> --log
```

#### Retry Failed Workflows
```bash
gh run rerun <run-id>
```

---

## 🔧 Troubleshooting

### Common Issues

#### CI Workflow Fails

**Symptoms**: Quality checks or tests fail

**Solutions**:
1. Check the specific job that failed
2. Review the error logs
3. Run locally: `pytest tests/ -v`
4. Fix code formatting: `black src/`
5. Fix imports: `isort src/`
6. Address linting issues

#### Build Workflow Fails

**Symptoms**: PyInstaller build fails

**Solutions**:
1. Check build logs for missing dependencies
2. Verify `build.py` script
3. Ensure all assets are included
4. Check PyInstaller spec file
5. Test locally: `python build.py`

#### Release Workflow Fails

**Symptoms**: Version bump or release creation fails

**Solutions**:
1. Check git tag conflicts
2. Verify conventional commit format
3. Ensure branch protection allows pushes
4. Check GitHub token permissions
5. Manually trigger with specific version type

#### Canary Deployment Fails

**Symptoms**: Canary deployment or monitoring fails

**Solutions**:
1. Check pre-deployment checks
2. Verify environment configuration
3. Review monitoring thresholds
4. Check deployment permissions
5. Manually trigger rollback if needed

#### Notifications Not Working

**Symptoms**: No notifications received

**Solutions**:
1. Verify webhook URLs are correct
2. Check secrets are properly configured
3. Test webhook connectivity
4. Review notification workflow logs
5. Check rate limits

### Debug Mode

Enable debug logging by adding this secret:

```yaml
ACTIONS_STEP_DEBUG: true
ACTIONS_RUNNER_DEBUG: true
```

### Log Collection

Download all logs from a workflow run:

```bash
gh run view <run-id> --log > workflow-logs.txt
```

---

## 🎯 Best Practices

### Development Practices

1. **Commit Often**: Small, frequent commits with clear messages
2. **Use Conventional Commits**: Follow the format for automatic versioning
3. **Test Locally**: Run tests before pushing
4. **Code Review**: Always review PRs before merging
5. **Branch Strategy**: Follow Git Flow or similar

### CI/CD Practices

1. **Monitor Workflows**: Regularly check workflow status
2. **Address Failures Quickly**: Fix CI failures immediately
3. **Use Canary Deployments**: Test releases with canary first
4. **Review Security Reports**: Act on security findings
5. **Keep Dependencies Updated**: Regular dependency updates

### Release Practices

1. **Semantic Versioning**: Follow semantic versioning principles
2. **Changelog Maintenance**: Keep CHANGELOG.md updated
3. **Release Notes**: Include detailed release notes
4. **Testing**: Thoroughly test before releasing
5. **Rollback Plan**: Always have a rollback plan

### Monitoring Practices

1. **Configure Notifications**: Set up all notification channels
2. **Review Health Reports**: Check weekly health reports
3. **Monitor Metrics**: Track CI/CD metrics over time
4. **Security Scanning**: Regular security scans
5. **Performance Monitoring**: Monitor workflow performance

### Security Practices

1. **Secret Management**: Never commit secrets to repository
2. **Dependency Updates**: Keep dependencies updated
3. **Security Scanning**: Regular security scans
4. **Access Control**: Proper branch protection
5. **Audit Logs**: Review workflow audit logs

---

## 📊 Metrics and Reporting

### Key Metrics to Track

- **Workflow Success Rate**: Percentage of successful workflow runs
- **Build Time**: Average time for build workflow
- **Test Coverage**: Code coverage percentage
- **Deployment Frequency**: Number of deployments per week
- **Lead Time**: Time from commit to deployment
- **Failure Rate**: Percentage of failed deployments

### Reporting

Weekly health reports are automatically generated and include:
- Workflow health status
- Dependency security status
- Vulnerability count
- Recommendations

---

## 🔄 Continuous Improvement

### Regular Reviews

- **Monthly**: Review workflow efficiency
- **Quarterly**: Update dependencies and tools
- **Semi-annually**: Review CI/CD strategy
- **Annually**: Major toolchain updates

### Feedback Loop

1. Monitor workflow performance
2. Collect team feedback
3. Identify pain points
4. Implement improvements
5. Measure impact

---

## 📞 Support and Resources

### Documentation
- GitHub Actions Documentation: https://docs.github.com/en/actions
- PyInstaller Documentation: https://pyinstaller.org/
- Conventional Commits: https://www.conventionalcommits.org/

### Internal Resources
- Project README: [README.md](README.md)
- Project Structure: [ESTRUCTURA_PROYECTO_COMPLETO.md](ESTRUCTURA_PROYECTO_COMPLETO.md)

### External Resources
- CI/CD Best Practices: Link to internal wiki
- Team Guidelines: Link to team documentation

---

## 📝 Version History

### v1.0.0 (Current)
- Initial CI/CD implementation
- Complete workflow automation
- Canary deployment support
- Multi-channel notifications
- Security scanning integration

---

**Last Updated**: 2026-08-11  
**Maintained By**: DevOps Team  
**Questions?**: Contact via GitHub Issues or team communication channels
