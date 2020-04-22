app_name = metaMS
parameters_path = data/MetamsFile.json
# change the path to your data path /Users/eber373/Desenvolvimento/metaB
data_dir = /Users/eber373/Desenvolvimento/metaB/data/
version := $(shell cat .bumpversion.cfg | grep current_version | cut -d= -f2 | tr -d ' ')
stage := $(shell cat .bumpversion.cfg | grep optional_value | cut -d= -f2 | tr -d ' ') 

cpu: 
	pyprof2calltree -k -i $(file)

mem: 

	mprof run --multiprocess $(script)
	mprof plot

major:
	
	@bumpversion major --allow-dirty

minor:
	
	@bumpversion minor --allow-dirty

patch:
	
	@bumpversion patch --allow-dirty

install:
	@source venv/bin/activate
	@pip3 install --editable .
	
run:
	@ . venv/bin/activate
	@metaMS run-gcms-workflow $(parameters_path)

pypi:
	@python3 setup.py sdist
	@twine upload dist/*

docker-push:
	
	@echo corilo/metams:$(version).$(stage)
	@docker build -t corilo/metams:$(version).$(stage) .
	@docker push corilo/metams:$(version).$(stage)
	@docker image tag corilo/metams:$(version).$(stage) corilo/metams:latest
	@docker push corilo/metams:latest

docker-build:

	docker build -t metams:local .

docker-run:

	docker run -v $(data_dir):/metaB/data metams:local run-gcms-workflow /metaB/data/MetamsFile.json