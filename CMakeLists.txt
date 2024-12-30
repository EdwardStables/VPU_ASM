cmake_minimum_required(VERSION 3.13)

add_library(vpu_defs
    ${VPU_DEFS_DIR}/${VPU_DEFS_NAME}.h
    ${VPU_DEFS_DIR}/${VPU_DEFS_NAME}.cpp
)

add_custom_command(
    OUTPUT ${VPU_DEFS_DIR}/${VPU_DEFS_NAME}.h ${VPU_DEFS_DIR}/${VPU_DEFS_NAME}.cpp
    DEPENDS ${VPU_ASM}/instructions.yaml
            ${VPU_ASM}/instructions.py
            ${VPU_ASM}/templates/cpp_def.cpp.j2
            ${VPU_ASM}/templates/cpp_def.h.j2
    COMMAND ${VPU_ASM}/instructions.py ${VPU_ASM}/instructions.yaml --cpp ${VPU_DEFS_DIR}/${VPU_DEFS_NAME} --namespace ${DEFS_NAMESPACE}
)
