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
        docker: "local-metams:latest"
        #TODO KRH: Change to dockerhub version after we've pushed the updated image
    }
}

