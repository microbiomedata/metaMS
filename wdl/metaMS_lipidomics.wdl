version 1.0

workflow lcmsLipidomics {
    input {
        # Path to the TOML file containing the configuration for the lipidomics workflow
        File config_file_toml
    }

    call runLipidomicsMetaMS {
        input:
            config_file = config_file_toml
    }
}

task runLipidomicsMetaMS {
    input {
        File config_file
    }

    command {
        #TODO KRH: This will be broken until docker image has been updated to include run-lipidomics-workflow function
        metaMS run-lipidomics-workflow ${config_file}
    }

    output {
        String result = read_string(stdout())
    }

    runtime {
        docker: "microbiomedata/metams:2.2.2"
    }
}