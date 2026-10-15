"""Vercel ASGI entrypoint: frozen inference, no server-side visitor history."""
from pathlib import Path
import os
from app.research_predictor.api import create_app

ROOT=Path(__file__).resolve().parents[1]
hosts=['localhost','127.0.0.1','testserver']
hosts.extend(value for key in ['VERCEL_URL','VERCEL_PROJECT_PRODUCTION_URL','VERCEL_BRANCH_URL'] if (value:=os.environ.get(key)))
hosts.extend(h.strip() for h in os.environ.get('ONCOPREDICT_ALLOWED_HOSTS','').split(',') if h.strip())
app=create_app(ROOT,public_demo=True,allowed_hosts=hosts)
