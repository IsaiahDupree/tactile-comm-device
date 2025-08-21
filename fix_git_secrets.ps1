# PowerShell script to remove API keys from Git history
# WARNING: This rewrites Git history and requires force push

Write-Host "🔒 Git Secrets Cleanup Script" -ForegroundColor Yellow
Write-Host "This will remove exposed API keys from Git history" -ForegroundColor Red
Write-Host ""

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "❌ Not in a Git repository" -ForegroundColor Red
    exit 1
}

# Show current status
Write-Host "📊 Current repository status:" -ForegroundColor Cyan
git status --short

Write-Host ""
Write-Host "🚨 WARNING: This will rewrite Git history!" -ForegroundColor Red
Write-Host "   - All commit hashes will change" -ForegroundColor Yellow
Write-Host "   - Collaborators will need to re-clone" -ForegroundColor Yellow
Write-Host "   - Force push will be required" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Continue? (type 'yes' to proceed)"
if ($confirm -ne "yes") {
    Write-Host "❌ Aborted" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "🔧 Step 1: Committing current changes..." -ForegroundColor Green
git add .
git commit -m "Remove exposed API keys and add environment variable handling

- Replace hardcoded ElevenLabs API keys with environment variables
- Add .env.example for secure configuration
- Update .gitignore to prevent future key exposure
- Fix security vulnerabilities in README.md, test files, and scripts"

Write-Host ""
Write-Host "🧹 Step 2: Using git-filter-repo to remove secrets..." -ForegroundColor Green

# Create a patterns file for git-filter-repo
@"
# Remove API key patterns
regex:sk_[a-zA-Z0-9]{48}
regex:ELEVENLABS_API_KEY.*=.*sk_[a-zA-Z0-9]{48}
"@ | Out-File -FilePath "api_key_patterns.txt" -Encoding UTF8

# Check if git-filter-repo is available
$filterRepo = Get-Command git-filter-repo -ErrorAction SilentlyContinue
if (-not $filterRepo) {
    Write-Host "⚠️  git-filter-repo not found. Installing..." -ForegroundColor Yellow
    Write-Host "Please install git-filter-repo first:" -ForegroundColor Red
    Write-Host "  pip install git-filter-repo" -ForegroundColor White
    Write-Host "Then run this script again." -ForegroundColor Red
    Remove-Item "api_key_patterns.txt" -ErrorAction SilentlyContinue
    exit 1
}

# Run git-filter-repo to remove the patterns
Write-Host "🔄 Filtering repository history..." -ForegroundColor Yellow
git filter-repo --replace-text api_key_patterns.txt --force

# Clean up
Remove-Item "api_key_patterns.txt" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "✅ Step 3: History cleaned!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Review the changes: git log --oneline" -ForegroundColor White
Write-Host "2. Force push to remote: git push --force-with-lease origin main" -ForegroundColor White
Write-Host "3. Create .env file with your actual API key" -ForegroundColor White
Write-Host "4. Notify collaborators to re-clone the repository" -ForegroundColor White
Write-Host ""
Write-Host "🔐 Security reminders:" -ForegroundColor Yellow
Write-Host "- Never commit API keys again" -ForegroundColor White
Write-Host "- Always use environment variables" -ForegroundColor White
Write-Host "- Consider rotating the exposed API keys" -ForegroundColor White
