# HOW TO UPLOAD TO GITHUB

## Method 1: GitHub Website (Easiest)

1. **Create Repository**
   - Go to: https://github.com/new
   - Name: `life-agent`
   - Privacy: **Private** (important!)
   - Click "Create repository"

2. **Upload Files**
   - Click "uploading an existing file"
   - Drag your entire `life-agent` folder
   - Click "Commit changes"

3. **Done!** 
   - Now follow DEPLOY.md to deploy to Railway

---

## Method 2: Git Command Line

If you have Git installed:

```bash
cd life-agent

git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/life-agent.git
git push -u origin main
```

Replace YOUR_USERNAME with your GitHub username.

---

## Important Files to Include

Make sure these are uploaded:
- [x] All .py files
- [x] Dockerfile
- [x] docker-compose.yml
- [x] requirements.txt
- [x] config/plugins.yaml
- [x] .gitignore
- [x] railway.json
- [x] Procfile

Do NOT upload:
- [ ] .env (has your secrets!)
- [ ] data/ folder
- [ ] logs/ folder
- [ ] __pycache__/

The .gitignore file handles this automatically.

---

## After Upload

1. Your code is on GitHub
2. Follow DEPLOY.md to deploy to Railway
3. Your agent runs 24/7
4. Use it on your phone via Telegram

---

## Need Help?

- GitHub not working? Use Method 1 (website upload)
- Can't find your repo? Check https://github.com/YOUR_USERNAME
- Deployment issues? Check DEPLOY.md
