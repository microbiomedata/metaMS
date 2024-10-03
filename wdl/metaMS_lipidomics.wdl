version 1.0

workflow lcmsLipidomics {
    call runLipidomicsMetaMS
}

task runLipidomicsMetaMS {
    input {
        File config_file
    }

    command {
        metaMS run-lipidomics-workflow -p ${config_file}
    }

    runtime {
        docker: "microbiomedata/metams:2.2.2"
    }
}