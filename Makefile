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
	@make bump_lcmsmetab_major
	@make convert_lipid_rst_to_md
	@make convert_lcmsmetab_rst_to_md
	@make docu

minor:
	
	@bumpversion minor --allow-dirty
	@make bump_lipid_minor
	@make bump_lcmsmetab_minor
	@make convert_lipid_rst_to_md
	@make convert_lcmsmetab_rst_to_md
	@make docu

patch:
	
	@bumpversion patch --allow-dirty
	@make bump_lipid_patch
	@make bump_lcmsmetab_patch
	@make convert_lipid_rst_to_md
	@make convert_lcmsmetab_rst_to_md
	@make docu

bump_lipid_major:
	
	@bumpversion major --allow-dirty --config-file .bumpversion_lipid.cfg

bump_lipid_minor:
	
	@bumpversion minor --allow-dirty --config-file .bumpversion_lipid.cfg

bump_lipid_patch:
	
	@bumpversion patch --allow-dirty --config-file .bumpversion_lipid.cfg

bump_lcmsmetab_major:
	
	@bumpversion major --allow-dirty --config-file .bumpversion_lcmsmetab.cfg

bump_lcmsmetab_minor:
	@bumpversion minor --allow-dirty --config-file .bumpversion_lcmsmetab.cfg

bump_lcmsmetab_patch:
	@bumpversion patch --allow-dirty --config-file .bumpversion_lcmsmetab.cfg

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

get-lipid-test-data:
	@echo "Downloading test data for lipidomics"
	@mkdir -p test_data
	@mkdir -p test_data/test_lipid_data
	@curl --retry 3 --retry-delay 5 --connect-timeout 30 --max-time 300 -L -o test_data/test_lipid_data.zip https://nmdcdemo.emsl.pnnl.gov/lipidomics/test_data/metams_lipid_test_data/test_lipid_data.zip
	@unzip test_data/test_lipid_data.zip -d test_data/test_lipid_data/
	@rm test_data/test_lipid_data.zip
	@echo "Test data downloaded and unzipped"

wdl-run-lipid :
	miniwdl run wdl/metaMS_lcmslipidomics.wdl -i wdl/metams_input_lipidomics.json --verbose --no-cache --copy-input-files

wdl-run-lipid-local:
	@make docker-build-local
	miniwdl run wdl/metaMS_lcmslipidomics.wdl -i wdl/metams_input_lipidomics_local_docker.json --verbose --no-cache --copy-input-files

get-lcms-metab-test-data:
	@echo "Downloading test data for LC-MS metabolomics workflow"
	@mkdir -p test_data
	@curl --retry 3 --retry-delay 5 --connect-timeout 30 --max-time 300 -L -o test_data/test_lcms_metab_data.zip https://nmdcdemo.emsl.pnl.gov/metabolomics/test_data/metams_lcms_metab_test_data/test_lcms_metab_data.zip
	@unzip test_data/test_lcms_metab_data.zip -d test_data/
	@rm test_data/test_lcms_metab_data.zip
	@echo "Test data downloaded and unzipped"

get-test-data: get-lipid-test-data wait-and-get-lcms-metab-test-data

wait-and-get-lcms-metab-test-data:
	@echo "Waiting 10 seconds before downloading LC-MS metabolomics data..."
	@sleep 10
	@$(MAKE) get-lcms-metab-test-data

wdl-run-lcms-metab :
	miniwdl run wdl/metaMS_lcms_metabolomics.wdl -i wdl/metams_input_lcms_metabolomics.json --verbose --no-cache --copy-input-files

wdl-run-lcms-metab-local:
	@make docker-build-local
	miniwdl run wdl/metaMS_lcms_metabolomics.wdl -i wdl/metams_input_lcms_metabolomics_local_docker.json --verbose --no-cache --copy-input-files

convert_lipid_rst_to_md:
    # convert the lipid documentation from rst to md and render it into html
	pandoc -f rst -t markdown -o docs/lcms_lipidomics/README_LCMS_LIPID.md docs/lcms_lipidomics/index.rst
	pandoc -f rst -t html -o docs/lcms_lipidomics/index.html docs/lcms_lipidomics/index.rst

convert_lcmsmetab_rst_to_md:
    # convert the lcms metabolomics documentation from rst to md and render it into html
	pandoc -f rst -t markdown -o docs/lcms_metabolomics/README_LCMS_METABOLOMICS.md docs/lcms_metabolomics/index.rst
	pandoc -f rst -t html -o docs/lcms_metabolomics/index.html docs/lcms_metabolomics/index.rst

docu:
	# Generate the documentation
	pdoc --output-dir docs --docformat numpy metaMS