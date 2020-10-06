workflow gcmsMetabolomics {
    
    Array[File] file_paths
    
    File calibration_file_path

    String output_directory

    String output_filename

    String output_type

    File corems_json_path

    Int jobs_count

    call runMetaMS {
         input: file_paths= file_paths,
                calibration_file_path=calibration_file_path,
                output_directory=output_directory,
                output_filename=output_filename,
                output_type=output_type,
                corems_json_path=corems_json_path,
                jobs_count=jobs_count
    }
}

task runMetaMS {
    
    Array[File] file_paths
    
    File calibration_file_path

    String output_directory

    String output_filename

    String output_type

    File corems_json_path

    Int jobs_count
    
    command {
        
        metaMS run-gcms-wdl-workflow ${sep=',' file_paths} \
                                     ${calibration_file_path} \
                                     ${output_directory} \
                                     ${output_filename} \
                                     ${output_type} \
                                     ${corems_json_path} \
                                     --jobs ${jobs_count} 
    }
    
    output {
        
        String out = read_string(stdout())
        File output_file = "${output_directory}/${output_filename}.${output_type}"
        File output_metafile = "${output_directory}/${output_filename}.json" 
    }

    runtime {
        docker: "microbiomedata/metams:latest"
    
    }

}

