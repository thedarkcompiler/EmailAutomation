# Lock the Files:

```bash
chmod 600 .env
chmod 600 recipients.json
chmod 600 mailer.log
```

# The Project Dir:

```bash
chmod 700 .
```

# To add env Data to Linux environment Variables

```bash
export SMTP_PASSWORD="your_password"
export SMTP_USER="mailer@example.com"
```

Then get with: 

```python
os.getenv("SMTP_PASSWORD")
```

# Make files Read-Only

```bash
chmod 400 recipients.json
```

