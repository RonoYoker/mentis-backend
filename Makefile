

bootstrap:
	rm -rf venv
	python3 -m venv venv
	venv/bin/pip3 install -r onyx_proj/config/pip/requirements.txt
