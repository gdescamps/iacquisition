rm -rf venv
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install flash-attn==2.3.3 --no-build-isolation
