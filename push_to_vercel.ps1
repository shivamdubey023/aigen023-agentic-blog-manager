# Push all .env variables directly to Vercel
Write-Host "Connecting to Vercel and pushing environment variables..." -ForegroundColor Cyan

# Ensure project is linked
npx -y vercel link

# Read .env and push keys
$envFile = ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#")) {
            if ($line -match '^\s*([a-zA-Z0-9_\-\.]+)\s*[:=]\s*"?([^"#]*)"?') {
                $key = $matches[1].Trim().ToUpper()
                $val = $matches[2].Trim()
                
                # Normalize key names
                if ($key -eq "GROQ") { $key = "GROQ_API_KEY" }
                if ($key -eq "GEMINI") { $key = "GEMINI_API_KEY" }
                if ($key -eq "COHERE") { $key = "COHERE_API_KEY" }
                if ($key -eq "CLIENT_ID") { $key = "GOOGLE_CLIENT_ID" }
                if ($key -eq "CLIENT_SECRET") { $key = "GOOGLE_CLIENT_SECRET" }
                if ($key -eq "REDIRECT_URI") { $key = "GOOGLE_OAUTH_REDIRECT_URI" }

                if ($val -and $key -notmatch "^(COOKIE_SECRET|AUTH_URI|TOKEN_URI|SERVER_METADATA_URL|AUTH_PROVIDER_X509_CERT_URL)$") {
                    Write-Host "Setting $key on Vercel (Production & Preview)..." -ForegroundColor Yellow
                    echo $val | npx -y vercel env add $key production --force
                    echo $val | npx -y vercel env add $key preview --force
                }
            }
        }
    }
    Write-Host "All environment variables pushed to Vercel successfully!" -ForegroundColor Green
} else {
    Write-Host ".env file not found." -ForegroundColor Red
}
