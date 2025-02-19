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
	@make bump_lipid_major
	@make convert_lipid_rst_to_md
	@make docu

minor:
	
	@bumpversion minor --allow-dirty
	@make bump_lipid_minor
	@make convert_lipid_rst_to_md
	@make docu

patch:
	
	@bumpversion patch --allow-dirty
	@make bump_lipid_patch
	@make convert_lipid_rst_to_md
	@make docu

bump_lipid_major:
	
	@bumpversion major --allow-dirty --config-file .bumpversion_lipid.cfg

bump_lipid_minor:
	
	@bumpversion minor --allow-dirty --config-file .bumpversion_lipid.cfg

bump_lipid_patch:
	
	@bumpversion patch --allow-dirty --config-file .bumpversion_lipid.cfg

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
	
docker-push-heal:
	@echo katherineheal257/metams:$(version)
	@docker buildx create --use
	@docker buildx build --platform linux/amd64,linux/arm64 --no-cache -t katherineheal257/metams:$(version) --push .
	@docker buildx imagetools create katherineheal257/metams:$(version) -t katherineheal257/metams:latest
	@docker buildx imagetools inspect katherineheal257/metams:latest

docker-nmdc:
	@echo microbiomedata/metams:$(version)
	@docker buildx create --use
	@docker buildx build --platform linux/amd64,linux/arm64 --no-cache -t microbiomedata/metams:$(version) --push .
	@docker buildx imagetools create microbiomedata/metams:$(version) -t microbiomedata/metams:latest
	@docker buildx imagetools inspect microbiomedata/metams:latest

echo-version:
	@echo $(version)

docker-build:

	docker build -t microbiomedata/metams:latest .

docker-build-local:
	docker build -t local-metams:latest .
	
docker-run:
	@echo $(data_dir)
	@echo $(config_dir)
	@docker run -v $(data_dir):/metams/data -v $(config_dir):/metams/configuration microbiomedata/metams:latest metaMS run-gcms-workflow /metams/configuration/metams.toml

wdl-run-gcms :
	@miniwdl run wdl/metaMS_gcms.wdl -i wdl/metams_input_gcms.json --verbose --no-cache --copy-input-files

wdl-run-gcms-local:
	@make docker-build-local
	@miniwdl run wdl/metaMS_gcms.wdl -i wdl/metams_input_gcms_local_docker.json --verbose --no-cache --copy-input-files

wdl-run-lipid :
	miniwdl run wdl/metaMS_lcmslipidomics.wdl -i wdl/metams_input_lipidomics.json --verbose --no-cache --copy-input-files

convert_lipid_rst_to_md:
    # convert the lipid documentation from rst to md
	pandoc -f rst -t markdown -o docs/lcms_lipidomics/README_LCMS_LIPID.md docs/lcms_lipidomics/index.rst
	# render the lipid documentation into html from the rst file
	pandoc -f rst -t html -o docs/lcms_lipidomics/index.html docs/lcms_lipidomics/index.rst

docu:
	# Generate the documentation, ignoring the nmdc_lipidomics_metadata_generation module
	pdoc --output-dir docs --docformat numpy metaMS !metaMS.nmdc_lipidomics_metadata_generation