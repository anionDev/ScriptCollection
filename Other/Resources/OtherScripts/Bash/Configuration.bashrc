# lsblk
alias bl='sudo lsblk'

# cd ..
alias c='cd ..'

# remove all content in current console-window ('cls'=>'clear screen')
alias cls='printf "\033c"'

# docker list container ('dl'=>'docker list')
alias dl='sudo docker container list --all'

# docker remove container ('dr'=>'docker remove')
alias dr='sudo docker container rm -f'

# docker remove all container ('dra'=>'docker remove all')
alias dra='sudo docker rm -f $(sudo docker ps -aq)'

# grep ('g'=>'grep')
alias g='grep --color=auto'

# list files/directories ('l'=>'list')
alias l='ls -la --color=auto --time-style=long-iso'

# show only lines which are not starting with '#' or ';' ('nel'=>'not encommented lines')
alias nel='grep --color=auto "^[^#;]"'

# cat ('p'=> 'print')
alias p='pygmentize -g -O linenos=1'

# restart
alias restart='sudo reboot -h now && exit'

# sudo ('s'=>'sudo')
alias s='sudo '

# shutdown
alias shutdown='sudo shutdown -h now && exit'
