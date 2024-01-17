# list files/directories
alias l='ls -la --color=auto --time-style=long-iso'

# cd ..
alias c='cd ..'

# cat ('cath'=> 'cat with highlighting')
alias cath='pygmentize -g -O linenos=1'

# show only lines which are not starting with # or ; ('nel'=>'not encommented lines')
alias nel='grep "^[^#;]"'

# docker list container ('dl'=>'docker list')
alias dl='sudo docker container list --all'

# docker remove container ('dr'=>'docker remove')
alias dr='sudo docker container rm -f'