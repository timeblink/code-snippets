git filter-branch -f --tag-name-filter cat --prune-empty --subdirectory-filter  -- --all

git filter-branch -f --tag-name-filter cat --prune-empty --subdirectory-filter rpm_proc -- --all
git filter-branch -f --tag-name-filter cat --prune-empty --subdirectory-filter adsp_proc -- --all
git filter-branch -f --tag-name-filter cat --prune-empty --subdirectory-filter common -- --all
git filter-branch -f --tag-name-filter cat --prune-empty --subdirectory-filter boot_images -- --all
git filter-branch -f --tag-name-filter cat --prune-empty --subdirectory-filter trustzone_images -- --all
git filter-branch -f --tag-name-filter cat --prune-empty --subdirectory-filter modem_proc -- --all
git filter-branch -f --tag-name-filter cat --prune-empty --subdirectory-filter wcnss_proc -- --all
git filter-branch -f --tag-name-filter cat --prune-empty --subdirectory-filter debug_image -- --all

llvm-rs
git filter-branch -f --tag-name-filter cat --prune-empty --subdirectory-filter LINUX/android/vendor/qcom/proprietary/llvm-rs -- --all

prebuilt_HY11
git filter-branch -f --tag-name-filter cat --prune-empty --subdirectory-filter LINUX/android/vendor/qcom/proprietary/prebuilt_HY11 -- --all

mm-camera
git filter-branch -f --tag-name-filter cat --prune-empty --subdirectory-filter LINUX/android/vendor/qcom/proprietary/mm-camera -- --all

mm-audio
git filter-branch -f --tag-name-filter cat --prune-empty --subdirectory-filter LINUX/android/vendor/qcom/proprietary/mm-audio -- --all


proprietary
git filter-branch -f --tag-name-filter cat --prune-empty --subdirectory-filter LINUX/android/vendor/qcom/proprietary -- --all

git filter-branch -f \
  --tag-name-filter cat --prune-empty --tree-filter \
  'rm -rf llvm-rs ; rm -rf mm-audio ; rm -rf mm-camera ; rm -rf prebuilt_HY11' -- --all
