version 1.0

workflow gcmsMetabolomics {
    call runMetaMS

    output {
        String out = runMetaMS.out
        File output_file = runMetaMS.output_file
        File output_metafile = runMetaMS.output_metafile
    }
}

task runMetaMS {
    input {
        Array[File] file_paths
        File calibration_reference_path
        File calibration_file_path
        String output_directory
        String output_filename
        String output_type
        File corems_toml_path
        File nmdc_metadata_path
        Int jobs_count
    }

    command {
        metaMS run-gcms-wdl-workflow \
            ${sep=',' file_paths} \
            ${calibration_reference_path} \
            ${calibration_file_path} \
            ${output_directory} \
            ${output_filename} \
            ${output_type} \
            ${corems_toml_path} \
            ${nmdc_metadata_path} \
            --jobs ${jobs_count}
    }

    output {
        String out = read_string(stdout())
        File output_file = "${output_directory}/${output_filename}.${output_type}"
        File output_metafile = "${output_directory}/${output_filename}.json"
    }

    runtime {
        docker: "microbiomedata/metams:2.2.2"
    }
}