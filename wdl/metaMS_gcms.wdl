version 1.0

workflow gcmsMetabolomics {
    call runMetaMSGCMS

    output {
        String out = runMetaMSGCMS.out
        File output_file = runMetaMSGCMS.output_file
        File output_metafile = runMetaMSGCMS.output_metafile
    }
}

task runMetaMSGCMS {
    input {
        Array[File] file_paths
        File calibration_file_path
        String output_directory
        String output_filename
        String output_type
        File corems_toml_path
        File nmdc_metadata_path
        File metabref_token_path
        Int jobs_count
    }

    command {
        metaMS run-gcms-wdl-workflow \
            ${sep=',' file_paths} \
            ${calibration_file_path} \
            ${output_directory} \
            ${output_filename} \
            ${output_type} \
            ${corems_toml_path} \
            ${nmdc_metadata_path} \
            ${metabref_token_path} \
            --jobs ${jobs_count}
    }

    output {
        String out = read_string(stdout())
        File output_file = "${output_directory}/${output_filename}.${output_type}"
        File output_metafile = "${output_directory}/${output_filename}.json"
    }

    runtime {
        docker: "local-metams:latest"
        #TODO KRH: Update to pushed version when available
    }
}