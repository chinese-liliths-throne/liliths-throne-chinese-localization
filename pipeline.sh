#!/bin/bash

git submodule init
git submodule update

# if the submodule folder "liliths-throne-public" exists, discard all the changes to it
if [ -d "liliths-throne-public" ]; then
	cd liliths-throne-public
	git reset --hard
	git clean -df
	cd ..
fi

python ./main.py --no-update-repo $*