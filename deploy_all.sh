source reset_cuda.sh
git submodule update --init --recursive
dvc pull
source deploy_python.sh

