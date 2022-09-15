app_name = metaMS
parameters_path = data/MetamsFile.json
# change the path to your data path and configuration
data_dir = /Users/eber373/Development/metams/data
config_dir = /Users/eber373/Development/metams/configuration
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
	
	@echo corilo/metams:$(version)
	@docker build --no-cache -t corilo/metams:$(version) .
	@docker push corilo/metams:$(version)
	@docker image tag corilo/metams:$(version) corilo/metams:latest
	@docker push corilo/metams:latest

docker-nmdc:
	
	@echo microbiomedata/metams:$(version)
	@docker build --no-cache -t microbiomedata/metams:$(version) .
	@docker push microbiomedata/metams:$(version)
	@docker image tag microbiomedata/metams:$(version) microbiomedata/metams:latest
	@docker push microbiomedata/metams:latest

docker-build:

	docker build -t microbiomedata/metams:latest .

docker-run:
	@echo $(data_dir)
	@echo $(config_dir)
	@docker run -v $(data_dir):/metams/data -v $(config_dir):/metams/configuration microbiomedata/metams:latest metaMS run-gcms-workflow /metams/configuration/metams.toml

wdl-run :
 	 
	 miniwdl run wdl/metaMS.wdl -i wdl/metams_input.json --verbose --no-cache --copy-input-files


	