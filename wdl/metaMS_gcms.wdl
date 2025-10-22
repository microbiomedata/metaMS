version 1.0

workflow gcmsMetabolomics {
    input {
        String? docker_image  # Optional input for Docker image
    }

    call runMetaMSGCMS {
        input:
            docker_image = docker_image
    }

    output {
        String out = runMetaMSGCMS.out
        Array[File] output_files = runMetaMSGCMS.output_files
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
        String? nmdc_metadata_path
        String? metabref_token_path
        Int jobs_count
        String? docker_image
    }

    command {
        metaMS run-gcms-wdl-workflow \
            ${sep=',' file_paths} \
            ${calibration_file_path} \
            ${output_directory} \
            ${output_filename} \
            ${output_type} \
            ${corems_toml_path} \
            ~{if defined(nmdc_metadata_path) then "--nmdc_metadata_path" + nmdc_metadata_path else ""} \
            ~{if defined(metabref_token_path) then "--metabref_token_path " + metabref_token_path else ""} \
            --jobs ${jobs_count}
    }

    output {
        String out = read_string(stdout())
        Array[File] output_files = glob('${output_directory}/*')
    }

    runtime {
        docker: "~{if defined(docker_image) then docker_image else 'microbiomedata/metams:3.3.2'}"
    }
}