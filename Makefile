app_name = metabMS
parameters_path = metabms.json

install:
	@ . venv/bin/activate
	@pip3 install --editable .
	
run:
	@ . venv/bin/activate
	@metabMS $(parameters_path)

release:
	@python3 setup.py sdist
	@twine upload dist/*

docker-build:
	docker build -t coremb:local .

# change the path to your path /Users/eber373/Desenvolvimento/metaB
docker-run:
	docker run -v /Users/eber373/Desenvolvimento/metaB/data/:/metaB/data coremb:local run-workflow /metaB/data/metabms.json