app_name = metabMS
parameters_path = data/coremb_params.json
# change the path to your data path /Users/eber373/Desenvolvimento/metaB
data_dir = /Users/eber373/Desenvolvimento/metaB/data/
version := $(shell cat .bumpversion.cfg | grep current_version | cut -d= -f2 | tr -d ' ')
stage := $(shell cat .bumpversion.cfg | grep optional_value | cut -d= -f2 | tr -d ' ') 

install:
	@ . venv/bin/activate
	@pip3 install --editable .
	
run:
	@ . venv/bin/activate
	@metabMS $(parameters_path)

release:
	@python3 setup.py sdist
	@twine upload dist/*

docker-push:
	
	@echo corilo/coremb:$(version).$(stage)
	@docker build -t corilo/coremb:$(version).$(stage) .
	@docker push corilo/coremb:$(version).$(stage)
	@docker image tag corilo/coremb:$(version).$(stage) corilo/coremb:latest
	@docker push corilo/coremb:latest

docker-build:

	docker build -t coremb:local .

docker-run:

	docker run -v $(data_dir):/metaB/data coremb:local run-workflow /metaB/data/metabms.json