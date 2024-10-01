version 1.0

workflow lcmsLipidomics{
    call runLipidomicsMetaMS

}

task runLipidomicsMetaMS{
    input {
        File lipid_workflow_toml_path
    }

    command {
        metaMS run-lipidomics-workflow \
            ${lipid_workflow_toml_path} 
    }

    runtime {
        docker: "microbiomedata/metams:2.2.2"
    }
}