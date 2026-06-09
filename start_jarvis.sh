#!/bin/bash
echo "🔄 Güncellemeler kontrol ediliyor..."
git pull

echo "🚀 J.A.R.V.I.S. Web Sunucusu Başlatılıyor..."
uvicorn web.server:app --host 0.0.0.0 --port 10000
