 #!/bin/bash
 #You need lingua and gettext installed to run this
 
 echo "Updating voteit.debate.pot"
 pot-create -d voteit.debate -o voteit/debate/locale/voteit.debate.pot .
 echo "Merging Swedish localisation"
 msgmerge --update voteit/debate/locale/sv/LC_MESSAGES/voteit.debate.po voteit/debate/locale/voteit.debate.pot
 echo "Updated locale files"
 