export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate myenv312

export NEO4J_URI="bolt://44.204.112.211:7687"                                         
export NEO4J_USERNAME="neo4j"                                                     
export NEO4J_PASSWORD="resource-cheeks-eighths"