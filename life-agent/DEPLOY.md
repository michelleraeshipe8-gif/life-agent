# DEPLOY TO RAILWAY - 5 MINUTE GUIDE

## Step 1: Upload to GitHub
1. Go to: https://github.com/new
2. Repository name: `life-agent`
3. Make it **Private**
4. Click "Create repository"
5. Upload all files from this folder
6. Click "Commit changes"

## Step 2: Deploy to Railway
1. Go to: https://railway.app
2. Click "Login with GitHub"
3. Click "New Project"
4. Click "Deploy from GitHub repo"
5. Select your `life-agent` repository
6. Click "Deploy"

## Step 3: Add Environment Variables

While it's deploying, click "Variables" and add these:

**Variable 1:**
```
Name: TELEGRAM_BOT_TOKEN
Value: [your bot token]
```

**Variable 2:**
```
Name: ANTHROPIC_API_KEY
Value: [your api key]
```

**Variable 3:**
```
Name: DATABASE_URL
Value: postgresql://postgres:password@postgres:5432/lifeagent
```

## Step 4: Add PostgreSQL Database

1. Click "+ New" 
2. Click "Database"
3. Click "PostgreSQL"
4. Click "Add"

Railway will auto-connect it to your app.

## Step 5: Done!

Your agent is now running 24/7 in the cloud.

Check logs by clicking "View Logs" - you should see:
```
[OK] Life Agent is running!
```

## Use Your Agent

Open Telegram and message: @myagentmsbot

Send: `/start`

It will respond!

---

## Troubleshooting

**If deployment fails:**
- Check logs for errors
- Make sure all environment variables are set
- Make sure PostgreSQL is connected

**If bot doesn't respond:**
- Check logs - is it running?
- Is your Telegram token correct?
- Try `/start` command

---

## Environment Variables You Need

Get these before deploying:

1. **TELEGRAM_BOT_TOKEN**
   - Open Telegram
   - Message @BotFather
   - Send `/mybots`
   - Select your bot
   - Click "API Token"

2. **ANTHROPIC_API_KEY**
   - Go to: https://console.anthropic.com/settings/keys
   - Click "Create Key"
   - Copy it

3. **DATABASE_URL**
   - Railway auto-generates this when you add PostgreSQL
   - Just add the database, Railway handles the rest

---

That's it! Your agent runs forever.
