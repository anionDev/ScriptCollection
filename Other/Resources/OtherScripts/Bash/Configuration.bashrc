# list files/directories
alias l='ls -la --color=auto --time-style=long-iso'

# cd ..
alias c='cd ..'

# cat ('p'=> 'print')
alias p='pygmentize -g -O linenos=1'

# show only lines which are not starting with # or ; ('nel'=>'not encommented lines')
alias nel='grep --color=auto "^[^#;]"'

# grep ('g'=>'grep')
alias g='grep --color=auto'

# docker list container ('dl'=>'docker list')
alias dl='sudo docker container list --all'

# docker remove container ('dr'=>'docker remove')
alias dr='sudo docker container rm -f'

# sudo ('s'=>'sudo')
alias s='sudo '

# restart ('restart'=>'reboot')
alias restart='sudo reboot -h now'
