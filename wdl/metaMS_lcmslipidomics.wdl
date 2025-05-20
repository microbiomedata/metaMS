version 1.0

workflow lcmsLipidomics {
    input {
        String? docker_image  # Optional input for Docker image
    }

    call runMetaMSLCMSLipidomics {
        input:
            docker_image = docker_image
    }

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
        File db_location
        File scan_translator_path
        Int cores
        String? docker_image
    }

    command {
        metaMS run-lipidomics-workflow \
            -i ${sep=',' file_paths} \
            -o ${output_directory} \
            -c ${corems_toml_path} \
            -d ${db_location} \
            -s ${scan_translator_path} \
            -j ${cores}
        EXIT_CODE=$?

        # Count subdirectories in output_directory
        num_subdirs=$(find "${output_directory}" -mindepth 1 -maxdepth 1 -type d | wc -l)
        num_inputs=${#file_paths[@]}

        # Check that each subdirectory contains at least one .csv file
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
        docker: "~{if defined(docker_image) then docker_image else 'microbiomedata/metams:3.1.0'}"
    }
}