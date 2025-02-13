To test

```bash
python3.10 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

to deploy

```bash
./deploy.sh
```

if you need to delete old services, use this:

```bash
gcloud app versions list --project=trio-oref-logs --format="get(version.id)" --filter="traffic_split=0" | xargs gcloud app versions delete --project=trio-oref-logs
```