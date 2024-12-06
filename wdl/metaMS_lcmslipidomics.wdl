version 1.0

workflow lcmsLipidomics {
    call runMetaMSLCMSLipidomics

    output {
        String out = runMetaMSLCMSLipidomics.out
        Array[File] output_files = runMetaMSLCMSLipidomics.output_files
    }
}

task runMetaMSLCMSLipidomics {
    input {
        Array[File] file_paths
        String output_directory
        File corems_toml_path
        File metabref_token_path
        File scan_translator_path
        Int cores
    }

    command {
        metaMS run-lipidomics-workflow \
            -i ${sep=',' file_paths} \
            -o ${output_directory} \
            -c ${corems_toml_path} \
            -t ${metabref_token_path} \
            -s ${scan_translator_path} \
            -j ${cores}
    }

    output {
        String out = read_string(stdout())
        Array[File] output_files = glob('${output_directory}/*')
    }

    runtime {
        docker: "local-metams:latest"
    }
}