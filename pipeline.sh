#!/bin/bash

git submodule init
git submodule update

# if the submodule folder "liliths-throne-public" exists, discard all the changes to it
if [ -d "liliths-throne-public" ]; then
	git submodule foreach git reset --hard
fi

python ./main.py --no-update-repo