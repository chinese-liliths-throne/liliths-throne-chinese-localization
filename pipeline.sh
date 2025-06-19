#!/bin/bash

git submodule init

# if the submodule folder "liliths-throne-public" exists, discard all the changes to it
if [ -d "liliths-throne-chinese" ]; then
	cd liliths-throne-chinese
	git reset --hard
	git clean -df
	cd ..
fi

git submodule update --remote
git add -A -- liliths-throne-chinese

python ./main.py --no-update-repo $*