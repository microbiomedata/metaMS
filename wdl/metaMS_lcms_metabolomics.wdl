version 1.0

workflow lcmsMetabolomics {
    input {
        String? docker_image  # Optional input for Docker image
    }

    call runMetaMSLCMSMetabolomics {
        input:
            docker_image = docker_image
    }

    output {
        String out = runMetaMSLCMSMetabolomics.out
        Array[File] output_files = runMetaMSLCMSMetabolomics.output_files
    }
}

task runMetaMSLCMSMetabolomics {
    input {
        Array[File] file_paths
        String output_directory
        File corems_toml_path
        File msp_file_path
        File scan_translator_path
        Int cores
        String? docker_image
    }

    command {
        metaMS run-lcms-metabolomics-workflow \
            -i ${sep=',' file_paths} \
            -o ${output_directory} \
            -c ${corems_toml_path} \
            -m ${msp_file_path} \
            -s ${scan_translator_path} \
            -j ${cores}
        EXIT_CODE=$?
        num_inputs=$(echo ${sep=' ' file_paths} | wc -w)
        num_subdirs=$(find "${output_directory}" -mindepth 1 -maxdepth 1 -type d | wc -l)
        all_ok=1
        for subdir in "${output_directory}"/*/; do
            if [ -d "$subdir" ]; then
                if ! ls "$subdir"/*.csv 1> /dev/null 2>&1; then
                    all_ok=0
                    break
                fi
            fi
        done

        if [ "$all_ok" -eq 1 ] && [ "$num_subdirs" -eq "$num_inputs" ]; then
            exit 0
        else
            exit $EXIT_CODE
        fi
    }

    output {
        String out = read_string(stdout())
        Array[File] output_files = glob('${output_directory}/*')
    }

    runtime {
        docker: "~{if defined(docker_image) then docker_image else 'microbiomedata/metams:3.2.2'}"
    }
}