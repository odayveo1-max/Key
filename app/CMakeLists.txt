cmake_minimum_required(VERSION 3.22.1)

project("jawaker_cheto")

# تحويل الكود المصدري إلى مكتبة مشتركة (.so)
add_library(system SHARED src/main/cpp/native-lib.cpp)

# جلب مكتبات النظام الأساسية من Android NDK لمنع الكراش
find_library(log-lib log)
find_library(android-lib android)
find_library(egl-lib EGL)
find_library(gles-lib GLESv2)

# ربط الكود الخاص بك بمكتبات النظام
target_link_libraries(system
        ${log-lib}
        ${android-lib}
        ${egl-lib}
        ${gles-lib}
)
