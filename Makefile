

bootstrap:
	rm -rf venv
	python3 -m venv venv
	pip3 venv/bin/install -r onyx_proj/config/pip/requirements.txt
